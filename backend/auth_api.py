from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import tempfile
import os
import traceback
from typing import Optional

from backend.orchestrator import orchestrate, CANDIDATE_DB
from backend.profile_agent import extract_text
from backend.evaluate_endpoint import router as evaluate_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(evaluate_router)


def _error_payload(code: str, message: str, status: int):
    return JSONResponse(
        status_code=status,
        content={"success": False, "error": {"code": code, "message": message}},
    )


def _recalculate_scores(c: dict) -> dict:
    """
    Recompute skill_score, sas_breakdown (skill_coverage), sas_score,
    and overall_score from the current state of c["skill_results"].
    Called after any skill result is updated.
    """
    skill_results   = c.get("skill_results", [])
    total_skills    = max(len(skill_results), 1)
    profile_score   = c.get("profile_score", 50)
    authenticity    = c.get("authenticity_score", 0.5)
    fraud_risk      = c.get("fraud_confidence", 0.0)

    # Count verified (externally) + passed (via skill test)
    verified_count = sum(
        1 for r in skill_results
        if r.get("score") in ("Verified", ) or
           (r.get("passed") and r.get("score") not in ("Pending", "Error", "Verified"))
    )
    pending_count  = sum(1 for r in skill_results if r.get("score") == "Pending")

    # Skill score
    partial_credit = (verified_count + 0.5 * pending_count) / total_skills
    skill_score    = max(10, round(partial_credit * 100))

    # SAS components
    verified_ratio   = verified_count / total_skills
    auth_pct         = authenticity * 100
    fraud_inv        = 1.0 - fraud_risk

    W_PROFILE, W_EVIDENCE, W_COVERAGE, W_FRAUD_INV = 0.40, 0.30, 0.20, 0.10

    contrib_profile   = profile_score       * W_PROFILE
    contrib_evidence  = auth_pct            * W_EVIDENCE
    contrib_coverage  = verified_ratio * 100 * W_COVERAGE
    contrib_fraud_inv = fraud_inv      * 100 * W_FRAUD_INV

    sas_score = max(20, round(
        contrib_profile + contrib_evidence + contrib_coverage + contrib_fraud_inv
    ))

    bd_profile   = round(contrib_profile)
    bd_evidence  = round(contrib_evidence)
    bd_coverage  = round(contrib_coverage)
    bd_fraud_inv = round(contrib_fraud_inv)
    delta        = sas_score - (bd_profile + bd_evidence + bd_coverage + bd_fraud_inv)
    bd_profile  += delta

    # Overall
    overall_score = max(10, round(
        0.25 * profile_score +
        0.40 * sas_score     +
        0.35 * skill_score
    ))

    fraud_flag = c.get("fraud_flag", False)
    recommendation = (
        "HIRE"   if overall_score >= 70 and not fraud_flag else
        "REVIEW" if overall_score >= 45 else "REJECT"
    )

    c["skill_score"]   = skill_score
    c["sas_score"]     = sas_score
    c["overall_score"] = overall_score
    c["recommendation"]= recommendation
    c["sas_breakdown"] = {
        "profile_completeness": bd_profile,
        "evidence_score":       bd_evidence,
        "skill_coverage":       bd_coverage,
        "fraud_risk_inverse":   bd_fraud_inv,
    }
    return c


# =========================
# ROOT
# =========================

@app.get("/")
def home():
    return {"status": "Backend running", "success": True}


# =========================
# ANALYZE
# =========================

@app.post("/analyze")
async def analyze(
    resume:         UploadFile    = File(...),
    candidate_name: Optional[str] = Form(None),
):
    temp_path = None
    try:
        print("\n========== FILE RECEIVED ==========")
        print("Filename:", resume.filename)
        print("Candidate name override:", candidate_name)

        suffix = os.path.splitext(resume.filename or "")[1].lower()
        if suffix not in (".pdf", ".txt", ".docx"):
            return _error_payload("UNSUPPORTED_FILE_TYPE", "Only PDF, TXT, and DOCX files are supported.", 400)

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await resume.read())
            temp_path = tmp.name

        resume_text = extract_text(temp_path)
        if not (resume_text or "").strip():
            return _error_payload("EMPTY_RESUME", "No text could be extracted from the file.", 400)

        result = orchestrate({
            "resume_text":    resume_text,
            "candidate_name": (candidate_name or "").strip(),
        })

        if not isinstance(result, dict):
            return _error_payload("INVALID_PIPELINE_RESULT", "Orchestrator returned an unexpected result.", 502)

        if result.get("success") is False or (result.get("error") and not result.get("profile")):
            return _error_payload("PIPELINE_ERROR", str(result.get("error", "Unknown error")), 502)

        result["success"] = True
        print("\n========== PIPELINE SUCCESS ==========")
        return result

    except ValueError as e:
        return _error_payload("BAD_FILE", str(e), 400)
    except Exception as e:
        traceback.print_exc()
        return _error_payload("INTERNAL_ERROR", str(e), 500)
    finally:
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except OSError: pass


# =========================
# CANDIDATES — list
# =========================

@app.get("/candidates")
def get_candidates():
    return {"success": True, "count": len(CANDIDATE_DB), "candidates": CANDIDATE_DB}


# =========================
# CANDIDATE — single
# =========================

@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str):
    match = next((c for c in CANDIDATE_DB if c["id"] == candidate_id), None)
    if not match:
        return JSONResponse(status_code=404, content={"success": False, "error": f"Candidate {candidate_id} not found"})
    return {"success": True, "candidate": match}


# =========================
# SKILL RESULT — persist eval outcome + recalculate scores
# Called by frontend after a successful /evaluate response.
# =========================

from pydantic import BaseModel

class SkillResultPayload(BaseModel):
    skill:   str
    verdict: str    # "Pass" | "Partial" | "Fail"
    total:   int    # 0–100


@app.post("/candidates/{candidate_id}/skill-result")
def update_skill_result(candidate_id: str, payload: SkillResultPayload):
    """
    Persist a skill test result into the stored candidate record.

    - Updates the matching skill_results entry: passed, score
    - Moves skill from pending_skills → verified_skills (if Pass/Partial)
    - Recalculates skill_score, sas_score, overall_score, sas_breakdown
    """
    candidate = next((c for c in CANDIDATE_DB if c["id"] == candidate_id), None)
    if not candidate:
        return JSONResponse(status_code=404, content={"success": False, "error": "Candidate not found"})

    skill   = payload.skill
    verdict = payload.verdict
    total   = payload.total
    passed  = verdict in ("Pass", "Partial")

    # 1. Update skill_results entry
    for r in candidate.get("skill_results", []):
        if r["skill"] == skill:
            r["passed"] = passed
            r["score"]  = f"{total}/100"
            r["category"] = "verified" if passed else "failed"
            break

    # 2. Move from pending → verified (or → failed) skill lists
    if passed:
        pending = candidate.get("pending_skills", [])
        if skill in pending:
            pending.remove(skill)
        verified = candidate.get("verified_skills", [])
        if skill not in verified:
            verified.append(skill)
        candidate["pending_skills"]  = pending
        candidate["verified_skills"] = verified
        # Update skills_matched chips
        candidate["skills_matched"] = verified[:5]
    else:
        # Mark as explicitly failed — stays in pending_skills for visibility
        pass

    # 3. Recalculate all derived scores
    _recalculate_scores(candidate)

    print(
        f"SKILL RESULT SAVED: {candidate['name']} / {skill} → {verdict} ({total}/100) | "
        f"new scores: sas={candidate['sas_score']} skill={candidate['skill_score']} overall={candidate['overall_score']}"
    )

    return {
        "success":      True,
        "skill":        skill,
        "verdict":      verdict,
        "sas_score":    candidate["sas_score"],
        "skill_score":  candidate["skill_score"],
        "overall_score":candidate["overall_score"],
        "sas_breakdown":candidate["sas_breakdown"],
    }


# =========================
# START
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_api:app", host="127.0.0.1", port=8000, reload=True)


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount evaluate router — POST /evaluate
app.include_router(evaluate_router)


def _error_payload(code: str, message: str, status: int):
    return JSONResponse(
        status_code=status,
        content={"success": False, "error": {"code": code, "message": message}},
    )


# =========================
# ROOT
# =========================

@app.get("/")
def home():
    return {"status": "Backend running", "success": True}


# =========================
# ANALYZE ENDPOINT
# Accepts:
#   resume        : file (required)
#   candidate_name: form field (optional) — overrides extracted name
# =========================

@app.post("/analyze")
async def analyze(
    resume:         UploadFile      = File(...),
    candidate_name: Optional[str]   = Form(None),
):
    temp_path = None

    try:
        print("\n========== FILE RECEIVED ==========")
        print("Filename:", resume.filename)
        print("Candidate name override:", candidate_name)

        suffix = os.path.splitext(resume.filename or "")[1].lower()

        if suffix not in (".pdf", ".txt", ".docx"):
            return _error_payload(
                "UNSUPPORTED_FILE_TYPE",
                "Only PDF, TXT, and DOCX files are supported.",
                400,
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            contents  = await resume.read()
            temp_file.write(contents)
            temp_path = temp_file.name

        print("TEMP FILE:", temp_path)

        resume_text = extract_text(temp_path)

        print("\n========== EXTRACTED TEXT (preview) ==========")
        print((resume_text or "")[:1000])

        if not (resume_text or "").strip():
            return _error_payload(
                "EMPTY_RESUME",
                "No text could be extracted from the file.",
                400,
            )

        result = orchestrate({
            "resume_text":    resume_text,
            "candidate_name": (candidate_name or "").strip(),
        })

        if not isinstance(result, dict):
            return _error_payload(
                "INVALID_PIPELINE_RESULT",
                "Orchestrator returned an unexpected result.",
                502,
            )

        if result.get("success") is False or (
            result.get("error") and not result.get("profile")
        ):
            return _error_payload(
                "PIPELINE_ERROR",
                str(result.get("error", "Unknown orchestration error")),
                502,
            )

        result["success"] = True
        print("\n========== PIPELINE SUCCESS ==========")
        return result

    except ValueError as e:
        return _error_payload("BAD_FILE", str(e), 400)

    except Exception as e:
        print("\n========== BACKEND ERROR ==========")
        traceback.print_exc()
        return _error_payload("INTERNAL_ERROR", str(e), 500)

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# =========================
# CANDIDATES — list all
# =========================

@app.get("/candidates")
def get_candidates():
    return {
        "success":    True,
        "count":      len(CANDIDATE_DB),
        "candidates": CANDIDATE_DB,
    }


# =========================
# CANDIDATE — single by id
# =========================

@app.get("/candidates/{candidate_id}")
def get_candidate(candidate_id: str):
    match = next((c for c in CANDIDATE_DB if c["id"] == candidate_id), None)
    if not match:
        return JSONResponse(
            status_code=404,
            content={"success": False, "error": f"Candidate {candidate_id} not found"},
        )
    return {"success": True, "candidate": match}


# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("auth_api:app", host="127.0.0.1", port=8000, reload=True)