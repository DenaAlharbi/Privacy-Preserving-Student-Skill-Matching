"""
backend/bloom_and_psi.py

Member 1's Cryptographic Module for Privacy-Preserving Student Skill Matching:
1. Bloom Filter Encoding (Section III-B of Hu et al., IEEE TIFS 2024):
   Converts a student's plaintext skill list into a fixed-size binary bit array
   using deterministic, seeded MD5 hash functions.
2. Bloom Filter Index Computation (Algorithm 5, Line 3):
   Computes the exact bit positions for a single skill so the server's TFHE
   ePSI-CA circuit knows which encrypted bits to homomorphically sum.
3. ECDH-Based Standard PSI (Figure 1 & Section VI-A):
   Appends the secret threshold tokens (K' for Client, K for Server) to each skill
   and executes a two-party Elliptic Curve Diffie-Hellman (SECP256R1) PSI protocol.
   Skills are revealed if and only if K' == K (i.e., the FHE threshold was met).
"""

import hashlib
from typing import List
from bitarray import bitarray
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

# Support both package imports (from backend.interfaces) and direct script runs
try:
    from backend.interfaces import BloomFilterPayload
except ImportError:
    from interfaces import BloomFilterPayload

# Fixed deterministic seeds matching Section III-B ("pre-generate |Hash| random numbers
# and use them to seed a single instance of the MD5 hash algorithm")
DEFAULT_HASH_SEEDS = [
    104729, 224737, 350377, 479909, 611953,
    746773, 882377, 1020379, 1159523, 1299709,
    1441049, 1583539, 1726943, 1871237, 2016151,
    2161829, 2308163, 2455129, 2602609, 2750659,
]

# SECP256R1 curve order (n) for scalar modular arithmetic
SECP256R1_ORDER = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551


def _normalize_skill(skill: str) -> str:
    """Standardizes skill strings so 'Python' and ' python ' hash identically."""
    return skill.strip().lower()


def get_skill_indices(skill: str, size: int = 128, num_hashes: int = 5) -> List[int]:
    """
    Computes the `num_hashes` Bloom filter bit positions for a single skill.
    Used both when building Student A's Bloom filter and by Student B (Server)
    inside ePSI-CA (Algorithm 5, Line 3) to look up encrypted bit positions.
    """
    if num_hashes > len(DEFAULT_HASH_SEEDS):
        raise ValueError(f"num_hashes cannot exceed {len(DEFAULT_HASH_SEEDS)}")

    normalized = _normalize_skill(skill)
    indices: List[int] = []

    for i in range(num_hashes):
        seed = DEFAULT_HASH_SEEDS[i]
        digest = hashlib.md5(f"{seed}:{normalized}".encode("utf-8")).hexdigest()
        bit_pos = int(digest, 16) % size
        indices.append(bit_pos)

    return indices


def create_bloom_filter(
    skills: List[str], size: int = 128, num_hashes: int = 5
) -> BloomFilterPayload:
    """
    Encodes Student A's (Client's) skill list into a Bloom Filter bit array.
    Returns a BloomFilterPayload containing the raw 0/1 list ready for TFHE encryption.
    """
    bf = bitarray(size)
    bf.setall(0)

    for skill in skills:
        if not skill or not skill.strip():
            continue
        for idx in get_skill_indices(skill, size=size, num_hashes=num_hashes):
            bf[idx] = 1

    return BloomFilterPayload(
        bit_array=bf.tolist(),
        num_hashes=num_hashes,
        size=size,
    )


def _hash_item_to_curve_point(tagged_item: str) -> ec.EllipticCurvePublicKey:
    """
    Deterministically maps a token-tagged string ('skill||token') onto a valid
    point on the SECP256R1 elliptic curve by hashing to a non-zero scalar h
    and computing H = h * G.
    """
    digest = hashlib.sha256(tagged_item.encode("utf-8")).digest()
    scalar_h = (int.from_bytes(digest, "big") % (SECP256R1_ORDER - 1)) + 1
    priv_key = ec.derive_private_key(scalar_h, ec.SECP256R1())
    return priv_key.public_key()


def _blind_point(
    point_pub_key: ec.EllipticCurvePublicKey, secret_scalar: int
) -> bytes:
    """
    Multiplies an elliptic curve point P by a party's secret scalar k (computing k * P)
    using ECDH scalar multiplication, returning compressed point bytes.
    Because (a * (b * P)) == (b * (a * P)), double-blinded points match iff P_A == P_B.
    """
    blinding_key = ec.derive_private_key(secret_scalar, ec.SECP256R1())
    shared_x = blinding_key.exchange(ec.ECDH(), point_pub_key)
    return shared_x


def _double_blind_point(
    tagged_item: str, scalar_first: int, scalar_second: int
) -> bytes:
    """
    Computes (scalar_first * scalar_second) * H(tagged_item) on SECP256R1.
    Simulates Party 1 blinding H(x) with `a`, sending to Party 2, and Party 2
    blinding with `b` (computing (a * b) mod n * G * h).
    """
    digest = hashlib.sha256(tagged_item.encode("utf-8")).digest()
    scalar_h = (int.from_bytes(digest, "big") % (SECP256R1_ORDER - 1)) + 1

    # Combine scalars mod curve order: (h * a * b) mod n
    combined_scalar = (scalar_h * scalar_first * scalar_second) % SECP256R1_ORDER
    if combined_scalar == 0:
        combined_scalar = 1

    point_key = ec.derive_private_key(combined_scalar, ec.SECP256R1())
    return point_key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.CompressedPoint,
    )


def run_ecdh_psi(
    skills_a: List[str],
    token_a: str,
    skills_b: List[str],
    token_b: str,
) -> List[str]:
    """
    Executes Step 6 of Algorithm 6: ECDH-Based Standard PSI on token-tagged sets.
    - Student A tags each skill as 'skill||token_a' and blinds with secret scalar `a`.
    - Student B tags each skill as 'skill||token_b' and blinds with secret scalar `b`.
    - Both exchange blinded elements and apply their own scalar to get doubly-blinded points.
    - Returns the list of overlapping normalized skills if token_a == token_b;
      otherwise returns [] with overwhelming probability.
    """
    # Generate fresh cryptographically secure random scalars `a` and `b` for this session
    secret_a = ec.generate_private_key(ec.SECP256R1()).private_numbers().private_value
    secret_b = ec.generate_private_key(ec.SECP256R1()).private_numbers().private_value

    # Step 1: Student A prepares tagged items, blinds with `a`, then receives B's `b`-blinding -> (ab)*H(c_i || K')
    client_doubly_blinded = {}
    for raw_skill in skills_a:
        norm_skill = _normalize_skill(raw_skill)
        if not norm_skill:
            continue
        tagged_a = f"{norm_skill}||{token_a}"
        blinded_ab = _double_blind_point(tagged_a, secret_a, secret_b)
        client_doubly_blinded[blinded_ab] = norm_skill

    # Step 2: Student B prepares tagged items, blinds with `b`, then receives A's `a`-blinding -> (ba)*H(s_j || K)
    server_doubly_blinded_set = set()
    for raw_skill in skills_b:
        norm_skill = _normalize_skill(raw_skill)
        if not norm_skill:
            continue
        tagged_b = f"{norm_skill}||{token_b}"
        blinded_ba = _double_blind_point(tagged_b, secret_b, secret_a)
        server_doubly_blinded_set.add(blinded_ba)

    # Step 3: Intersect the doubly-blinded curve points
    matched_skills: List[str] = []
    for blinded_point, original_skill in client_doubly_blinded.items():
        if blinded_point in server_doubly_blinded_set:
            if original_skill not in matched_skills:
                matched_skills.append(original_skill)

    return matched_skills