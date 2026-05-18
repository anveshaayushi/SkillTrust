import os
import tempfile

from fastapi import FastAPI, HTTPException, Request, UploadFile

from auth_logic import evaluate as evaluate_authenticity
from evidence_agent import run_evidence_agent
from profile_agent import extract_text, run_profile_agent

app = FastAPI()


async def _resume_text_from_request(request: Request) -> str:
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        data = await request.json()
        text = data.get("resume_text") or data.get("resume")
        if not text:
            raise HTTPException(
                status_code=400,
                detail="resume_text or resume required in JSON body",
            )
        return text

    if "multipart/form-data" in content_type:
        form = await request.form()
        resume: UploadFile = form.get("resume")
        if resume is None:
            raise HTTPException(status_code=400, detail="resume file required")

        suffix = os.path.splitext(resume.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(await resume.read())
            temp_path = temp_file.name

        try:
            return extract_text(temp_path)
        finally:
            os.remove(temp_path)

    raise HTTPException(
        status_code=415,
        detail="Use application/json or multipart/form-data",
    )


@app.get("/")
def home():
    return {"message": "SkillTrust API is running"}


@app.post("/profile")
async def profile_agent_endpoint(request: Request):
    resume_text = await _resume_text_from_request(request)
    result = run_profile_agent(resume_text)
    return result.model_dump()


@app.post("/evidence")
async def evidence_agent_endpoint(request: Request):
    resume_text = await _resume_text_from_request(request)
    return run_evidence_agent(resume_text)


@app.post("/authenticity")
def authenticity_agent(data: dict):
    profile = data["profile"]
    evidence = data["evidence"]

    claimed_skills = profile["skills"]
    evidence_skills = evidence.get("aggregated_skill_scores", {})

    fraud_risk = 0
    missing_skills = []

    for skill in claimed_skills:
        if skill not in evidence_skills:
            fraud_risk += 0.2
            missing_skills.append(skill)

    authenticity_score = max(0, 1 - fraud_risk)
    fraud_flag = fraud_risk > 0.3

    if authenticity_score > 0.8:
        trust_level = "High"
    elif authenticity_score > 0.5:
        trust_level = "Medium"
    else:
        trust_level = "Low"

    code = data.get("code", "")
    if isinstance(code, list):
        code = code[0] if code else ""

    if evidence_skills:
        evidence_score = sum(evidence_skills.values()) / len(evidence_skills)
    else:
        evidence_score = 0.7

    logic = evaluate_authenticity({
        "code": code or " ",
        "evidence_score": evidence_score,
        "skill_test_score": 0.7,
    })

    return {
        "authenticity_score": round(authenticity_score, 2),
        "fraud_flag": fraud_flag,
        "missing_skills": missing_skills,
        "trust_level": trust_level,
        "trust_score": logic["trust_score"],
        "risk_level": logic["risk_level"],
        "semantic_similarity": logic.get("semantic_similarity"),
        "flags": [],
        "recommendation": logic.get("reason", "Needs further review"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
