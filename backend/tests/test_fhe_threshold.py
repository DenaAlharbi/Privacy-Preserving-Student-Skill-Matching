"""
backend/tests/test_fhe_threshold.py

End-to-end tests connecting:

Member 1:
    Bloom Filter
    ECDH PSI

Member 2:
    FHE threshold logic
"""

from backend.bloom_and_psi import (
    create_bloom_filter,
    run_ecdh_psi,
)

from backend.fhe_threshold import (
    evaluate_threshold,
)


def test_threshold_passed():

    # Student A private skills
    student_a_skills = [
        "Python",
        "AI",
        "Cybersecurity",
        "Embedded Systems",
    ]

    # Student B private skills
    student_b_skills = [
        "Python",
        "AI",
        "Web",
        "Databases",
    ]

    # fixed threshold used by the FHE circuit
    threshold = 2

    # Member 1 creates Student A's Bloom Filter
    bloom_payload = create_bloom_filter(
        student_a_skills
    )

    # Member 2 performs the FHE threshold check
    result = evaluate_threshold(
        bloom_bits=bloom_payload.bit_array,
        server_skills=student_b_skills,
        threshold=threshold,
    )

    # Python and AI are common
    # therefore 2 matches >= threshold 2
    assert result["threshold_satisfied"] is True

    # If threshold passed
    # client token K' must equal server token K
    assert (
        result["client_token"]
        == result["server_token"]
    )

    # Member 1 now performs ECDH PSI
    common_skills = run_ecdh_psi(
        student_a_skills,
        str(result["client_token"]),
        student_b_skills,
        str(result["server_token"]),
    )

    # PSI should reveal the two common skills
    assert common_skills == [
        "python",
        "ai",
    ]


def test_threshold_failed():

    # Only Python is common
    student_a_skills = [
        "Python",
        "Cybersecurity",
        "Embedded Systems",
    ]

    student_b_skills = [
        "Python",
        "Web",
        "Databases",
    ]

    threshold = 2

    bloom_payload = create_bloom_filter(
        student_a_skills
    )

    result = evaluate_threshold(
        bloom_bits=bloom_payload.bit_array,
        server_skills=student_b_skills,
        threshold=threshold,
    )

    # Only 1 match
    # therefore threshold 2 should fail
    assert result["threshold_satisfied"] is False

    # Client receives a different random token K'
    assert (
        result["client_token"]
        != result["server_token"]
    )

    common_skills = run_ecdh_psi(
        student_a_skills,
        str(result["client_token"]),
        student_b_skills,
        str(result["server_token"]),
    )

    # Different tokens prevent the PSI intersection
    # from being revealed
    assert common_skills == []