"""
test_agent.py — Full Test Suite for SkillTrust Skill Testing Agent
===================================================================
Tests: calibration, task generation, evaluation, schema, EvalResult,
       end-to-end integration, JSON parsing, TASK_BANK integrity,
       AzureLLMClient multi-endpoint + key rotation, SkillEvaluator.

Run standalone:   python test_agent.py
Run with pytest:  pytest test_agent.py -v
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

try:
    from skill_testing_agent import (
        TASK_BANK,
        Level,
        EvalResult,
        AzureLLMClient,
        Task,
        _LEVEL_MULTIPLIER,
        _AZURE_ENDPOINTS,
        _parse_llm_eval,
        _rule_based_score,
        _skill_evaluator,
        calibrate_level,
        evaluate_answer,
        generate_task,
        run_agent,
    )
except ModuleNotFoundError as exc:
    print(f"ERROR: Could not import skill_testing_agent — {exc}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Minimal test framework
# ---------------------------------------------------------------------------

_PASS   = 0
_FAIL   = 0
_ERRORS: list[str] = []


def test(name: str, condition: bool, detail: str = "") -> None:
    global _PASS, _FAIL
    if condition:
        _PASS += 1
        print(f"  ✅  {name}")
    else:
        _FAIL += 1
        msg = f"  ❌  {name}" + (f"\n       → {detail}" if detail else "")
        print(msg)
        _ERRORS.append(msg)


def section(title: str) -> None:
    print(f"\n{'─' * 64}")
    print(f"  {title}")
    print(f"{'─' * 64}")


# ---------------------------------------------------------------------------
# 1. Level Calibration
# ---------------------------------------------------------------------------

def test_calibration() -> None:
    section("1. Level Calibration")

    test("intermediate + 0.5 → intermediate",
         calibrate_level("intermediate", 0.5) == Level.INTERMEDIATE)
    test("evidence 0.3 → keep level",
         calibrate_level("intermediate", 0.3) == Level.INTERMEDIATE)
    test("evidence 0.7 → keep level",
         calibrate_level("intermediate", 0.7) == Level.INTERMEDIATE)
    test("beginner + 0.8 → intermediate",
         calibrate_level("beginner", 0.8) == Level.INTERMEDIATE)
    test("intermediate + 0.75 → advanced",
         calibrate_level("intermediate", 0.75) == Level.ADVANCED)
    test("intermediate + 0.2 → beginner",
         calibrate_level("intermediate", 0.2) == Level.BEGINNER)
    test("advanced + 0.1 → intermediate",
         calibrate_level("advanced", 0.1) == Level.INTERMEDIATE)
    test("beginner + 0.1 stays beginner (floor)",
         calibrate_level("beginner", 0.1) == Level.BEGINNER)
    test("advanced + 0.9 stays advanced (ceiling)",
         calibrate_level("advanced", 0.9) == Level.ADVANCED)
    test("evidence 0.0 → downgrade",
         calibrate_level("intermediate", 0.0) == Level.BEGINNER)
    test("evidence 1.0 → upgrade",
         calibrate_level("intermediate", 1.0) == Level.ADVANCED)
    result = calibrate_level("expert", 0.5)
    test("unknown level 'expert' → valid Level",
         isinstance(result, Level))
    test("unknown level defaults to intermediate",
         result == Level.INTERMEDIATE)
    test("'BEGINNER' uppercase handled",
         calibrate_level("BEGINNER", 0.5) == Level.BEGINNER)
    test("'Advanced' mixed-case handled",
         calibrate_level("Advanced", 0.5) == Level.ADVANCED)


# ---------------------------------------------------------------------------
# 2. Task Generation
# ---------------------------------------------------------------------------

def test_task_generation() -> None:
    section("2. Task Generation (TASK_BANK fallback — no API key needed)")

    for skill in list(TASK_BANK.keys()):
        for level in [Level.BEGINNER, Level.INTERMEDIATE, Level.ADVANCED]:
            task = generate_task(skill, level)
            test(f"[{skill}/{level.value}] Task instance",       isinstance(task, Task))
            test(f"[{skill}/{level.value}] description non-empty", bool(task.description.strip()))
            test(f"[{skill}/{level.value}] >= 20 chars",           len(task.description) >= 20)
            test(f"[{skill}/{level.value}] skill matches",          task.skill == skill)
            test(f"[{skill}/{level.value}] level matches",          task.level == level)
            test(f"[{skill}/{level.value}] source valid",           task.source in ("llm", "fallback"))

    task = generate_task("cobol", Level.BEGINNER)
    test("Unknown skill 'cobol' → no crash",       isinstance(task, Task))
    test("Unknown skill description non-empty",     len(task.description) >= 20)

    task = generate_task("", Level.INTERMEDIATE)
    test("Empty skill handled without crash",        isinstance(task, Task))

    task = generate_task("  Python  ", Level.BEGINNER)
    test("Skill with whitespace handled",            isinstance(task, Task))


# ---------------------------------------------------------------------------
# 3. Evaluation
# ---------------------------------------------------------------------------

def test_evaluation() -> None:
    section("3. Evaluation — rule-based fallback + evaluate_answer")

    python_task = Task(
        skill="python", level=Level.INTERMEDIATE,
        description="Implement merge_sorted_lists(a, b) in O(n+m).", source="fallback",
    )

    good_answer = (
        "def merge_sorted_lists(a: list[int], b: list[int]) -> list[int]:\n"
        "    \"\"\"Merge in O(n+m).\"\"\"\n"
        "    result, i, j = [], 0, 0\n"
        "    while i < len(a) and j < len(b):\n"
        "        if a[i] <= b[j]:\n"
        "            result.append(a[i]); i += 1\n"
        "        else:\n"
        "            result.append(b[j]); j += 1\n"
        "    return result + a[i:] + b[j:]\n"
        "# Edge: empty inputs handled by while guard\n"
        "assert merge_sorted_lists([], [1]) == [1]\n"
    )
    bad_answer   = "I don't know how to do this."
    empty_answer = ""

    r_good, s_good, i_good = _rule_based_score(python_task, good_answer)
    r_bad,  _,      _      = _rule_based_score(python_task, bad_answer)

    test("Good correctness >= bad correctness",    r_good.correctness >= r_bad.correctness)
    test("Good total > bad total",                 r_good.total > r_bad.total)
    test("All scores in 0–25",
         all(0 <= v <= 25 for v in [r_good.correctness, r_good.completeness,
                                     r_good.code_quality, r_good.edge_cases]))
    test("strengths is non-empty string",          isinstance(s_good, str) and len(s_good) > 0)
    test("improvements is non-empty string",       isinstance(i_good, str) and len(i_good) > 0)

    adv_task = Task(skill="python", level=Level.ADVANCED,     description="x", source="fallback")
    int_task = Task(skill="python", level=Level.INTERMEDIATE, description="x", source="fallback")
    beg_task = Task(skill="python", level=Level.BEGINNER,     description="x", source="fallback")

    r_adv, _, _ = _rule_based_score(adv_task, good_answer)
    r_int, _, _ = _rule_based_score(int_task, good_answer)
    r_beg, _, _ = _rule_based_score(beg_task, good_answer)

    test("Advanced <= Intermediate (stricter)",    r_adv.total <= r_int.total)
    test("Intermediate <= Beginner (stricter)",    r_int.total <= r_beg.total)
    test("Multiplier ordering correct",
         _LEVEL_MULTIPLIER[Level.BEGINNER]
         > _LEVEL_MULTIPLIER[Level.INTERMEDIATE]
         > _LEVEL_MULTIPLIER[Level.ADVANCED])

    out_good  = evaluate_answer(python_task, good_answer)
    out_bad   = evaluate_answer(python_task, bad_answer)
    out_empty = evaluate_answer(python_task, empty_answer)

    test("Empty answer → score = 0.0",            out_empty["score"] == 0.0)
    test("Empty answer → all dims = 0",
         all(out_empty[k] == 0 for k in ["correctness","completeness","code_quality","edge_cases"]))
    test("Good score >= bad score",               out_good["score"] >= out_bad["score"])

    for skill in ["react", "sql", "ml", "fastapi"]:
        t = Task(skill=skill, level=Level.INTERMEDIATE, description="...", source="fallback")
        r = evaluate_answer(t, "SELECT FROM WHERE def class function return useState import")
        test(f"No crash for skill={skill}",       isinstance(r, dict) and "score" in r)


# ---------------------------------------------------------------------------
# 4. Output Schema Validation
# ---------------------------------------------------------------------------

_REQUIRED_KEYS = {
    "correctness", "completeness", "code_quality", "edge_cases",
    "total", "score", "verdict", "strengths", "improvements",
}


def test_output_schema() -> None:
    section("4. Output Schema Validation")

    task = Task(skill="python", level=Level.INTERMEDIATE,
                description="Write merge sort.", source="fallback")
    answer = (
        "def merge_sort(arr):\n"
        "    # base case\n"
        "    if len(arr) <= 1: return arr\n"
        "    mid = len(arr) // 2\n"
        "    return merge(merge_sort(arr[:mid]), merge_sort(arr[mid:]))\n"
    )
    output = evaluate_answer(task, answer)

    test("All required keys present",
         _REQUIRED_KEYS.issubset(output.keys()),
         f"Missing: {_REQUIRED_KEYS - output.keys()}")
    test("score is float",              isinstance(output["score"], float))
    test("score in [0.0, 1.0]",         0.0 <= output["score"] <= 1.0)
    test("total == sum of 4 dims",
         output["total"] == sum(output[k] for k in
             ["correctness","completeness","code_quality","edge_cases"]))
    test("verdict in Pass/Partial/Fail", output["verdict"] in ("Pass", "Partial", "Fail"))
    for dim in ["correctness", "completeness", "code_quality", "edge_cases"]:
        test(f"{dim} in 0–25",           0 <= output[dim] <= 25, f"Got {output[dim]}")
    test("total in 0–100",              0 <= output["total"] <= 100)
    test("strengths is string",         isinstance(output["strengths"], str))
    test("improvements is string",      isinstance(output["improvements"], str))

    er = EvalResult(**{k: output[k] for k in ["correctness","completeness","code_quality","edge_cases"]})
    test("verdict matches EvalResult property", output["verdict"] == er.verdict)

    try:
        json.dumps(output)
        test("JSON-serialisable", True)
    except TypeError as exc:
        test("JSON-serialisable", False, str(exc))

    test("No None values", all(v is not None for v in output.values()))


# ---------------------------------------------------------------------------
# 5. EvalResult Unit Tests
# ---------------------------------------------------------------------------

def test_eval_result() -> None:
    section("5. EvalResult — unit tests")

    r = EvalResult(25, 25, 25, 25)
    test("Perfect total = 100",          r.total == 100)
    test("Perfect score = 1.0",          r.score == 1.0)
    test("Perfect verdict = Pass",       r.verdict == "Pass")

    r2 = EvalResult(10, 10, 10, 10)
    test("40/100 score = 0.4",           r2.score == 0.4)
    test("40/100 verdict = Partial",     r2.verdict == "Partial")

    r3 = EvalResult(5, 5, 5, 5)
    test("20/100 verdict = Fail",        r3.verdict == "Fail")

    r4 = EvalResult()
    test("Default total = 0",            r4.total == 0)
    test("Default score = 0.0",          r4.score == 0.0)
    test("Default verdict = Fail",       r4.verdict == "Fail")

    d = r.to_dict(strengths="Great.", improvements="Nothing.")
    test("to_dict has all keys",         _REQUIRED_KEYS.issubset(d.keys()))
    test("to_dict strengths correct",    d["strengths"] == "Great.")
    test("to_dict improvements correct", d["improvements"] == "Nothing.")

    r5 = EvalResult(16, 16, 17, 16)   # total=65 → 0.65 → Pass
    test("Score 0.65 → Pass",           r5.verdict == "Pass")

    r6 = EvalResult(10, 10, 10, 10)   # total=40 → 0.40 → Partial
    test("Score 0.40 → Partial",        r6.verdict == "Partial")


# ---------------------------------------------------------------------------
# 6. run_agent — end-to-end
# ---------------------------------------------------------------------------

def test_run_agent() -> None:
    section("6. run_agent — end-to-end integration")

    out = run_agent("python", "intermediate", 0.5)
    test("task-only: has task_description",
         "task_description" in out and len(out["task_description"]) >= 20)
    test("task-only: calibrated_level correct",   out.get("calibrated_level") == "intermediate")
    test("task-only: task_source valid",           out.get("task_source") in ("llm", "fallback"))
    test("task-only: no 'score' key",             "score"   not in out)
    test("task-only: no 'verdict' key",           "verdict" not in out)

    out2 = run_agent(
        skill="react", claimed_level="beginner", evidence=0.85,
        answer=(
            "function Counter() {\n"
            "  const [count, setCount] = React.useState(0);\n"
            "  return <div>\n"
            "    <button onClick={() => setCount(c => c-1)}>-</button>\n"
            "    {count}\n"
            "    <button onClick={() => setCount(c => c+1)}>+</button>\n"
            "  </div>;\n"
            "}"
        ),
    )
    test("full pipeline: has score",              "score" in out2)
    test("full pipeline: upgrades beginner+0.85 → intermediate",
         out2.get("calibrated_level") == "intermediate")
    test("full pipeline: full schema",            _REQUIRED_KEYS.issubset(out2.keys()))
    test("full pipeline: score in [0,1]",         0.0 <= out2.get("score", -1) <= 1.0)

    out3 = run_agent("sql", "advanced", 0.15)
    test("downgrades advanced+0.15 → intermediate",
         out3.get("calibrated_level") == "intermediate")

    try:
        run_agent("", "expert", 2.5, answer="")
        test("garbage inputs: no crash", True)
    except Exception as exc:
        test("garbage inputs: no crash", False, str(exc))

    out5 = run_agent("ml", "beginner", 0.4, answer=None)
    test("answer=None → no score key",            "score" not in out5)

    for skill in TASK_BANK.keys():
        try:
            r = run_agent(skill, "intermediate", 0.5, answer="def return class if for import")
            test(f"no crash for skill={skill}",   isinstance(r, dict))
        except Exception as exc:
            test(f"no crash for skill={skill}",   False, str(exc))


# ---------------------------------------------------------------------------
# 7. _parse_llm_eval
# ---------------------------------------------------------------------------

def test_parse_llm_eval() -> None:
    section("7. _parse_llm_eval — JSON extraction")

    clean = ('{"correctness":20,"completeness":18,"code_quality":22,'
             '"edge_cases":15,"strengths":"Good","improvements":"More"}')
    r = _parse_llm_eval(clean)
    test("Clean JSON parsed",                      r is not None and r["correctness"] == 20)

    fenced = ('```json\n{"correctness":10,"completeness":12,"code_quality":10,'
              '"edge_cases":8,"strengths":"ok","improvements":"n/a"}\n```')
    r2 = _parse_llm_eval(fenced)
    test("Strips ```json fences",                  r2 is not None and r2["completeness"] == 12)

    plain_fenced = ('```\n{"correctness":15,"completeness":15,"code_quality":15,'
                    '"edge_cases":10,"strengths":"s","improvements":"i"}\n```')
    test("Strips plain fences",                    _parse_llm_eval(plain_fenced) is not None)

    with_prose = ('Here:\n{"correctness":18,"completeness":20,"code_quality":17,'
                  '"edge_cases":14,"strengths":"s","improvements":"i"}\nDone.')
    r3 = _parse_llm_eval(with_prose)
    test("Extracts JSON from prose",               r3 is not None and r3["correctness"] == 18)

    test("None for plain text",                    _parse_llm_eval("Great work!") is None)
    test("None for missing keys",
         _parse_llm_eval('{"correctness":10,"completeness":10}') is None)
    test("None for empty string",                  _parse_llm_eval("") is None)
    test("None for malformed JSON",
         _parse_llm_eval('{"correctness": 10,') is None)


# ---------------------------------------------------------------------------
# 8. TASK_BANK Integrity
# ---------------------------------------------------------------------------

def test_task_bank() -> None:
    section("8. TASK_BANK integrity")

    all_levels = [Level.BEGINNER, Level.INTERMEDIATE, Level.ADVANCED]
    for skill, levels_dict in TASK_BANK.items():
        test(f"TASK_BANK[{skill}] has all 3 levels",
             all(lv in levels_dict for lv in all_levels))
        for level in all_levels:
            entries = levels_dict.get(level, [])
            test(f"[{skill}/{level.value}] >= 1 entry", len(entries) >= 1)
            for i, e in enumerate(entries):
                test(f"[{skill}/{level.value}][{i}] >= 20 chars",
                     isinstance(e, str) and len(e) >= 20, f"Got {len(e)}")


# ---------------------------------------------------------------------------
# 9. AzureLLMClient — config, multi-endpoint, key rotation
# ---------------------------------------------------------------------------

def test_azure_llm_client() -> None:
    section("9. AzureLLMClient — multi-endpoint + key rotation")

    def _make(targets: list[dict]) -> AzureLLMClient:
        c = AzureLLMClient.__new__(AzureLLMClient)
        c._targets       = targets
        c.api_version    = "2024-02-15-preview"
        c.timeout        = 10
        c._model_override = ""
        return c

    # No targets → not configured
    c_empty = _make([])
    test("_is_configured() False when no targets",  not c_empty._is_configured())
    test("complete() returns None when unconfigured (no crash)",
         c_empty.complete("sys", "usr") is None)

    # With targets → configured
    c_ok = _make([
        {"endpoint": "https://ep1.openai.azure.com/openai/v1",
         "api_key": "key1", "label": "ep1", "model": "gpt-4o"},
    ])
    test("_is_configured() True when targets exist", c_ok._is_configured())

    # status() returns structured info
    c_status = _make([
        {"endpoint": "https://nikxgupta-9818-resource.openai.azure.com/openai/v1",
         "api_key": "key1", "label": "endpoint-9818", "model": "gpt-4o"},
        {"endpoint": "https://nikxgupta-6518-resource.openai.azure.com/openai/v1",
         "api_key": "key2", "label": "endpoint-6518", "model": "gpt-4o"},
    ])
    s = c_status.status()
    test("status() has configured_endpoints",       "configured_endpoints" in s)
    test("status() shows 2 endpoints",              s["configured_endpoints"] == 2)
    test("status() has endpoints list",             isinstance(s["endpoints"], list))
    test("status() each endpoint has label",
         all("label" in ep for ep in s["endpoints"]))
    test("status() each endpoint has has_key",
         all("has_key" in ep for ep in s["endpoints"]))

    # Verify both hardcoded endpoints are present in _AZURE_ENDPOINTS
    endpoint_urls = [cfg["endpoint"] for cfg in _AZURE_ENDPOINTS]
    test("Endpoint-9818 in _AZURE_ENDPOINTS",
         any("9818" in url for url in endpoint_urls))
    test("Endpoint-6518 in _AZURE_ENDPOINTS",
         any("6518" in url for url in endpoint_urls))
    test("_AZURE_ENDPOINTS has 2 entries",          len(_AZURE_ENDPOINTS) == 2)

    # Each endpoint config has required keys
    for cfg in _AZURE_ENDPOINTS:
        test(f"[{cfg.get('label','')}] has 'endpoint' key",  "endpoint" in cfg)
        test(f"[{cfg.get('label','')}] has 'key_env' key",   "key_env"  in cfg)
        test(f"[{cfg.get('label','')}] has 'label' key",     "label"    in cfg)
        test(f"[{cfg.get('label','')}] endpoint starts with https",
             cfg["endpoint"].startswith("https://"))

    # Fallback key env var logic
    test("fallback_key_env key exists in each endpoint config",
         all("fallback_key_env" in cfg for cfg in _AZURE_ENDPOINTS))


# ---------------------------------------------------------------------------
# 10. SkillEvaluator Registry
# ---------------------------------------------------------------------------

def test_skill_evaluator() -> None:
    section("10. SkillEvaluator — hint registry")

    for skill in ["python", "react", "sql", "ml", "fastapi"]:
        h = _skill_evaluator.hint(skill)
        test(f"hint for '{skill}' non-empty",      isinstance(h, str) and len(h) > 10)

    test("Unknown skill → default hint (no crash)",
         isinstance(_skill_evaluator.hint("cobol"), str))
    test("Default hint non-empty",
         len(_skill_evaluator.hint("unknown")) > 10)
    test("Case-insensitive lookup",
         _skill_evaluator.hint("Python") == _skill_evaluator.hint("python"))
    test("Whitespace-stripped lookup",
         _skill_evaluator.hint("  sql  ") == _skill_evaluator.hint("sql"))


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n" + "=" * 64)
    print("  SkillTrust Agent — Full Test Suite")
    print("  (Azure OpenAI — multi-endpoint with key rotation)")
    print("=" * 64)

    test_calibration()
    test_task_generation()
    test_evaluation()
    test_output_schema()
    test_eval_result()
    test_run_agent()
    test_parse_llm_eval()
    test_task_bank()
    test_azure_llm_client()
    test_skill_evaluator()

    total = _PASS + _FAIL
    print("\n" + "=" * 64)
    print(f"  Results: {_PASS}/{total} passed, {_FAIL} failed")
    print("=" * 64)

    if _ERRORS:
        print("\nFailed tests:")
        for e in _ERRORS:
            print(e)
        sys.exit(1)
    else:
        print(f"\n  All {_PASS} tests passed! ✅")


if __name__ == "__main__":
    main()