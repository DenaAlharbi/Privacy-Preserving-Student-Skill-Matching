"""
backend/test_fhe_threshold.py

Simple end-to-end test connecting:

Member 1:
    Bloom Filter
    ECDH PSI

Member 2:
    FHE threshold logic
"""

try:
    from backend.bloom_and_psi import (
        create_bloom_filter,
        run_ecdh_psi,
    )

    from backend.fhe_threshold import (
        evaluate_threshold,
    )

except ImportError:
    from bloom_and_psi import (
        create_bloom_filter,
        run_ecdh_psi,
    )

    from fhe_threshold import (
        evaluate_threshold,
    )


# ---------------------------------------------------------
# Example private student data
# ---------------------------------------------------------

student_a_skills = [
    "Python",
    "AI",
    "Cybersecurity",
    "Embedded Systems",
]

student_b_skills = [
    "Python",
    "AI",
    "Web",
    "Databases",
]


# ---------------------------------------------------------
# Threshold
# ---------------------------------------------------------

threshold = 2


# ---------------------------------------------------------
# Member 1:
# create Student A's Bloom Filter
# ---------------------------------------------------------

bloom_payload = create_bloom_filter(
    student_a_skills
)

print()
print("Student A Bloom Filter created")
print(
    "Bloom size:",
    bloom_payload.size
)
print(
    "Number of hashes:",
    bloom_payload.num_hashes
)


# ---------------------------------------------------------
# Member 2:
# FHE threshold evaluation
# ---------------------------------------------------------

result = evaluate_threshold(
    bloom_bits=bloom_payload.bit_array,
    server_skills=student_b_skills,
    threshold=threshold,
)


print()
print("----- FHE THRESHOLD RESULT -----")

print(
    "Threshold satisfied:",
    result["threshold_satisfied"]
)

print(
    "Server token K:",
    result["server_token"]
)

print(
    "Client token:",
    result["client_token"]
)

print(
    "FHE latency:",
    round(result["latency_ms"], 2),
    "ms",
)


# ---------------------------------------------------------
# Member 1:
# ECDH PSI using the tokens produced by Member 2
# ---------------------------------------------------------

common_skills = run_ecdh_psi(
    student_a_skills,
    str(result["client_token"]),
    student_b_skills,
    str(result["server_token"]),
)


print()
print("----- PSI RESULT -----")

print(
    "Common skills:",
    common_skills
)


# ---------------------------------------------------------
# Expected result
# ---------------------------------------------------------
#
# Student A:
#
# Python
# AI
# Cybersecurity
# Embedded
#
# Student B:
#
# Python
# AI
# Web
# Databases
#
# There are two common skills:
#
# Python
# AI
#
# threshold = 2
#
# therefore:
#
# K' == K
#
# and ECDH PSI should reveal:
#
# ['python', 'ai']