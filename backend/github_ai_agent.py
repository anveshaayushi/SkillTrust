"""
github_ai_agent.py
==================
Agent 6 — GitHub AI-Authorship Detection

Fetches a candidate's GitHub repositories and analyses the code for
signals of AI-generated content (ChatGPT / Copilot style patterns).

Detection heuristics (no external API needed — pure static analysis):
  1. Boilerplate density   — ultra-clean scaffold code, uniform docstrings
  2. Comment-to-code ratio — AI tends to over-comment
  3. Variable naming       — suspiciously perfect snake_case everywhere
  4. Error handling style  — `try/except Exception as e: print(e)` pattern
  5. Structural uniformity — identical file shapes across a repo
  6. Commit pattern        — single-commit repos are a red flag
  7. README quality        — AI-generated READMEs are over-structured

If Azure OpenAI is available, it also runs an LLM semantic check on
a sample of code.  Falls back gracefully to heuristics-only.

Returns
-------
{
    "github_urls": [...],
    "repos_analysed": int,
    "repo_results": [
        {
            "repo": "owner/name",
            "url": "https://github.com/...",
            "ai_probability": 0.0–1.0,
            "verdict": "Likely Human" | "Possibly AI" | "Likely AI",
            "signals": ["signal1", ...],
            "commits": int,
            "primary_language": str,
        }
    ],
    "overall_ai_probability": 0.0–1.0,
    "overall_verdict": str,
    "agent": "github_ai_agent",
}
"""

from __future__ import annotations

import re
import json
import logging
import os
from typing import Any

import requests

log = logging.getLogger("SkillTrust.GitHubAI")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# ── GitHub API helpers ────────────────────────────────────────────────────────

def _gh(url: str, params: dict | None = None) -> Any:
    """GET a GitHub API URL, return parsed JSON or None."""
    try:
        r = requests.get(
            url, headers={**HEADERS, "Accept": "application/vnd.github.v3+json"},
            params=params, timeout=8
        )
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        log.warning("GitHub request failed: %s", e)
    return None


def _extract_github_urls(text: str) -> list[str]:
    """Pull github.com/user/repo URLs from resume text."""
    pattern = r"github\.com/([a-zA-Z0-9_\-]+(?:/[a-zA-Z0-9_\-\.]+)?)"
    matches = re.findall(pattern, text or "")
    seen = set()
    urls = []
    for m in matches:
        parts = m.strip("/").split("/")
        if len(parts) >= 1:
            url = f"https://github.com/{'/'.join(parts[:2])}"
            if url not in seen:
                seen.add(url)
                urls.append(url)
    return urls[:5]


def _get_user_repos(username: str) -> list[dict]:
    data = _gh(f"https://api.github.com/users/{username}/repos",
               {"per_page": 10, "sort": "updated"})
    return data if isinstance(data, list) else []


def _get_repo_commits(owner: str, repo: str) -> int:
    data = _gh(f"https://api.github.com/repos/{owner}/{repo}/commits",
               {"per_page": 1})
    if isinstance(data, list):
        return len(data)
    # GitHub returns pagination link header with total for large repos
    return 1


def _get_repo_files(owner: str, repo: str) -> list[dict]:
    data = _gh(f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD",
               {"recursive": "1"})
    if data and "tree" in data:
        return [f for f in data["tree"] if f.get("type") == "blob"]
    return []


def _fetch_file_content(owner: str, repo: str, path: str) -> str:
    """Fetch raw file content. Returns empty string on failure."""
    try:
        r = requests.get(
            f"https://raw.githubusercontent.com/{owner}/{repo}/HEAD/{path}",
            headers=HEADERS, timeout=6
        )
        if r.status_code == 200:
            return r.text[:4000]  # Cap at 4KB per file
    except Exception:
        pass
    return ""


# ── Heuristic detectors ───────────────────────────────────────────────────────

def _heuristic_score(code_samples: list[str], commit_count: int,
                     file_count: int, readme: str) -> tuple[float, list[str]]:
    """
    Returns (probability 0.0–1.0, list of signal strings).
    Each positive signal adds to the probability.
    """
    signals: list[str] = []
    score = 0.0

    combined = "\n".join(code_samples)
    lines = [l for l in combined.split("\n") if l.strip()]
    total_lines = len(lines) or 1

    # 1. Single-commit repo
    if commit_count <= 1:
        signals.append("Single-commit repo — likely uploaded all at once")
        score += 0.25

    # 2. Over-commented code (AI loves explaining everything)
    comment_lines = sum(1 for l in lines if l.strip().startswith(("#", "//", "/*", "*", '"""', "'''")))
    comment_ratio = comment_lines / total_lines
    if comment_ratio > 0.35:
        signals.append(f"Unusually high comment density ({comment_ratio:.0%})")
        score += 0.15

    # 3. Boilerplate docstrings — "This function/class/method ..." pattern
    boilerplate_hits = len(re.findall(
        r'"""(This (function|class|method|script|module)|Args:|Returns:|Raises:)',
        combined, re.IGNORECASE
    ))
    if boilerplate_hits > 2:
        signals.append(f"Boilerplate docstrings detected ({boilerplate_hits} hits)")
        score += 0.20

    # 4. Lazy exception handling — AI signature
    lazy_except = len(re.findall(r"except\s+Exception\s+as\s+e\s*:\s*\n\s*(print|pass|log)", combined))
    if lazy_except > 1:
        signals.append(f"AI-style exception handling pattern ({lazy_except}× found)")
        score += 0.10

    # 5. Over-structured README (AI loves badge-filled READMEs)
    if readme:
        headers = len(re.findall(r"^#{1,3}\s", readme, re.MULTILINE))
        if headers > 8:
            signals.append(f"README has {headers} sections — over-structured for project size")
            score += 0.10

    # 6. Suspiciously perfect naming (all vars are descriptive_snake_case)
    long_vars = re.findall(r"\b([a-z][a-z_]{8,}[a-z])\s*=", combined)
    if len(long_vars) > 15:
        signals.append("Suspiciously verbose/uniform variable naming")
        score += 0.10

    # 7. Very few files for a "complete" project
    if file_count > 0 and file_count < 4 and commit_count <= 2:
        signals.append("Minimal file structure with few commits")
        score += 0.10

    # 8. Type hints everywhere with perfect consistency (Copilot pattern)
    type_hints = len(re.findall(r"def \w+\([^)]*:\s*\w+", combined))
    if type_hints > 5 and commit_count <= 3:
        signals.append("Perfect type hint coverage in a low-commit repo")
        score += 0.05

    return min(score, 1.0), signals


# ── LLM check (Azure OpenAI — optional) ──────────────────────────────────────

def _llm_ai_check(code_sample: str) -> dict | None:
    """
    Ask the LLM to estimate AI-authorship probability.
    Returns dict with 'probability' and 'reasoning', or None on failure.
    """
    try:
        import openai
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
        api_key  = os.environ.get("AZURE_OPENAI_API_KEY", "")
        deploy   = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

        if not endpoint or not api_key:
            return None

        client = openai.AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview",
        )

        prompt = f"""Analyse the following code and estimate the probability (0.0–1.0) that it was 
written by an AI tool (ChatGPT, GitHub Copilot, etc.) rather than a human developer.
Consider: over-perfect structure, boilerplate comments, uniform style, lack of personal quirks.

Respond ONLY as JSON: {{"probability": 0.0, "reasoning": "one sentence"}}

CODE:
{code_sample[:2000]}"""

        resp = client.chat.completions.create(
            model=deploy,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0,
        )

        raw  = resp.choices[0].message.content.strip()
        data = json.loads(raw.strip("```json").strip("```").strip())
        return {
            "probability": float(data.get("probability", 0)),
            "reasoning":   str(data.get("reasoning", "")),
        }

    except Exception as e:
        log.debug("LLM AI check failed (non-critical): %s", e)
        return None


# ── Per-repo analysis ─────────────────────────────────────────────────────────

def _analyse_repo(owner: str, repo_name: str, repo_url: str) -> dict:
    log.info("Analysing repo: %s/%s", owner, repo_name)

    files    = _get_repo_files(owner, repo_name)
    commits  = _get_repo_commits(owner, repo_name)

    code_ext = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs", ".cpp", ".cs"}
    code_files = [
        f["path"] for f in files
        if any(f["path"].endswith(e) for e in code_ext)
    ][:6]  # analyse at most 6 files

    readme_files = [
        f["path"] for f in files
        if f["path"].lower().startswith("readme")
    ]

    code_samples = [_fetch_file_content(owner, repo_name, p) for p in code_files]
    readme       = _fetch_file_content(owner, repo_name, readme_files[0]) if readme_files else ""

    primary_language = "Unknown"
    repo_meta = _gh(f"https://api.github.com/repos/{owner}/{repo_name}")
    if repo_meta:
        primary_language = repo_meta.get("language") or "Unknown"

    # Heuristic score
    h_prob, signals = _heuristic_score(
        code_samples, commits, len(files), readme
    )

    # Optional LLM boost
    llm_result = None
    if code_samples:
        llm_result = _llm_ai_check("\n\n".join(code_samples[:2]))

    # Final probability: blend heuristics + LLM (if available)
    if llm_result:
        final_prob = round(0.5 * h_prob + 0.5 * llm_result["probability"], 2)
        signals.append(f"LLM analysis: {llm_result['reasoning']}")
    else:
        final_prob = round(h_prob, 2)

    verdict = (
        "Likely AI"    if final_prob >= 0.60 else
        "Possibly AI"  if final_prob >= 0.35 else
        "Likely Human"
    )

    return {
        "repo":             f"{owner}/{repo_name}",
        "url":              repo_url,
        "ai_probability":   final_prob,
        "verdict":          verdict,
        "signals":          signals,
        "commits":          commits,
        "primary_language": primary_language,
        "files_analysed":   len(code_files),
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def run_github_ai_agent(resume_text: str) -> dict:
    """
    Extract GitHub URLs from resume text, analyse each repo,
    return a structured result dict.
    """
    log.info("GitHub AI Agent starting")

    github_urls = _extract_github_urls(resume_text)

    if not github_urls:
        return {
            "github_urls":           [],
            "repos_analysed":        0,
            "repo_results":          [],
            "overall_ai_probability": 0.0,
            "overall_verdict":       "No GitHub links found",
            "agent":                 "github_ai_agent",
        }

    repo_results: list[dict] = []

    for url in github_urls:
        path  = url.replace("https://github.com/", "").strip("/")
        parts = path.split("/")

        if len(parts) == 1:
            # Profile URL — fetch their repos
            repos = _get_user_repos(parts[0])
            for r in repos[:3]:
                try:
                    result = _analyse_repo(parts[0], r["name"], r["html_url"])
                    repo_results.append(result)
                except Exception as e:
                    log.warning("Failed to analyse repo %s: %s", r.get("name"), e)
        elif len(parts) == 2:
            # Direct repo URL
            try:
                result = _analyse_repo(parts[0], parts[1], url)
                repo_results.append(result)
            except Exception as e:
                log.warning("Failed to analyse repo %s/%s: %s", parts[0], parts[1], e)

    if not repo_results:
        return {
            "github_urls":           github_urls,
            "repos_analysed":        0,
            "repo_results":          [],
            "overall_ai_probability": 0.0,
            "overall_verdict":       "Could not access repositories",
            "agent":                 "github_ai_agent",
        }

    overall_prob = round(
        sum(r["ai_probability"] for r in repo_results) / len(repo_results), 2
    )

    overall_verdict = (
        "Likely AI-Generated"  if overall_prob >= 0.60 else
        "Possibly AI-Assisted" if overall_prob >= 0.35 else
        "Likely Human-Written"
    )

    return {
        "github_urls":            github_urls,
        "repos_analysed":         len(repo_results),
        "repo_results":           repo_results,
        "overall_ai_probability": overall_prob,
        "overall_verdict":        overall_verdict,
        "agent":                  "github_ai_agent",
    }
