from utils import similarity, cosine_sim, authenticity_score, fraud_check


def evaluate(data):
    # Mock template (later replace with real dataset)
    template_code = "def add(a,b): return a+b"

    # Calculate similarities
    sim1 = similarity(data["code"], template_code)
    sim2 = cosine_sim(data["code"], template_code)

    # Average similarity
    sim_score = (sim1 + sim2) / 2

    # Dummy complexity score (you can improve later)
    complexity_score = 0.7

    # Final score
    score = authenticity_score(sim_score, complexity_score)

    # Fraud flag
    fraud = fraud_check(score, sim_score)

    # Reason (important for demo)
    if sim_score > 0.9:
        reason = "Code is highly similar to known template"
    elif score < 0.3 and sim_score < 0.9:
        reason = "Low originality detected"
    else:
        reason = "Work appears original"

    return {
       "authenticity_score": float(round(score, 2)),
        "fraud_flag": fraud,
        "reason": reason
    }


# TEST RUN
if __name__ == "__main__":
    data = {
        "code": "def add(a,b): return a+b",
        "readme": "Simple addition function",
        "skills": ["python"]
    }

    result = evaluate(data)
    print(result)