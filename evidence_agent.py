import os
import re
import json
import base64
from xml.dom.minidom import Document

import pdfplumber
import requests
from typing import List, Dict
from dotenv import load_dotenv
from google import genai


load_dotenv()

# -------------------------------
# CONFIG
# -------------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
# -------------------------------
#Text extractor — stays exactly the same
#--------------------------------
def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        if not text.strip():
            raise ValueError("No text found in PDF")
        return text
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Only PDF or DOCX supported")

# Core agent — only this function changes
# -------------------------------
# Extract GitHub links
# -------------------------------
def extract_github_links(text: str) -> List[str]:
    pattern = r"(https?://)?(www\.)?github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
    matches = re.finditer(pattern, text)

    links = []
    for match in matches:
        url = match.group()
        if not url.startswith("http"):
            url = "https://" + url
        links.append(url.rstrip("/"))

    return list(set(links))


# -------------------------------
# Parse repo
# -------------------------------
def parse_repo(url: str):
    path = url.replace("https://github.com/", "").replace("http://github.com/", "")
    parts = path.strip("/").split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repo URL: {url}")
    return parts[0], parts[1]
# -------------------------------
# Fetch README
# -------------------------------
def fetch_readme(owner: str, repo: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/readme"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return ""

    data = res.json()
    return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")


# -------------------------------
# Fetch repo tree
# -------------------------------
def fetch_repo_tree(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    res = requests.get(url, headers=HEADERS)

    if res.status_code != 200:
        return []

    return res.json().get("tree", [])


IMPORTANT_EXTENSIONS = (".py", ".js", ".ts", ".jsx", ".tsx")


# -------------------------------
# Filter code files
# -------------------------------
def filter_code_files(tree):
    # Step 1: keep only important code files
    code_files = [
        file["path"]
        for file in tree
        if file["type"] == "blob"
        and file["path"].endswith(IMPORTANT_EXTENSIONS)
    ]

    # Step 2: remove low-signal directories
    EXCLUDE_DIRS = ["docs", "examples", "test", "tests", "node_modules"]

    filtered = [
        path for path in code_files
        if not any(ex in path.lower() for ex in EXCLUDE_DIRS)
    ]

    # Step 3: prioritize backend / core folders
    PRIORITY_KEYWORDS = ["app", "core", "src", "api", "fastapi"]

    prioritized = sorted(
        filtered,
        key=lambda x: any(k in x.lower() for k in PRIORITY_KEYWORDS),
        reverse=True
    )

    # Step 4: prefer Python files first
    py_files = [p for p in prioritized if p.endswith(".py")]
    other_files = [p for p in prioritized if not p.endswith(".py")]

    final_selection = py_files + other_files

    return final_selection[:5]

# -------------------------------
# Fetch code files
# -------------------------------
def fetch_code_files(owner, repo, paths):
    collected = ""

    for path in paths:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        res = requests.get(url, headers=HEADERS)

        if res.status_code == 200:
            data = res.json()
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            collected += f"\n\n--- {path} ---\n{content[:30000]}"

    return collected


# -------------------------------
# Fetch key files
# -------------------------------
def fetch_key_files(owner: str, repo: str) -> str:
    tree = fetch_repo_tree(owner, repo)

    if not tree:
        return ""

    paths = filter_code_files(tree)

    if not paths:
        return ""

    return fetch_code_files(owner, repo, paths)


# -------------------------------
# Extract skills (Gemini)
# -------------------------------
def extract_skills_llm(resume_text: str) -> List[str]:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    Extract ONLY technical skills from this resume.

    Rules:
    - Include programming languages, frameworks, tools
    - Ignore soft skills
    - Normalize names (e.g., "ML" → "Machine Learning")

    Return ONLY JSON:
    {{
      "skills": []
    }}

    Resume:
    {resume_text}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        return json.loads(raw)["skills"]
    except:
        return []


# -------------------------------
# Evaluate ONE skill (Gemini)
# -------------------------------
def evaluate_repo(skills: List[str], readme: str, code: str) -> Dict:
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
You are an expert software engineer evaluating a GitHub repository.

TASK:
For each skill below, determine how well it is actually implemented in the repository.

Skills:
{skills}

SCORING RULE:
0.0 → Not present
0.2 → Mention only
0.4 → Basic usage (import / setup)
0.6 → Functional usage
0.8 → Strong implementation
1.0 → Advanced / production-level usage

STRICT RULES:
- Do NOT assume skills exist
- Prefer lower scores if evidence is unclear
- Look ONLY at provided code + README

Return ONLY valid JSON:
{{
  "skills": {{
    "skill1": 0.0,
    "skill2": 0.0
  }},
  "flags": [
    {{
      "skill": "skill_name",
      "issue": "short reason if weak or missing"
    }}
  ]
}}

README:
{readme[:3000]}

CODE:
{code[:3000]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw = response.text.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"Error decoding JSON from LLM response: {raw}")
        return {"skills": {}, "flags": []}

# -------------------------------
# Compute summary fields
# -------------------------------
def compute_project_score(scores: Dict[str, float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores.values()) / len(scores), 2)


def compute_repo_quality(readme: str, code: str) -> str:
    if readme and code:
        return "good"
    elif readme or code:
        return "average"
    return "poor"


def compute_evidence_strength(scores: Dict[str, float]) -> str:
    if not scores:
        return "low"

    values = list(scores.values())
    high = sum(1 for v in values if v > 0.7)
    low = sum(1 for v in values if v < 0.4)

    if high >= len(values) / 2:
        return "high"
    elif low >= len(values) / 2:
        return "low"
    return "medium"
# -------------------------------
# Aggregate skill scores across projects
# -------------------------------

def aggregate_skill_scores(project_results: list) -> Dict[str, float]:
    all_scores = {}
    counts = {}
    for project in project_results:
        for skill, score in project["skills"].items():
            all_scores[skill] = all_scores.get(skill, 0) + score
            counts[skill] = counts.get(skill, 0) + 1
    return {skill: round(all_scores[skill] / counts[skill], 2) for skill in all_scores}

# Aggregate flags across projects

def aggregate_flags(project_results: list) -> List[str]:
    seen = set()
    flags = []

    for project in project_results:
        repo_name = project.get("repo", "unknown_repo")

        for flag in project.get("flags", []):
            msg = f"{flag['skill']} ({repo_name}): {flag['issue']}"

            if msg not in seen:
                seen.add(msg)
                flags.append(msg)

    return flags

# -------------------------------
# MAIN Evidence Agent
# -------------------------------
def run_evidence_agent(resume_text: str):
    github_links = extract_github_links(resume_text)
    skills = extract_skills_llm(resume_text)

    project_results = []

    for link in github_links:
        try:
            owner, repo = parse_repo(link)
        except ValueError as e:
            print(f"Error parsing repo URL '{link}': {e}")
            continue

        readme = fetch_readme(owner, repo)
        code = fetch_key_files(owner, repo)

        if not readme and not code:
            continue

        repo_scores = {}
        repo_flags = []
        try:
            result = evaluate_repo(skills, readme, code)
        except Exception as e:
            print(f"Error evaluating repo '{link}': {e}")
            continue

        repo_scores = result.get("skills", {})
        repo_flags = result.get("flags", [])

        project_results.append({
            "repo": f"{owner}/{repo}",
            "skills": repo_scores,
            "project_score": compute_project_score(repo_scores),
            "repo_quality": compute_repo_quality(readme, code),
            "evidence_strength": compute_evidence_strength(repo_scores),
            "flags": repo_flags
        })

    return {
        "projects": project_results,
        "aggregated_skill_scores": aggregate_skill_scores(project_results),
        "aggregated_flags": aggregate_flags(project_results)
    }
def evidence_agent(file_path: str):
    resume_text = extract_text(file_path)
    return run_evidence_agent(resume_text)


if __name__ == "__main__":
    fake_resume = """
    John Doe

    Projects:
    1. GPT Sandbox
    GitHub: https://github.com/shreyashankar/gpt3-sandbox

    2. Full Stack App
    GitHub: https://github.com/tiangolo/full-stack-fastapi-template

    Skills:
    FastAPI, React, Python, Machine Learning, SQL
    """

    result = run_evidence_agent(fake_resume)
    print(json.dumps(result, indent=2))