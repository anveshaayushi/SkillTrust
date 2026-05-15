"""
api.py
======
FastAPI wrapper around the Skill Testing Agent.
Person 1 (orchestrator) calls this via HTTP.
You run this independently — zero dependency on other people's code.

Usage:
    python api.py
    → Server starts at http://localhost:8001

Endpoints:
    POST /test-skill          Test a single skill
    POST /test-skills-batch   Test multiple skills
    GET  /generate-task       Just generate a task (no evaluation)
    GET  /health              Health check
"""

import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn

from skill_testing_agent import (
    generate_task,
    evaluate_answer,
    calibrate_level,
    TASK_BANK
)

app = FastAPI(
    title="SkillTrust — Skill Testing Agent",
    description="Person 4's agent: generates tasks, evaluates answers, returns scores.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REQUEST / RESPONSE MODELS ────────────────────────────────────────────────

class SkillTestRequest(BaseModel):
    skill: str = Field(..., example="React")
    claimed_level: str = Field(..., example="intermediate")
    evidence_score: float = Field(0.5, ge=0.0, le=1.0, example=0.7)
    candidate_answer: str = Field(..., example="function MyComponent() { return <div>Hello</div> }")

class BatchTestRequest(BaseModel):
    tests: List[SkillTestRequest]

class TaskGenerateRequest(BaseModel):
    skill: str
    claimed_level: str
    evidence_score: float = 0.5


# ── ENDPOINTS ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "agent": "skill_testing_agent", "version": "1.0.0"}


@app.post("/generate-task")
def generate_task_endpoint(req: TaskGenerateRequest):
    """
    Step 1 of the flow: just generate a task.
    Call this first, show the task to candidate, then call /test-skill with their answer.
    """
    level = calibrate_level(req.claimed_level, req.evidence_score)
    task = generate_task(req.skill, level)
    return {
        "skill": req.skill,
        "claimed_level": req.claimed_level,
        "level_tested": level,
        "task": task
    }


@app.post("/test-skill")
def test_single_skill(req: SkillTestRequest):
    """
    Full pipeline: calibrate → evaluate answer → return score.
    Call this after the candidate has answered the task.
    """
    if not req.candidate_answer.strip():
        raise HTTPException(status_code=400, detail="candidate_answer cannot be empty")

    level = calibrate_level(req.claimed_level, req.evidence_score)
    task = generate_task(req.skill, level)
    evaluation = evaluate_answer(req.skill, level, task, req.candidate_answer)

    return {
        "skill": req.skill,
        "claimed_level": req.claimed_level,
        "level_tested": level,
        "evidence_score_used": req.evidence_score,
        "task": task,
        "score": evaluation.get("score", 0.0),
        "total_points": evaluation.get("total", 0),
        "breakdown": {
            "correctness": evaluation.get("correctness", 0),
            "completeness": evaluation.get("completeness", 0),
            "code_quality": evaluation.get("code_quality", 0),
            "edge_cases": evaluation.get("edge_cases", 0),
        },
        "strengths": evaluation.get("strengths", ""),
        "improvements": evaluation.get("improvements", ""),
        "verdict": evaluation.get("verdict", "Fail")
    }


@app.post("/test-skills-batch")
def test_multiple_skills(req: BatchTestRequest):
    """
    Run tests for multiple skills at once.
    This is what the orchestrator calls after profile + evidence agents finish.
    """
    results = {}
    for item in req.tests:
        level = calibrate_level(item.claimed_level, item.evidence_score)
        task = generate_task(item.skill, level)
        evaluation = evaluate_answer(item.skill, level, task, item.candidate_answer)
        results[item.skill] = {
            "skill": item.skill,
            "level_tested": level,
            "score": evaluation.get("score", 0.0),
            "total_points": evaluation.get("total", 0),
            "verdict": evaluation.get("verdict", "Fail"),
            "strengths": evaluation.get("strengths", ""),
            "improvements": evaluation.get("improvements", ""),
        }

    overall = sum(r["score"] for r in results.values()) / len(results) if results else 0.0

    return {
        "skill_scores": results,
        "overall_test_score": round(overall, 3)
    }


if __name__ == "__main__":
    print("\n Starting Skill Testing Agent API on http://localhost:8001")
    print(" Docs available at http://localhost:8001/docs\n")
    uvicorn.run(app, host="0.0.0.0", port=8001)
