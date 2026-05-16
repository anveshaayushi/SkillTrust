from fastapi import FastAPI
from pydantic import BaseModel
from utils import (
    similarity,
    cosine_sim,
    complexity_score,
    diversity_score
)

app = FastAPI()


# Request model
class InputData(BaseModel):
    code: str
    readme: str
    skills: list[str]
    profile: dict
    evidence: dict


@app.get("/")
def home():
    return {"message": "SkillTrust API is running"}


@app.post("/authenticity")
def authenticity_agent(data: dict):

    profile = data["profile"]
    evidence = data["evidence"]

    claimed_skills = profile["skills"]

    evidence_skills = evidence["aggregated_skill_scores"]

    fraud_risk = 0

    missing_skills = []

    for skill in claimed_skills:

        if skill not in evidence_skills:
            fraud_risk += 0.2
            missing_skills.append(skill)

    authenticity_score = max(0, 1 - fraud_risk)

    fraud_flag = fraud_risk > 0.3

    # -----------------------------
    # FINAL TRUST LABEL
    # -----------------------------
    if authenticity_score > 0.8:
        trust_level = "High"

    elif authenticity_score > 0.5:
        trust_level = "Medium"

    else:
        trust_level = "Low"

    return {
        "authenticity_score": round(authenticity_score, 2),
        "fraud_flag": fraud_flag,
        "missing_skills": missing_skills,
        "trust_level": trust_level
    }

@app.post("/profile")
def profile_agent(data: dict):

    return {
        "skills": ["React", "FastAPI", "Python"],
        "vague_claims": ["Machine Learning"],
        "confidence": {
            "React": 0.8,
            "FastAPI": 0.7
        }
    }


@app.post("/evidence")
def evidence_agent(data: dict):

    return {
        "projects": [{
            "repo": "owner/repo",
            "skills": {
                "FastAPI": 0.8,
                "React": 0.8
            },
            "project_score": 0.68,
            "repo_quality": "good",
            "evidence_strength": "high",
            "flags": [{
                "skill": "ML",
                "issue": "not found"
            }]
        }],
        "aggregated_skill_scores": {
            "FastAPI": 0.8,
            "React": 0.5
        }
    }