"""
/evaluate  — Skill Answer Evaluation Endpoint
==============================================
Mount this router in your main FastAPI app:

    from backend.evaluate_endpoint import router as evaluate_router
    app.include_router(evaluate_router)

POST /evaluate
Request body  : EvaluateRequest  (JSON)
Response body : EvaluateResponse (JSON)
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.skill_testing_agent import (
    Task,
    Level,
    calibrate_level,
    evaluate_answer,
)

log = logging.getLogger("SkillTrust.EvaluateEndpoint")

router = APIRouter()


# ---------------------------------------------------------------------------
# Score recalculation helper (mirrors auth_api._recalculate_scores)
# ---------------------------------------------------------------------------

def _recalculate(c: dict) -> None:
    """Mutates c in-place: updates skill_score, sas_score, overall_score, sas_breakdown."""
    skill_results = c.get("skill_results", [])
    total_skills  = max(len(skill_results), 1)
    profile_score = c.get("profile_score", 50)
    authenticity  = c.get("authenticity_score", 0.5)
    fraud_risk    = c.get("fraud_confidence", 0.0)

    verified_count = sum(
        1 for r in skill_results
        if r.get("score") == "Verified" or
           (r.get("passed") and r.get("score") not in ("Pending", "Error", "Verified"))
    )
    pending_count = sum(1 for r in skill_results if r.get("score") == "Pending")

    partial_credit = (verified_count + 0.5 * pending_count) / total_skills
    skill_score    = max(10, round(partial_credit * 100))

    verified_ratio   = verified_count / total_skills
    auth_pct         = authenticity * 100
    fraud_inv        = 1.0 - fraud_risk

    cp = profile_score       * 0.40
    ce = auth_pct            * 0.30
    cc = verified_ratio * 100 * 0.20
    cf = fraud_inv      * 100 * 0.10

    sas_score = max(20, round(cp + ce + cc + cf))
    bd_p = round(cp); bd_e = round(ce); bd_c = round(cc); bd_f = round(cf)
    bd_p += sas_score - (bd_p + bd_e + bd_c + bd_f)  # absorb rounding

    overall_score = max(10, round(0.25 * profile_score + 0.40 * sas_score + 0.35 * skill_score))
    fraud_flag    = c.get("fraud_flag", False)

    c["skill_score"]    = skill_score
    c["sas_score"]      = sas_score
    c["overall_score"]  = overall_score
    c["recommendation"] = "HIRE" if overall_score >= 70 and not fraud_flag else "REVIEW" if overall_score >= 45 else "REJECT"
    c["sas_breakdown"]  = {
        "profile_completeness": bd_p,
        "evidence_score":       bd_e,
        "skill_coverage":       bd_c,
        "fraud_risk_inverse":   bd_f,
    }


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------

class EvaluateRequest(BaseModel):
    skill:            str   = Field(..., description="Original skill label")
    skill_key:        str   = Field("python", description="Normalised agent skill key")
    claimed_level:    str   = Field("intermediate")
    evidence:         float = Field(0.5, ge=0.0, le=1.0)
    task_description: str   = Field(..., description="Question text shown to candidate")
    answer:           str   = Field(..., description="Candidate's answer")
    candidate_id:     str   = Field("", description="Candidate UUID — if provided, result is persisted")


class EvaluateResponse(BaseModel):
    skill:        str
    passed:       bool
    verdict:      str          # "Pass" | "Partial" | "Fail"
    score:        float        # 0.0 – 1.0
    total:        int          # 0 – 100
    correctness:  int
    completeness: int
    code_quality: int
    edge_cases:   int
    strengths:    str
    improvements: str
    error:        str | None = None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(req: EvaluateRequest) -> EvaluateResponse:
    """
    Evaluate a candidate's answer for a given skill task.

    Steps:
    1. Re-calibrate level using evidence score (consistent with question generation).
    2. Reconstruct the Task object from the stored task_description.
    3. Call evaluate_answer() — tries Azure OpenAI, falls back to rule-based.
    4. Return structured verdict + dimensional scores + feedback.
    """
    log.info(
        "Evaluating answer — skill=%s skill_key=%s level=%s evidence=%.2f",
        req.skill, req.skill_key, req.claimed_level, req.evidence,
    )

    try:
        # Recalibrate level exactly as it was during question generation
        calibrated: Level = calibrate_level(req.claimed_level, req.evidence)

        # Reconstruct the Task that was presented to the candidate
        task = Task(
            skill=req.skill_key.lower().strip(),
            level=calibrated,
            description=req.task_description,
            source="reconstructed",
        )

        # Run evaluation (LLM → rule-based fallback)
        result: dict[str, Any] = evaluate_answer(task, req.answer)

        passed  = result.get("verdict", "Fail") in ("Pass", "Partial")
        verdict = result.get("verdict", "Fail")
        total   = result.get("total", 0)

        # ── Auto-persist to CANDIDATE_DB if candidate_id was provided ──
        if req.candidate_id:
            try:
                from backend.orchestrator import CANDIDATE_DB

                candidate = next(
                    (c for c in CANDIDATE_DB if c["id"] == req.candidate_id), None
                )
                if candidate:
                    # Update skill_results entry
                    for r in candidate.get("skill_results", []):
                        if r["skill"] == req.skill:
                            r["passed"]   = passed
                            r["score"]    = f"{total}/100"
                            r["category"] = "verified" if passed else "failed"
                            break

                    # Move skill to verified if passed
                    if passed:
                        pending  = candidate.get("pending_skills", [])
                        verified = candidate.get("verified_skills", [])
                        if req.skill in pending:
                            pending.remove(req.skill)
                        if req.skill not in verified:
                            verified.append(req.skill)
                        candidate["pending_skills"]  = pending
                        candidate["verified_skills"] = verified
                        candidate["skills_matched"]  = verified[:5]

                    # Recalculate scores
                    _recalculate(candidate)
                    log.info(
                        "Persisted result for %s / %s → %s | sas=%s skill=%s overall=%s",
                        candidate.get("name"), req.skill, verdict,
                        candidate["sas_score"], candidate["skill_score"], candidate["overall_score"],
                    )
            except Exception as persist_err:
                log.warning("Could not persist skill result: %s", persist_err)

        return EvaluateResponse(
            skill=req.skill,
            passed=passed,
            verdict=verdict,
            score=result.get("score",          0.0),
            total=total,
            correctness=result.get("correctness",  0),
            completeness=result.get("completeness", 0),
            code_quality=result.get("code_quality", 0),
            edge_cases=result.get("edge_cases",   0),
            strengths=result.get("strengths",    ""),
            improvements=result.get("improvements", ""),
        )

    except Exception as exc:
        log.error("Evaluation endpoint error: %s", exc, exc_info=True)
        return EvaluateResponse(
            skill=req.skill,
            passed=False,
            verdict="Fail",
            score=0.0,
            total=0,
            correctness=0,
            completeness=0,
            code_quality=0,
            edge_cases=0,
            strengths="",
            improvements="",
            error=str(exc),
        )