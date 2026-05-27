"""
SkillTrust — Skill Testing Agent (Person 4)
============================================
Production-ready, fully modular, fallback-safe.

Inputs  : skill, claimed_level, evidence_score
Outputs : structured JSON with multi-dimensional scores + verdict
"""

from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from openai import AzureOpenAI

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("SkillTrust.Agent")


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------

class Level(str, Enum):
    BEGINNER     = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED     = "advanced"

    def __lt__(self, other: "Level") -> bool:
        return _LEVEL_ORDER[self] < _LEVEL_ORDER[other]

    def __le__(self, other: "Level") -> bool:
        return _LEVEL_ORDER[self] <= _LEVEL_ORDER[other]

    def __gt__(self, other: "Level") -> bool:
        return _LEVEL_ORDER[self] > _LEVEL_ORDER[other]

    def __ge__(self, other: "Level") -> bool:
        return _LEVEL_ORDER[self] >= _LEVEL_ORDER[other]


_LEVEL_ORDER: dict[Level, int] = {
    Level.BEGINNER:     0,
    Level.INTERMEDIATE: 1,
    Level.ADVANCED:     2,
}
_LEVEL_UP: dict[Level, Level] = {
    Level.BEGINNER:     Level.INTERMEDIATE,
    Level.INTERMEDIATE: Level.ADVANCED,
    Level.ADVANCED:     Level.ADVANCED,
}
_LEVEL_DOWN: dict[Level, Level] = {
    Level.BEGINNER:     Level.BEGINNER,
    Level.INTERMEDIATE: Level.BEGINNER,
    Level.ADVANCED:     Level.INTERMEDIATE,
}

PASS_THRESHOLD    = 0.65
PARTIAL_THRESHOLD = 0.40
DIM_MAX           = 25


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class EvalResult:
    correctness:  int = 0
    completeness: int = 0
    code_quality: int = 0
    edge_cases:   int = 0

    @property
    def total(self) -> int:
        return self.correctness + self.completeness + self.code_quality + self.edge_cases

    @property
    def score(self) -> float:
        return round(self.total / 100, 3)

    @property
    def verdict(self) -> str:
        s = self.score
        if s >= PASS_THRESHOLD:    return "Pass"
        if s >= PARTIAL_THRESHOLD: return "Partial"
        return "Fail"

    def to_dict(self, strengths: str = "", improvements: str = "") -> dict[str, Any]:
        return {
            "correctness":  self.correctness,
            "completeness": self.completeness,
            "code_quality": self.code_quality,
            "edge_cases":   self.edge_cases,
            "total":        self.total,
            "score":        self.score,
            "verdict":      self.verdict,
            "strengths":    strengths,
            "improvements": improvements,
        }


@dataclass
class Task:
    skill:       str
    level:       Level
    description: str
    hints:       list[str] = field(default_factory=list)
    source:      str = "llm"


# ---------------------------------------------------------------------------
# Task Bank
# ---------------------------------------------------------------------------

TASK_BANK: dict[str, dict[Level, list[str]]] = {
    "python": {
        Level.BEGINNER: [
            "Write a Python function `reverse_string(s: str) -> str` that returns the "
            "string reversed. Include at least two test cases.",

            "Write a Python function `is_palindrome(s: str) -> bool` that checks if a "
            "string reads the same forwards and backwards (case-insensitive). Show test cases.",

            "Write a Python function `count_vowels(s: str) -> int` that counts the vowels "
            "in a string. Demonstrate with examples.",
        ],
        Level.INTERMEDIATE: [
            "Implement a Python class `Stack` with push, pop, peek, and is_empty methods "
            "using a list internally. Include error handling for underflow.",

            "Write a Python function `merge_sorted_lists(a: list[int], b: list[int]) -> "
            "list[int]` that merges two sorted lists in O(n+m) time without using sort(). "
            "Add edge-case tests.",

            "Implement an LRU Cache class in Python with `get(key)` and `put(key, value)` "
            "operations in O(1) using only stdlib. Explain your design choices in comments.",
        ],
        Level.ADVANCED: [
            "Implement a thread-safe singleton metaclass in Python that lazily initialises "
            "the instance. Demonstrate it with a concrete example and explain why your "
            "approach is thread-safe.",

            "Write a Python decorator `@retry(max_attempts, delay)` that retries a function "
            "on exception with exponential back-off. Include typing, logging, and edge-case "
            "handling.",

            "Implement a memory-efficient generator-based pipeline: `read_lines(file_path)` "
            "-> `parse_records(lines)` -> `filter_valid(records)` -> `aggregate(records)`. "
            "Each stage must be a generator. Discuss time and space complexity.",
        ],
    },
    "react": {
        Level.BEGINNER: [
            "Write a React functional component `Counter` that shows a number and has "
            "Increment / Decrement buttons using useState. Show the JSX only.",

            "Write a React component `Greeting` that accepts a `name` prop and renders "
            "'Hello, {name}!' If name is missing, render 'Hello, Guest!'.",

            "Write a React component `ToggleText` that shows 'ON' or 'OFF' and toggles "
            "on button click using useState.",
        ],
        Level.INTERMEDIATE: [
            "Write a React custom hook `useFetch(url)` that returns `{data, loading, "
            "error}`. Handle cleanup to avoid setting state on unmounted components.",

            "Implement a React `<SearchableList items={[...]} />` component that filters "
            "a list of strings as the user types. Use useMemo to avoid redundant filtering.",

            "Write a React context + reducer setup for a simple shopping cart: add, remove, "
            "and clear actions. Show the context, reducer, and a consumer component.",
        ],
        Level.ADVANCED: [
            "Design a React compound component pattern for a `<Tabs>` UI: `<Tabs>`, "
            "`<Tabs.List>`, `<Tabs.Tab>`, `<Tabs.Panel>`. Use Context to share state, "
            "support keyboard navigation (Arrow keys + Enter), and add correct ARIA roles.",

            "Implement a React `<VirtualList items={[...]} itemHeight={50} "
            "containerHeight={400} />` component that only renders visible items. "
            "Explain the scroll-offset math in comments.",

            "Write a React higher-order component `withErrorBoundary(Component, FallbackUI)` "
            "and a hook-friendly wrapper using an Error Boundary class. Explain each decision.",
        ],
    },
    "sql": {
        Level.BEGINNER: [
            "Given `employees(id, name, department, salary)`, write a SQL query to find "
            "all employees in 'Engineering' ordered by salary descending.",

            "Write a SQL query on `orders(order_id, customer_id, amount, created_at)` to "
            "find the total amount spent by each customer.",

            "Write a SQL query to find employees whose salary is above the average salary "
            "from `employees(id, name, salary)`.",
        ],
        Level.INTERMEDIATE: [
            "Given `employees(id, name, manager_id, salary)`, write a SQL query using a "
            "self-join to list each employee alongside their manager's name.",

            "Write a SQL query using a window function to rank employees by salary within "
            "each department. Handle ties using DENSE_RANK.",

            "Given `orders` and `customers` tables, return customers with more than 3 "
            "orders and total amount > 1000. Show name, order count, and total.",
        ],
        Level.ADVANCED: [
            "Write a recursive CTE to find the full reporting chain from a given "
            "employee_id up to the CEO in `employees(id, name, manager_id)`. Handle cycles.",

            "Given `events(user_id, event_type, occurred_at)`, write SQL to compute a "
            "7-day rolling retention rate using only standard SQL window functions.",

            "Design SQL DDL and a complex query for an inventory system with products, "
            "warehouses, and stock_movements. Find products below reorder threshold using "
            "a CTE pipeline.",
        ],
    },
    "ml": {
        Level.BEGINNER: [
            "Explain the difference between supervised and unsupervised learning with one "
            "real-world example each. Define what 'training data' means in each context.",

            "In your own words, explain what overfitting is and describe two techniques "
            "to prevent it.",

            "Describe what a confusion matrix is and define precision and recall. "
            "Provide a small numeric 2x2 example.",
        ],
        Level.INTERMEDIATE: [
            "Write Python pseudocode implementing gradient descent for linear regression "
            "with MSE loss. Show the weight update rule and explain each term.",

            "Explain the bias-variance tradeoff and how model complexity affects both. "
            "Describe the classic U-curve error diagram.",

            "Describe steps to handle a highly imbalanced classification dataset "
            "(90% negative / 10% positive). Name at least four specific techniques.",
        ],
        Level.ADVANCED: [
            "Derive the back-propagation update rule for a two-layer neural network with "
            "sigmoid activations and cross-entropy loss. Show all chain-rule steps.",

            "Design a complete ML pipeline for time-series anomaly detection: feature "
            "engineering, model choice, evaluation strategy avoiding data leakage, and "
            "deployment considerations.",

            "Explain scaled dot-product attention and multi-head attention mathematics. "
            "Implement scaled dot-product attention in NumPy (no PyTorch/TF).",
        ],
    },
    "fastapi": {
        Level.BEGINNER: [
            "Write a FastAPI app with a GET `/hello/{name}` endpoint returning "
            '`{"message": "Hello, {name}!"}`. Include imports and a uvicorn run call.',

            "Write a FastAPI POST `/items` that accepts a Pydantic `Item(name, price)` "
            "model and returns it with an added `id: int` field.",

            "Write FastAPI endpoints: GET `/items` returning a list, and "
            "GET `/items/{item_id}` returning one item or raising HTTPException 404.",
        ],
        Level.INTERMEDIATE: [
            "Implement FastAPI dependency injection: a `get_db()` dependency that yields "
            "a fake DB session, used in two endpoints. Show how to override it in tests.",

            "Write a FastAPI router for a `users` resource with full CRUD, Pydantic "
            "create/update/response schemas, and a custom `UserNotFoundError` handler.",

            "Implement JWT-based auth in FastAPI: a `/token` POST returning a JWT, and "
            "a `get_current_user` dependency validating it with `python-jose`.",
        ],
        Level.ADVANCED: [
            "Design a FastAPI middleware that rate-limits requests per IP using an "
            "in-process sliding window counter (no Redis). Explain thread-safety.",

            "Implement a FastAPI background task system: POST `/tasks` enqueues a job; "
            "GET `/tasks/{id}` polls status. Discuss limitations vs Celery.",

            "Write a FastAPI app with WebSocket support for a chat room: connection "
            "manager, broadcast, graceful disconnect. Discuss horizontal scaling challenges.",
        ],
    },
}

SUPPORTED_SKILLS = set(TASK_BANK.keys())


# ---------------------------------------------------------------------------
# Level Calibration
# ---------------------------------------------------------------------------

def calibrate_level(claimed: str, evidence: float) -> Level:
    """
    Adjust difficulty based on evidence score.
    evidence < 0.3  → downgrade | evidence > 0.7 → upgrade | else → keep
    """
    try:
        base = Level(claimed.lower().strip())
    except ValueError:
        log.warning("Unknown level '%s', defaulting to intermediate.", claimed)
        base = Level.INTERMEDIATE

    if evidence < 0.3:
        calibrated = _LEVEL_DOWN[base]
        log.info("Evidence %.2f < 0.3 → downgrading %s → %s",
                 evidence, base.value, calibrated.value)
    elif evidence > 0.7:
        calibrated = _LEVEL_UP[base]
        log.info("Evidence %.2f > 0.7 → upgrading %s → %s",
                 evidence, base.value, calibrated.value)
    else:
        calibrated = base
        log.info("Evidence %.2f in [0.3, 0.7] → keeping %s", evidence, base.value)

    return calibrated


# ---------------------------------------------------------------------------
# Azure OpenAI Client — NEW (mentor-provided, using openai SDK)
# ---------------------------------------------------------------------------

# ── Defaults (override via environment variables) ────────────────────────────
_DEFAULT_ENDPOINT   = "https://nikxgupta-9818-resource.cognitiveservices.azure.com/"
_DEFAULT_KEY        = " "
_DEFAULT_API_VERSION = "2024-10-21"
_DEFAULT_DEPLOYMENT  = "gpt-4.1"


class AzureLLMClient:
    """
    Thin wrapper around the official openai SDK's AzureOpenAI client.

    Configuration (environment variables override the hardcoded defaults):
      AZURE_OPENAI_ENDPOINT     — Azure Cognitive Services endpoint URL
      AZURE_OPENAI_KEY          — API key
      AZURE_OPENAI_API_VERSION  — API version  (default: 2024-10-21)
      AZURE_OPENAI_DEPLOYMENT   — Deployment / model name (default: gpt-4.1)
    """

    def __init__(self) -> None:
        self._deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", _DEFAULT_DEPLOYMENT)
        try:
            self._client = AzureOpenAI(
                azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", _DEFAULT_ENDPOINT),
                api_key=os.getenv("AZURE_OPENAI_KEY", _DEFAULT_KEY),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", _DEFAULT_API_VERSION),
            )
            self._configured = True
            log.info(
                "Azure LLM client ready — endpoint: %s | deployment: %s",
                os.getenv("AZURE_OPENAI_ENDPOINT", _DEFAULT_ENDPOINT),
                self._deployment,
            )
        except Exception as exc:
            log.warning("Failed to initialise AzureOpenAI client: %s", exc)
            self._configured = False

    def complete(self, system_prompt: str, user_prompt: str) -> str | None:
        """
        Send a chat completion request.
        Returns the response text, or None on any failure (never raises).
        """
        if not self._configured:
            log.info("Azure client not configured — using fallback.")
            return None

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]

        try:
            resp = self._client.chat.completions.create(
                model=self._deployment,
                messages=messages,
                temperature=0.3,
                max_tokens=1024,
            )
            content = resp.choices[0].message.content or ""
            log.info("Azure LLM call succeeded.")
            return content
        except Exception as exc:
            log.warning("Azure LLM call failed: %s", exc)
            return None

    def status(self) -> dict[str, Any]:
        """Return current configuration for diagnostics."""
        return {
            "configured":  self._configured,
            "endpoint":    os.getenv("AZURE_OPENAI_ENDPOINT", _DEFAULT_ENDPOINT),
            "deployment":  self._deployment,
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", _DEFAULT_API_VERSION),
        }


# Module-level singleton
_llm = AzureLLMClient()


# ---------------------------------------------------------------------------
# Task Generation
# ---------------------------------------------------------------------------

_TASK_GEN_SYSTEM = """
You are a technical interviewer creating fair, practical assessment tasks.

Strict rules:
- Task must be solvable in a plain text editor — no database server, container, or cloud setup.
- No ambiguous or purely subjective questions.
- Must clearly test the specified skill and difficulty level.
- Output ONLY the task description — no preamble, labels, or commentary.
- Maximum 120 words.
""".strip()


def _task_gen_user_prompt(skill: str, level: Level) -> str:
    return (
        f"Generate ONE practical assessment task for a {level.value}-level {skill} developer. "
        "The task must produce verifiable, concrete output (working code, correct SQL, or a "
        "clear written explanation with examples). "
        "Do NOT ask the candidate to set up any servers, databases, cloud services, or "
        "external systems."
    )


def generate_task(skill: str, level: Level) -> Task:
    """
    Generate an assessment task.
    Primary  : Azure OpenAI LLM (dynamic, varied).
    Fallback : Random pick from TASK_BANK (always available).
    """
    normalized = skill.lower().strip()

    raw = _llm.complete(_TASK_GEN_SYSTEM, _task_gen_user_prompt(normalized, level))
    if raw and len(raw.strip()) >= 20:
        log.info("Task generated via Azure OpenAI.")
        return Task(skill=normalized, level=level, description=raw.strip(), source="llm")

    log.info("Falling back to TASK_BANK for task generation.")
    bank_skill = normalized if normalized in TASK_BANK else "python"
    if normalized not in TASK_BANK:
        log.warning("Skill '%s' not in TASK_BANK — using 'python' tasks.", normalized)

    level_tasks = TASK_BANK[bank_skill].get(level) or next(iter(TASK_BANK[bank_skill].values()))
    return Task(skill=normalized, level=level, description=random.choice(level_tasks), source="fallback")


# ---------------------------------------------------------------------------
# Evaluation — LLM prompts
# ---------------------------------------------------------------------------

_EVAL_SYSTEM = """
You are a strict but fair technical evaluator scoring a candidate's answer to an assessment task.

Scoring dimensions (each 0–25 points, 100 total):
  correctness  — Is the core logic or explanation correct and accurate?
  completeness — Does the answer fully address all parts of the task?
  code_quality — Is it clean, readable, well-structured, and idiomatic?
  edge_cases   — Are edge cases handled or at least clearly acknowledged?

Respond ONLY with a valid JSON object in this exact schema.
No preamble, no trailing text, no markdown fences:
{
  "correctness":  <integer 0-25>,
  "completeness": <integer 0-25>,
  "code_quality": <integer 0-25>,
  "edge_cases":   <integer 0-25>,
  "strengths":    "<one concise sentence>",
  "improvements": "<one concise sentence>"
}
""".strip()


def _strictness_note(level: Level) -> str:
    return {
        Level.BEGINNER: (
            "Apply a LENIENT standard. Basic correctness is sufficient. "
            "Simple structure is acceptable."
        ),
        Level.INTERMEDIATE: (
            "Apply MODERATE strictness. Expect correct logic, reasonable structure, "
            "and some awareness of edge cases."
        ),
        Level.ADVANCED: (
            "Apply STRICT evaluation. Require optimised, clean, production-quality solutions. "
            "Penalise naive approaches and missing edge cases."
        ),
    }[level]


def _eval_user_prompt(task: Task, answer: str) -> str:
    return (
        f"Skill: {task.skill} | Level: {task.level.value}\n"
        f"Strictness: {_strictness_note(task.level)}\n\n"
        f"TASK:\n{task.description}\n\n"
        f"CANDIDATE ANSWER:\n{answer.strip()}"
    )


def _parse_llm_eval(raw: str) -> dict[str, Any] | None:
    """Extract and validate JSON from LLM response. Handles markdown fences and prose."""
    cleaned = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).replace("```", "").strip()
    match = re.search(r"\{.*?\}", cleaned, re.DOTALL)
    if match:
        cleaned = match.group(0)
    try:
        data = json.loads(cleaned)
    except (json.JSONDecodeError, TypeError):
        return None
    required = {"correctness", "completeness", "code_quality", "edge_cases"}
    if not required.issubset(data.keys()):
        return None
    return data


# ---------------------------------------------------------------------------
# Evaluation — Rule-based fallback
# ---------------------------------------------------------------------------

_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "python":  ["def ", "return", "class ", "import", "for ", "while ", "if ", ":"],
    "react":   ["function", "const ", "useState", "useEffect", "return", "=>", "<div", "props"],
    "sql":     ["SELECT", "FROM", "WHERE", "JOIN", "GROUP BY", "ORDER BY", "WITH", "HAVING"],
    "ml":      ["gradient", "loss", "epoch", "train", "accuracy", "precision", "recall", "bias"],
    "fastapi": ["@app", "FastAPI", "router", "Request", "Response", "Depends", "BaseModel"],
}
_GENERIC_SIGNALS  = ["return", "if", "for", "class", "def", "function", "import"]
_EDGE_KEYWORDS    = ["edge", "empty", "none", "null", "assert", "raise", "except",
                     "error", "zero", "negative", "boundary", "overflow", "corner"]
_LEVEL_MULTIPLIER = {Level.BEGINNER: 1.00, Level.INTERMEDIATE: 0.85, Level.ADVANCED: 0.70}


def _rule_based_score(task: Task, answer: str) -> tuple[EvalResult, str, str]:
    ans      = answer.strip()
    signals  = _SIGNAL_KEYWORDS.get(task.skill, _GENERIC_SIGNALS)
    hits     = sum(1 for kw in signals if kw.lower() in ans.lower())
    coverage = min(hits / max(len(signals), 1), 1.0)
    len_sc   = min(len(ans) / 300, 1.0)
    comments = any(m in ans for m in ("#", '"""', "'''", "/*", "--", "//"))
    edge_hit = any(kw in ans.lower() for kw in _EDGE_KEYWORDS)
    mult     = _LEVEL_MULTIPLIER[task.level]

    result = EvalResult(
        correctness  = min(int(coverage                           * 25 * mult), 25),
        completeness = min(int(len_sc                             * 25 * mult), 25),
        code_quality = min(int((0.5 + 0.5 * comments)            * 25 * mult), 25),
        edge_cases   = min(int((0.4 * coverage + 0.6 * edge_hit) * 25 * mult), 25),
    )
    strengths = (
        "Answer demonstrates relevant technical knowledge."
        if coverage > 0.5 else "Some technical content present; more depth needed."
    )
    improvements = (
        "Add edge-case handling, inline comments, and ensure full task coverage."
    )
    return result, strengths, improvements


# ---------------------------------------------------------------------------
# Skill-aware Evaluator Registry
# ---------------------------------------------------------------------------

class SkillEvaluator:
    _HINTS: dict[str, str] = {
        "python":  "Pay attention to Pythonic idioms, type hints, and exception handling.",
        "react":   "Check hook usage, prop handling, component composition, and re-render avoidance.",
        "sql":     "Verify SQL correctness, join types, aggregation, and index-friendly patterns.",
        "ml":      "Assess mathematical correctness, awareness of pitfalls, and practical reasoning.",
        "fastapi": "Check Pydantic models, dependency injection, HTTP semantics, and schema design.",
    }
    _DEFAULT = "Evaluate for correctness, completeness, code clarity, and best practices."

    def hint(self, skill: str) -> str:
        return self._HINTS.get(skill.lower().strip(), self._DEFAULT)


_skill_evaluator = SkillEvaluator()


# ---------------------------------------------------------------------------
# Main Evaluation Function
# ---------------------------------------------------------------------------

def evaluate_answer(task: Task, answer: str) -> dict[str, Any]:
    """
    Evaluate a candidate's answer.
    1. Guard  : empty answer → zero score immediately.
    2. Primary: Azure OpenAI LLM evaluation.
    3. Fallback: rule-based heuristic (zero API dependency).
    Always returns the full 9-key schema. Never raises.
    """
    if not answer or not answer.strip():
        log.warning("Empty answer — returning zero score.")
        return EvalResult().to_dict(
            strengths    = "No answer was provided.",
            improvements = "Submit a complete answer addressing the task.",
        )

    system = _EVAL_SYSTEM + f"\n\nSkill guidance: {_skill_evaluator.hint(task.skill)}"
    raw    = _llm.complete(system, _eval_user_prompt(task, answer))

    if raw:
        parsed = _parse_llm_eval(raw)
        if parsed:
            result = EvalResult(
                correctness  = max(0, min(int(parsed.get("correctness",  0)), 25)),
                completeness = max(0, min(int(parsed.get("completeness", 0)), 25)),
                code_quality = max(0, min(int(parsed.get("code_quality", 0)), 25)),
                edge_cases   = max(0, min(int(parsed.get("edge_cases",  0)), 25)),
            )
            log.info("Evaluation completed via Azure OpenAI.")
            return result.to_dict(
                strengths    = str(parsed.get("strengths",    "")).strip(),
                improvements = str(parsed.get("improvements", "")).strip(),
            )
        log.warning("LLM returned unparseable response — using rule-based fallback.")

    log.info("Using rule-based fallback evaluator.")
    result, strengths, improvements = _rule_based_score(task, answer)
    return result.to_dict(strengths=strengths, improvements=improvements)


# ---------------------------------------------------------------------------
# Public Agent Entry Point
# ---------------------------------------------------------------------------

def run_agent(
    skill:         str,
    claimed_level: str,
    evidence:      float,
    answer:        str | None = None,
) -> dict[str, Any]:
    """
    Full SkillTrust pipeline.

    Parameters
    ----------
    skill          : "python" | "react" | "sql" | "ml" | "fastapi"
    claimed_level  : "beginner" | "intermediate" | "advanced"
    evidence       : 0.0–1.0 evidence score from prior agent
    answer         : candidate's answer (None = task-only mode)

    Returns
    -------
    dict — always contains: calibrated_level, task_description, task_source
           + full eval schema when answer is provided
    """
    calibrated = calibrate_level(claimed_level, evidence)
    task       = generate_task(skill, calibrated)

    output: dict[str, Any] = {
        "calibrated_level": calibrated.value,
        "task_description": task.description,
        "task_source":      task.source,
    }

    if answer is not None:
        output.update(evaluate_answer(task, answer))

    return output


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 64)
    print("  SkillTrust Agent — CLI Smoke Test")
    print("=" * 64)

    # Print current Azure config status
    status = _llm.status()
    print(f"\n  Configured : {status['configured']}")
    print(f"  Endpoint   : {status['endpoint']}")
    print(f"  Deployment : {status['deployment']}")
    print(f"  API Version: {status['api_version']}")
    print()

    sample_answer = (
        "def merge_sorted_lists(a: list[int], b: list[int]) -> list[int]:\n"
        "    \"\"\"Merge two sorted lists in O(n+m).\"\"\"\n"
        "    result, i, j = [], 0, 0\n"
        "    while i < len(a) and j < len(b):\n"
        "        if a[i] <= b[j]:\n"
        "            result.append(a[i]); i += 1\n"
        "        else:\n"
        "            result.append(b[j]); j += 1\n"
        "    return result + a[i:] + b[j:]  # handles remaining\n\n"
        "# Edge cases\n"
        "assert merge_sorted_lists([], []) == []\n"
        "assert merge_sorted_lists([], [1, 2]) == [1, 2]\n"
        "assert merge_sorted_lists([1, 3], [2, 4]) == [1, 2, 3, 4]\n"
    )

    result = run_agent(
        skill         = "python",
        claimed_level = "intermediate",
        evidence      = 0.6,
        answer        = sample_answer,
    )
    print(json.dumps(result, indent=2))
