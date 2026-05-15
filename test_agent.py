"""
test_agent.py
=============

Fully compatible with fallback system.
No API dependency.
"""

from skill_testing_agent import (
    generate_task,
    evaluate_answer,
    calibrate_level,
    TASK_BANK
)

PASS = "✓"
FAIL = "✗"
results = []


def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((status, name, detail))
    print(f"  {status}  {name}")
    if detail:
        print(f"       {detail}")


print("\n" + "="*55)
print("  SKILL TESTING AGENT — COMPONENT TESTS")
print("="*55)


# ── TEST 1: Task Bank ───────────────────────────────────

print("\n[1] Task Bank coverage")
for skill in TASK_BANK:
    for level in TASK_BANK[skill]:
        task = TASK_BANK[skill][level]
        check(f"{skill}/{level}", len(task) > 20)


# ── TEST 2: Calibration ─────────────────────────────────

print("\n[2] Difficulty calibrator")

check("Weak → down",
      calibrate_level("intermediate", 0.2) == "beginner")

check("Medium → same",
      calibrate_level("intermediate", 0.5) == "intermediate")

check("Strong → up",
      calibrate_level("intermediate", 0.8) == "advanced")


# ── TEST 3: Task generation ─────────────────────────────

print("\n[3] Task generation")

task = generate_task("python", "beginner")
check("Task generated", len(task) > 20)


# ── TEST 4: Evaluation ──────────────────────────────────

print("\n[4] Evaluation")

good_answer = """
def is_palindrome(s):
    return s == s[::-1]
"""

bad_answer = "idk"

eval_good = evaluate_answer(
    "python",
    "beginner",
    "check palindrome",
    good_answer
)

eval_bad = evaluate_answer(
    "python",
    "beginner",
    "check palindrome",
    bad_answer
)

# ✅ Updated conditions (IMPORTANT)

check("Good answer score >= 0.6",
      eval_good["score"] >= 0.6,
      f"score: {eval_good['score']}")

check("Bad < Good",
      eval_bad["score"] < eval_good["score"],
      f"bad: {eval_bad['score']} vs good: {eval_good['score']}")

check("Empty low score",
      evaluate_answer("python", "beginner", "x", "")["score"] <= 0.3)


# ── TEST 5: Schema ─────────────────────────────────────

print("\n[5] Output schema")

required = [
    "score", "total", "verdict",
    "strengths", "improvements",
    "correctness", "completeness",
    "code_quality", "edge_cases"
]

for field in required:
    check(f"{field} present", field in eval_good)


# ── SUMMARY ─────────────────────────────────────────────

passed = sum(1 for r in results if r[0] == PASS)
total = len(results)

print("\n" + "="*55)
print(f"  TESTS PASSED: {passed}/{total}")

if passed == total:
    print("  ALL TESTS PASSED — AGENT READY 🚀")
else:
    print("  Some tests failed — check above.")

print("="*55)