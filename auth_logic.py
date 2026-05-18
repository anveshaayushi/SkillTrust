from utils import (
    similarity,
    cosine_sim,
    authenticity_score,
    fraud_check
)

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


# Load semantic model once
model = SentenceTransformer('all-MiniLM-L6-v2')


def semantic_similarity(text1, text2):

    emb1 = model.encode(text1)
    emb2 = model.encode(text2)

    score = cosine_similarity(
        [emb1],
        [emb2]
    )[0][0]

    return float(score)


def evaluate(data):

    # Temporary reference template
    template_code = "def add(a,b): return a+b"

    candidate_code = data.get("code", "")

    # Traditional similarities
    sim1 = similarity(candidate_code, template_code)
    sim2 = cosine_sim(candidate_code, template_code)

    # NEW semantic similarity
    semantic_score = semantic_similarity(
        candidate_code,
        template_code
    )

    # Combined similarity score
    sim_score = (
        0.2 * sim1 +
        0.2 * sim2 +
        0.6 * semantic_score
    )

    # Temporary mock values
    complexity_score = 0.7
    evidence_score = data.get("evidence_score", 0.7)
    skill_test_score = data.get("skill_test_score", 0.7)

    # Final authenticity score
    score = authenticity_score(
        sim_score,
        complexity_score
    )

    # Final trust score
    trust_score = (
        0.4 * evidence_score +
        0.3 * (1 - sim_score) +
        0.3 * skill_test_score
    )

    # Fraud detection
    fraud = fraud_check(score, sim_score)

    # Risk levels
    if trust_score > 0.8:
        risk_level = "LOW"

    elif trust_score > 0.5:
        risk_level = "MEDIUM"

    else:
        risk_level = "HIGH"

    # Reasons
    if semantic_score > 0.9:
        reason = "Code is semantically very similar to known template"

    elif score < 0.3:
        reason = "Low originality detected"

    else:
        reason = "Work appears original"

    return {
        "authenticity_score": float(round(score, 2)),
        "semantic_similarity": float(round(semantic_score, 2)),
        "trust_score": float(round(trust_score, 2)),
        "risk_level": risk_level,
        "fraud_flag": fraud,
        "reason": reason
    }


# TEST RUN
if __name__ == "__main__":

    data = {
        "code": "def add(a,b): return a+b",
        "readme": "Simple addition function",
        "skills": ["python"],
        "evidence_score": 0.8,
        "skill_test_score": 0.75
    }

    result = evaluate(data)

    print(result)