"""
backend/tests/test_psi.py

Unit tests for Member 1's Bloom Filter and ECDH Standard PSI module.
Verifies:
1. Bloom filter deterministic indexing and normalization.
2. ECDH-PSI reveals exact overlapping skills when threshold tokens match (K' == K).
3. ECDH-PSI reveals an empty set ([]) when threshold tokens differ (K' != K),
   protecting student privacy when the threshold is not met.
"""

from backend.bloom_and_psi import (
    create_bloom_filter,
    get_skill_indices,
    run_ecdh_psi,
)


def test_bloom_filter_encoding_and_normalization():
    skills = ["Python", "AI", "Cybersecurity"]
    payload = create_bloom_filter(skills, size=128, num_hashes=5)

    assert payload.size == 128
    assert payload.num_hashes == 5
    assert len(payload.bit_array) == 128

    # Verify that checking indices for "  python " hits all 1s in Student A's filter
    python_indices = get_skill_indices("  python ", size=128, num_hashes=5)
    assert all(payload.bit_array[idx] == 1 for idx in python_indices)


def test_ecdh_psi_matching_tokens():
    """Test 1: When FHE threshold is met (token_a == token_b), reveal only common skills."""
    student_a_skills = ["Python", "AI", "Embedded Systems", "Figma"]
    student_b_skills = ["python", "Rust", "ai", "Databases"]
    shared_token = "session_secret_token_K_98234"

    intersection = run_ecdh_psi(
        skills_a=student_a_skills,
        token_a=shared_token,
        skills_b=student_b_skills,
        token_b=shared_token,
    )

    assert intersection == ["python", "ai"]


def test_ecdh_psi_mismatched_tokens():
    """Test 2: When FHE threshold fails (token_a != token_b), reveal nothing ([])."""
    student_a_skills = ["Python", "AI", "Cybersecurity"]
    student_b_skills = ["Python", "AI", "Cloud"]

    token_client_k_prime = "random_garbage_token_11111"
    token_server_k = "real_secret_token_99999"

    intersection = run_ecdh_psi(
        skills_a=student_a_skills,
        token_a=token_client_k_prime,
        skills_b=student_b_skills,
        token_b=token_server_k,
    )

    assert intersection == []