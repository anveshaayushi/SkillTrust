import os
import json

# Optional Gemini (will fail safely)
try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    client = genai.GenerativeModel("gemini-1.5-flash")
except:
    client = None


# ── TASK BANK ─────────────────────────────────────────────

TASK_BANK = {
    "react": {
        "beginner": "Create a React component called `Greeting` that accepts a `name` prop and displays 'Hello, {name}!' in an h1 tag.",
        "intermediate": "Build a form with conditional fields.",
        "advanced": "Create a custom hook for pagination."
    },
    "sql": {
        "beginner": "Write a SQL query to find employees with salary > 50000 ordered by salary descending.",
        "intermediate": "Find the 3rd highest salary.",
        "advanced": "Get top 3 customers per country."
    },
    "python": {
        "beginner": "Write a function to check palindrome.",
        "intermediate": "Write a retry decorator.",
        "advanced": "Implement LRU cache."
    }
}


# ── TASK GENERATION ─────────────────────────────────────

def generate_task(skill, level):
    try:
        if client:
            response = client.generate_content(
                f"Generate one {level} level question for {skill}"
            )
            return response.text.strip()
    except Exception as e:
        print(f"[fallback] Dynamic generation failed ({e}), using task bank.")

    return TASK_BANK.get(skill.lower(), {}).get(level.lower(), "Explain concept.")


# ── EVALUATION (FINAL FIXED VERSION) ─────────────────────

def evaluate_answer(skill, level, task, answer):
    answer_lower = answer.lower()

    # Try API (will fail → fallback)
    try:
        if client:
            response = client.generate_content(f"Evaluate: {answer}")
            raw = response.text.strip()
            return json.loads(raw)
    except Exception as e:
        print(f"  [fallback] Using local evaluation: {e}")

    # ── FALLBACK SCORING ──

    correctness = 0
    completeness = 0
    code_quality = 0
    edge_cases = 0

    # GOOD answer
    if any(keyword in answer_lower for keyword in [
        "function", "return", "usestate", "select", "where", "<h1>", "props"
    ]):
        correctness = 35
        completeness = 25
        code_quality = 20
        edge_cases = 10
        score = 0.8
        verdict = "Pass"
        strengths = "Correct implementation with proper structure"
        improvements = "Could include more edge cases"

    # BAD answer
    elif len(answer.strip()) < 10 or "idk" in answer_lower:
        correctness = 5
        completeness = 5
        code_quality = 5
        edge_cases = 0
        score = 0.1
        verdict = "Fail"
        strengths = "Minimal attempt"
        improvements = "Needs proper logic"

    # MEDIUM answer
    else:
        correctness = 15
        completeness = 10
        code_quality = 10
        edge_cases = 5
        score = 0.4
        verdict = "Partial"
        strengths = "Basic understanding shown"
        improvements = "Needs more complete solution"

    total = correctness + completeness + code_quality + edge_cases

    return {
        "correctness": correctness,
        "completeness": completeness,
        "code_quality": code_quality,
        "edge_cases": edge_cases,
        "total": total,
        "score": float(score),
        "strengths": strengths,
        "improvements": improvements,
        "verdict": verdict
    }


# ── LEVEL CALIBRATION ───────────────────────────────────

def calibrate_level(level, evidence):
    levels = ["beginner", "intermediate", "advanced"]

    level = level.lower()
    if level not in levels:
        level = "intermediate"

    idx = levels.index(level)

    if evidence < 0.3 and idx > 0:
        return levels[idx - 1]
    elif evidence > 0.7 and idx < 2:
        return levels[idx + 1]

    return levels[idx]


# ── RUN TEST ────────────────────────────────────────────

def run_skill_test():
    print("\nChoose mode:")
    print("  1. Test a single skill")
    print("  2. Run demo")
    choice = input("Enter 1 or 2: ")

    if choice == "1":
        skill = input("Skill: ")
        level = input("Level: ")
        evidence = float(input("Evidence score: "))
    else:
        skill = "react"
        level = "beginner"
        evidence = 0.5

    level = calibrate_level(level, evidence)

    print("\nGenerating task...")
    task = generate_task(skill, level)

    print("\nTASK:\n", task)
    print("\nType your answer below.")
    print("(When done, type 'END')")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    answer = "\n".join(lines)

    print("\nEvaluating...")
    result = evaluate_answer(skill, level, task, answer)

    print("\nRESULT:")
    print(result)


# ── MAIN ────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nSKILL TESTING AGENT RUNNING...")
    run_skill_test()