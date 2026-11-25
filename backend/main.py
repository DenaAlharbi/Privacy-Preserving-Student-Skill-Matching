from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from backend.bloom_and_psi import (
    create_bloom_filter,
    run_ecdh_psi,
)

from backend.fhe_threshold import evaluate_threshold


app = FastAPI(
    title="Privacy-Preserving Student Skill Matching",
    description="Threshold PSI using Bloom Filter, FHE, and ECDH PSI",
    version="1.0",
)


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class MatchRequest(BaseModel):
    student_a_skills: List[str]
    student_b_skills: List[str]
    threshold: int = 2


# ---------------------------------------------------------
# Response model
# ---------------------------------------------------------

class MatchResponse(BaseModel):
    threshold_satisfied: bool
    common_skills: List[str]
    fhe_latency_ms: float


# ---------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Privacy-Preserving Student Skill Matching API is running"
    }


# ---------------------------------------------------------
# Main matching endpoint
# ---------------------------------------------------------

@app.post("/match", response_model=MatchResponse)
def match_students(request: MatchRequest):

    try:

        # -------------------------------------------------
        # Step 1
        # Student A skills -> Bloom Filter
        # -------------------------------------------------

        bloom_payload = create_bloom_filter(
            request.student_a_skills
        )


        # -------------------------------------------------
        # Step 2
        # FHE threshold check
        #
        # This returns:
        # server_token = K
        # client_token = K if threshold passes
        #                K' if threshold fails
        # -------------------------------------------------

        threshold_result = evaluate_threshold(
            bloom_bits=bloom_payload.bit_array,
            server_skills=request.student_b_skills,
            threshold=request.threshold,
        )


        # -------------------------------------------------
        # Step 3
        # Run ECDH PSI using the tokens produced
        # by the FHE threshold stage
        # -------------------------------------------------

        common_skills = run_ecdh_psi(
            skills_a=request.student_a_skills,
            token_a=str(
                threshold_result["client_token"]
            ),
            skills_b=request.student_b_skills,
            token_b=str(
                threshold_result["server_token"]
            ),
        )


        # -------------------------------------------------
        # Step 4
        # Return only the final application result
        # -------------------------------------------------

        return MatchResponse(
            threshold_satisfied=
                threshold_result["threshold_satisfied"],

            common_skills=common_skills,

            fhe_latency_ms=
                threshold_result["latency_ms"],
        )


    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(error)}",
        )