"""
backend/fhe_threshold.py

Member 2's FHE Threshold Module

This module implements the threshold part of the privacy-preserving student skill matching system

1. Receive Student A's Bloom Filter
2. Receive Student B's skills
3. Compute Student B's Bloom Filter indices using the SAME hash function used by Member 1
4. Encrypt Student A's Bloom Filter using Concrete FHE
5. Homomorphically test Student B's skills against the encrypted Bloom Filter
6. Homomorphically count how many skills matched
7. Check whether:

       intersection_count >= threshold

8. If the threshold is satisfied:
       return the correct server token K

   Otherwise:
       return a random token K'

The important point is that the server evaluates thethreshold condition without decrypting Student A's Bloom Filter
"""

import secrets
import time
from typing import Dict, List

import numpy as np

# Concrete is the FHE library used for our PoC
from concrete import fhe


# Import Dina's Bloom Filter functions
#
#  using :
# create_bloom_filter()
#     only in testing / integration

# get_skill_indices()
#     to calculate exactly the same Bloom Filter positions
#     that Dina's module uses
try:
    from backend.bloom_and_psi import get_skill_indices
except ImportError:
    from bloom_and_psi import get_skill_indices


# ---------------------------------------------------------
# Shared Bloom Filter parameters
# ---------------------------------------------------------
# IMPORTANT:
# These MUST match Dina's defaults:
# size = 128
# num_hashes = 5

BLOOM_SIZE = 128
NUM_HASHES = 5

# ---------------------------------------------------------
# PoC limit
# ---------------------------------------------------------
# Concrete circuits use fixed input shapes
# For our demo we allow Student B to provide at most 10 skills
# This can be increased later, but increasing it also increases the FHE computation cost

MAX_SERVER_SKILLS = 10


# ---------------------------------------------------------
# Token parameters
# ---------------------------------------------------------

# The paper uses a secret token K
# For our PoC we use a 16-bit random integer
# Student B/server keeps K

# The FHE circuit produces:
# K       if threshold is satisfied

# or

# random K'   if threshold is not satisfied

TOKEN_BITS = 16
MAX_TOKEN = (2 ** TOKEN_BITS) - 1


# =========================================================
# 1. BUILD SERVER MEMBERSHIP MASKS
# =========================================================

def build_membership_masks(
    server_skills: List[str],
) -> np.ndarray:
    """
    Convert Student B's skills into Bloom Filter masks

    Dina's function:

        get_skill_indices(skill)

    gives us the five Bloom Filter positions associated with one skill

    Example:

        Python -> [4, 17, 31, 72, 100]

    We represent this as a row of 128 values where only  those five positions contain 1

    Example conceptually:

        [0, 0, 0, 0, 1, 0, ..., 1, ..., 1, ...]

    The result is a matrix:

        MAX_SERVER_SKILLS x BLOOM_SIZE

    Example:

        Python       -> row 0
        AI           -> row 1
        Web          -> row 2
        Databases    -> row 3

    Remaining rows are zero padding.
    """

    if len(server_skills) > MAX_SERVER_SKILLS:
        raise ValueError(
            f"Student B can provide at most "
            f"{MAX_SERVER_SKILLS} skills."
        )

    # Start with all zeros
    masks = np.zeros(
        (MAX_SERVER_SKILLS, BLOOM_SIZE),
        dtype=np.int64,
    )

    # Process each Student B skill
    for skill_number, skill in enumerate(server_skills):

        # Ignore empty strings
        if not skill or not skill.strip():
            continue

        # Use Dina's exact hashing logic
        indices = get_skill_indices(
            skill,
            size=BLOOM_SIZE,
            num_hashes=NUM_HASHES,
        )

        # Set the corresponding Bloom Filter positions to 1
        for index in indices:
            masks[skill_number, index] = 1

    return masks


# =========================================================
# 2. THE FHE FUNCTION
# =========================================================
#
# This is the function Concrete will compile into an FHE circuit

# encrypted_bloom:
#     Student A's Bloom Filter

# membership_masks:
#     Student B's Bloom Filter lookup masks

# threshold:
#     Required number of common skills

# token_k:
#     Correct server secret token

# random_token:
#     Incorrect/random token used when threshold fails


def fhe_threshold_function(
    encrypted_bloom,
    membership_masks,
    threshold,
    token_k,
    random_token,
):
    """
    Homomorphically determine whether enough skills match

    Everything involving Student A's Bloom Filter remains encrypted during evaluation
    """

    # -----------------------------------------------------
    # Membership test
    # -----------------------------------------------------
    
    # encrypted_bloom shape:
    #     (128,)
    
    # membership_masks shape:
    #     (10, 128)
    
    # Multiplication keeps only Bloom Filter positions corresponding to each Student B skill

    selected_bits = membership_masks * encrypted_bloom

    # Sum each row
    
    # A real skill uses NUM_HASHES = 5 positions
    
    # If all five corresponding encrypted Bloom Filter
    # bits are 1:
    #     selected_sum = 5
    
    # otherwise:
    #     selected_sum < 5

    selected_sums = np.sum(
        selected_bits,
        axis=1,
    )

    # -----------------------------------------------------
    # Determine which skills matched
    # -----------------------------------------------------
    
    # Each row becomes:
    
    # 1 -> Bloom Filter membership test succeeded
    # 0 -> membership test failed
    
    # This comparison is evaluated homomorphically

    matches = selected_sums == NUM_HASHES

    # -----------------------------------------------------
    # Count matching skills
    # -----------------------------------------------------

    match_count = np.sum(matches)

    # -----------------------------------------------------
    # Threshold test
    # -----------------------------------------------------
    #
    # Example:

    # match_count = 2
    # threshold   = 2

    # threshold_passed = 1

    threshold_passed = match_count >= threshold

    # -----------------------------------------------------
    # SecretTokenGen-style result
    # -----------------------------------------------------
    # If threshold_passed = 1:
    #     selected_token = token_k

    # If threshold_passed = 0:
    #     selected_token = random_token

    # We write it arithmetically because normal Python branching on encrypted data is not what we want

    selected_token = (threshold_passed * token_k + (1 - threshold_passed) * random_token)

    return selected_token


# =========================================================
# 3. CREATE THE CONCRETE COMPILER
# =========================================================
# Only Student A's Bloom Filter needs to be encrypted for this PoC

# Student B is the server/evaluator, so its masks,threshold and server-generated tokens are clear inputs from the evaluator's side

compiler = fhe.Compiler(
    fhe_threshold_function,
    {
        "encrypted_bloom": "encrypted",
        "membership_masks": "clear",
        "threshold": "clear",
        "token_k": "clear",
        "random_token": "clear",
    },
)


# =========================================================
# 4. CREATE COMPILATION EXAMPLES
# =========================================================
# Concrete needs representative inputs to determine integer ranges and build the FHE circuit
# These are NOT real student data

def create_inputset():
    """
    Build representative dummy inputs for Concrete

    Concrete examines these values when compiling the FHE circuit
    """

    inputset = []

    # Add several examples with different values.
    for example_number in range(20):

        # Random dummy Bloom Filter
        bloom = np.random.randint(
            0,
            2,
            size=BLOOM_SIZE,
            dtype=np.int64,
        )

        # Dummy Student B masks.]
        masks = np.zeros(
            (MAX_SERVER_SKILLS, BLOOM_SIZE),
            dtype=np.int64,
        )

        # Give every dummy skill NUM_HASHES positions
        for skill_number in range(MAX_SERVER_SKILLS):

            indices = np.random.choice(
                BLOOM_SIZE,
                NUM_HASHES,
                replace=False,
            )

            masks[
                skill_number,
                indices
            ] = 1

        # Vary threshold between examples
        threshold = (
            example_number % MAX_SERVER_SKILLS
        ) + 1

        # Include values covering the token range
        
        # This helps Concrete understand the maximum integer size required by the circuit

        if example_number == 0:
            token_k = 1
            random_token = 2

        elif example_number == 1:
            token_k = MAX_TOKEN
            random_token = MAX_TOKEN - 1

        else:
            token_k = secrets.randbelow(
                MAX_TOKEN - 1
            ) + 1

            random_token = secrets.randbelow(
                MAX_TOKEN - 1
            ) + 1

        inputset.append(
            (
                bloom,
                masks,
                threshold,
                token_k,
                random_token,
            )
        )

    return inputset


# =========================================================
# 5. CIRCUIT CACHE
# =========================================================
# Compiling an FHE circuit is expensive
# We therefore compile once and reuse the same circuit

_threshold_circuit = None


def get_threshold_circuit():
    """
    Compile the FHE circuit the first time it is needed

    Later calls reuse the already compiled circuit
    """

    global _threshold_circuit

    if _threshold_circuit is None:

        print(
            "[FHE] compiling threshold circuit..."
        )

        inputset = create_inputset()

        _threshold_circuit = compiler.compile(
            inputset
        )

        print(
            "[FHE] generating cryptographic keys..."
        )

        _threshold_circuit.keygen()

        print(
            "[FHE] circuit ready."
        )

    return _threshold_circuit


# =========================================================
# 6. TOKEN GENERATION
# =========================================================

def generate_tokens():
    """
    Generate:

        K  = correct server token

        K' = random incorrect token

    We make sure K != K'
    """

    token_k = (
        secrets.randbelow(MAX_TOKEN - 1) + 1
    )

    random_token = (
        secrets.randbelow(MAX_TOKEN - 1) + 1
    )

    while random_token == token_k:
        random_token = (
            secrets.randbelow(MAX_TOKEN - 1) + 1
        )

    return token_k, random_token


# =========================================================
# 7. MAIN FUNCTION USED BY THE REST OF THE PROJECT
# =========================================================

def evaluate_threshold(
    bloom_bits: List[int],
    server_skills: List[str],
    threshold: int,
) -> Dict:
    """
    Main public function for Member 2's module

    INPUT
    -----

    bloom_bits:
        Student A's Bloom Filter from Dina's
        create_bloom_filter() function

    server_skills:
        Student B's skill list

    threshold:
        Minimum number of matching skills required

    OUTPUT
    ------

    Dictionary containing:

        server_token
            K held by Student B/server

        client_token
            K if threshold passed,
            otherwise random K'

        threshold_satisfied
            True if K == K'

        latency_ms
            FHE execution time

    Example:

        result = evaluate_threshold(
            bloom_bits,
            ["Python", "AI", "Web"],
            threshold=2
        )
    """

    # -----------------------------------------------------
    # Validate Bloom Filter
    # -----------------------------------------------------

    if len(bloom_bits) != BLOOM_SIZE:
        raise ValueError(
            f"Bloom Filter must contain "
            f"{BLOOM_SIZE} bits."
        )

    # Make sure all Bloom Filter values are 0 or 1
    if any(bit not in (0, 1) for bit in bloom_bits):
        raise ValueError(
            "Bloom Filter may contain only 0 and 1."
        )

    # -----------------------------------------------------
    # Clean Student B skills
    # -----------------------------------------------------

    cleaned_server_skills = [
        skill
        for skill in server_skills
        if skill and skill.strip()
    ]

    if not cleaned_server_skills:
        raise ValueError(
            "Student B must provide at least one skill."
        )

    if (
        len(cleaned_server_skills)
        > MAX_SERVER_SKILLS
    ):
        raise ValueError(
            f"Student B can provide at most "
            f"{MAX_SERVER_SKILLS} skills."
        )

    # -----------------------------------------------------
    # Validate threshold
    # -----------------------------------------------------

    if threshold < 1:
        raise ValueError(
            "Threshold must be at least 1."
        )

    if threshold > len(cleaned_server_skills):
        raise ValueError(
            "Threshold cannot be larger than "
            "Student B's number of skills."
        )

    # -----------------------------------------------------
    # Convert Bloom Filter into NumPy
    # -----------------------------------------------------

    bloom_array = np.array(
        bloom_bits,
        dtype=np.int64,
    )

    # -----------------------------------------------------
    # Create Student B membership masks
    # -----------------------------------------------------
    # using Dina's get_skill_indices() function here,
    # ensuring both modules use exactly the same hashes

    membership_masks = build_membership_masks(
        cleaned_server_skills
    )

    # -----------------------------------------------------
    # Generate K and random K'
    # -----------------------------------------------------

    server_token_k, random_token = (
        generate_tokens()
    )

    # -----------------------------------------------------
    # Get compiled FHE circuit
    # -----------------------------------------------------

    circuit = get_threshold_circuit()

    # -----------------------------------------------------
    # Start performance timer
    # -----------------------------------------------------

    start_time = time.perf_counter()

    # -----------------------------------------------------
    # Encrypt inputs
    # -----------------------------------------------------
    #
    # Concrete looks at the Compiler definition and knows:
    #
    # encrypted_bloom -> encrypted
    #
    # everything else -> clear

    encrypted_arguments = circuit.encrypt(
        bloom_array,
        membership_masks,
        threshold,
        server_token_k,
        random_token,
    )

    # -----------------------------------------------------
    # Perform FHE evaluation
    # -----------------------------------------------------
    #
    # The evaluator performs the computation without
    # decrypting Student A's Bloom Filter.

    encrypted_result = circuit.run(
        encrypted_arguments
    )

    # -----------------------------------------------------
    # Client decrypts the resulting token
    # -----------------------------------------------------

    client_token = circuit.decrypt(
        encrypted_result
    )

    # -----------------------------------------------------
    # Stop timer
    # -----------------------------------------------------

    end_time = time.perf_counter()

    latency_ms = (
        end_time - start_time
    ) * 1000.0

    # Concrete may return a NumPy integer.
    client_token = int(client_token)

    # -----------------------------------------------------
    # Result
    # -----------------------------------------------------
    #
    # This equality is NOT how we perform the threshold
    # calculation.
    #
    # The threshold calculation already happened inside
    # FHE.
    #
    # We compare the tokens here only so the application
    # can report whether the threshold was satisfied.

    threshold_satisfied = (
        client_token == server_token_k
    )

    return {
        "server_token": server_token_k,
        "client_token": client_token,
        "threshold_satisfied":
            threshold_satisfied,
        "latency_ms": latency_ms,
    }