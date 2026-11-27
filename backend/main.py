from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict
from uuid import uuid4

from backend.bloom_and_psi import create_bloom_filter, run_ecdh_psi
from backend.fhe_threshold import evaluate_threshold


app = FastAPI(
    title="Privacy-Preserving Student Skill Matching",
    description="Threshold PSI using Bloom Filter, FHE, and ECDH PSI",
    version="1.0",
)

# For local/demo use
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Temporary in-memory sessions for the demo
sessions: Dict[str, dict] = {}


class MatchRequest(BaseModel):
    student_a_skills: List[str]
    student_b_skills: List[str]
    threshold: int = Field(default=2, ge=1)


class MatchResponse(BaseModel):
    threshold_satisfied: bool
    common_skills: List[str]
    fhe_latency_ms: float


class CreateSessionRequest(BaseModel):
    threshold: int = Field(default=2, ge=1)


class CreateSessionResponse(BaseModel):
    session_id: str
    threshold: int


class SkillsRequest(BaseModel):
    skills: List[str]


class SessionStatusResponse(BaseModel):
    session_id: str
    student_a_submitted: bool
    student_b_submitted: bool
    threshold: int
    status: str


def calculate_match(
    student_a_skills: List[str],
    student_b_skills: List[str],
    threshold: int,
) -> MatchResponse:

    bloom_payload = create_bloom_filter(student_a_skills)

    threshold_result = evaluate_threshold(
        bloom_bits=bloom_payload.bit_array,
        server_skills=student_b_skills,
        threshold=threshold,
    )

    common_skills = run_ecdh_psi(
        skills_a=student_a_skills,
        token_a=str(threshold_result["client_token"]),
        skills_b=student_b_skills,
        token_b=str(threshold_result["server_token"]),
    )

    return MatchResponse(
        threshold_satisfied=threshold_result["threshold_satisfied"],
        common_skills=common_skills,
        fhe_latency_ms=threshold_result["latency_ms"],
    )


@app.get("/")
def root():
    return {
        "message": "Privacy-Preserving Student Skill Matching API is running"
    }


# Existing single-request endpoint
@app.post("/match", response_model=MatchResponse)
async def match_students(request: MatchRequest):
    try:
        return calculate_match(
            request.student_a_skills,
            request.student_b_skills,
            request.threshold,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(error)}",
        )


# Student A creates a matching session
@app.post("/sessions", response_model=CreateSessionResponse)
def create_session(request: CreateSessionRequest):
    session_id = uuid4().hex[:8]

    sessions[session_id] = {
        "student_a_skills": None,
        "student_b_skills": None,
        "threshold": request.threshold,
    }

    return CreateSessionResponse(
        session_id=session_id,
        threshold=request.threshold,
    )


# Student A or B submits skills
@app.post("/sessions/{session_id}/{student}", response_model=SessionStatusResponse)
def submit_skills(
    session_id: str,
    student: str,
    request: SkillsRequest,
):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    if student not in {"student-a", "student-b"}:
        raise HTTPException(
            status_code=400,
            detail="Student must be student-a or student-b",
        )

    if not request.skills:
        raise HTTPException(
            status_code=400,
            detail="Skills list cannot be empty",
        )

    sessions[session_id][f"{student.replace('-', '_')}_skills"] = request.skills

    session = sessions[session_id]
    both_submitted = (
        session["student_a_skills"] is not None
        and session["student_b_skills"] is not None
    )

    return SessionStatusResponse(
        session_id=session_id,
        student_a_submitted=session["student_a_skills"] is not None,
        student_b_submitted=session["student_b_skills"] is not None,
        threshold=session["threshold"],
        status="ready" if both_submitted else "waiting",
    )


# Either student checks the result
@app.get("/sessions/{session_id}/result", response_model=MatchResponse)
async def get_session_result(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = sessions[session_id]

    if (
        session["student_a_skills"] is None
        or session["student_b_skills"] is None
    ):
        raise HTTPException(
            status_code=409,
            detail="Both students must submit their skills first",
        )

    return calculate_match(
        session["student_a_skills"],
        session["student_b_skills"],
        session["threshold"],
    )
