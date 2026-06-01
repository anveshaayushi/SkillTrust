import re
import requests
from collections import defaultdict


# ========================================
# GITHUB LINK EXTRACTION
# ========================================

def extract_github_links(text):

    """
    Collect GitHub profile and repo URLs:
    - https://github.com/user/repo
    - www.github.com/...
    - github.com/... without scheme
    """

    if not text:

        return []

    seen = set()

    patterns = [

        r"https?://(?:www\.)?github\.com/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?/?",

        r"(?<![\w/])github\.com/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?/?",

    ]

    for pattern in patterns:

        for match in re.finditer(pattern, text, re.IGNORECASE):

            raw = match.group(0).strip()

            raw = raw.rstrip(").,;]>'\"")

            if not raw.startswith("http"):

                raw = "https://" + raw.lstrip("/")

            raw = re.sub(
                r"^https?://www\.github\.com/",
                "https://github.com/",
                raw,
                flags=re.I,
            )

            raw = raw.rstrip("/")

            if "github.com/" in raw.lower():

                seen.add(raw)

    return list(seen)


# ========================================
# LINKEDIN LINK EXTRACTION
# ========================================

def extract_linkedin_links(text):

    if not text:

        return []

    seen = set()

    pattern = (
        r"https?://(?:[\w-]+\.)?linkedin\.com/"
        r"(?:in|pub)/[A-Za-z0-9_-]+/?"
    )

    for match in re.finditer(pattern, text, re.IGNORECASE):

        url = match.group(0).strip().rstrip("/)\"'")

        seen.add(url)

    return list(seen)


# ========================================
# PROJECT / TECH SNIPPETS (resume body)
# ========================================

def extract_project_snippets(text, max_snippets=8):

    """
    Pull bullet lines after common project/experience headers
    to capture technologies near project descriptions.
    """

    if not text:

        return []

    lines = [ln.rstrip() for ln in text.splitlines()]

    bullets = []

    header_re = re.compile(

        r"(?i)^(projects?|project experience|"
        r"selected work|portfolio|relevant experience|"
        r"professional experience|work experience)\s*:?\s*$"

    )

    for i, line in enumerate(lines):

        if header_re.match(line.strip()):

            for j in range(i + 1, min(i + 25, len(lines))):

                ln = lines[j].strip()

                if not ln:

                    continue

                if ln.startswith(("-", "•", "*", "·")) or re.match(r"^\d+[\).\s]", ln):

                    bullets.append(ln[:400])

                    if len(bullets) >= max_snippets:

                        break

            if bullets:

                break

    return bullets[:max_snippets]


def skills_from_resume_context(resume_text, snippets):

    """
    Lightweight keyword scan over full resume + project bullets
    (complements GitHub repo analysis).
    """

    block = (resume_text or "") + "\n" + "\n".join(snippets or [])

    block_lower = block.lower()

    scores = defaultdict(float)

    for skill, keywords in SKILL_KEYWORDS.items():

        for keyword in keywords:

            if keyword.lower() in block_lower:

                scores[skill] = max(scores[skill], 0.35)

                break

    return dict(scores)


# ========================================
# SKILL KEYWORDS
# ========================================

SKILL_KEYWORDS = {
    "React": ["react", "nextjs", "next.js"],
    "Python": ["python", "fastapi", "flask", "django"],
    "JavaScript": ["javascript", "js", "node"],
    "TypeScript": ["typescript", "ts"],
    "SQL": ["sql", "postgres", "mysql", "sqlite"],
    "Machine Learning": ["tensorflow", "pytorch", "sklearn"],
    "FastAPI": ["fastapi"],
}


# ========================================
# GITHUB USERNAME EXTRACTION
# ========================================

def extract_username(github_url):

    cleaned = github_url.strip().rstrip("/")

    cleaned = re.sub(

        r"^https?://(www\.)?github\.com/",

        "",

        cleaned,

        flags=re.IGNORECASE,

    )

    cleaned = cleaned.strip("/")

    username = cleaned.split("/")[0]

    return username


# ========================================
# FETCH USER REPOS
# ========================================

def fetch_repositories(username):

    try:

        url = f"https://api.github.com/users/{username}/repos"

        response = requests.get(
            url,
            timeout=15
        )

        if response.status_code != 200:

            print(
                f"GitHub API failed for {username}"
            )

            return []

        repos = response.json()

        return repos

    except Exception as e:

        print(
            "ERROR FETCHING REPOS:"
        )

        print(str(e))

        return []


# ========================================
# ANALYZE REPOS
# ========================================

def analyze_repositories(repos):

    skill_scores = defaultdict(float)

    repo_summaries = []

    for repo in repos:

        name = (
            repo.get("name", "")
            or ""
        ).lower()

        description = (
            repo.get("description", "")
            or ""
        ).lower()

        combined_text = (
            name + " " + description
        )

        matched_skills = []

        for skill, keywords in SKILL_KEYWORDS.items():

            for keyword in keywords:

                if keyword.lower() in combined_text:

                    skill_scores[skill] += 1

                    matched_skills.append(skill)

                    break

        repo_summaries.append({

            "repo_name":
                repo.get("name"),

            "description":
                repo.get("description"),

            "stars":
                repo.get("stargazers_count"),

            "matched_skills":
                matched_skills,
        })

    return {
        "aggregated_skill_scores":
            dict(skill_scores),

        "repositories":
            repo_summaries,
    }


# ========================================
# MAIN EVIDENCE AGENT
# ========================================

def run_evidence_agent(resume_text):

    print(
        "\n========== EVIDENCE AGENT =========="
    )

    resume_text = resume_text or ""

    github_links = extract_github_links(
        resume_text
    )

    linkedin_links = extract_linkedin_links(
        resume_text
    )

    project_snippets = extract_project_snippets(
        resume_text
    )

    resume_skill_hints = skills_from_resume_context(
        resume_text,
        project_snippets,
    )

    print("\nEXTRACTED GITHUB LINKS:")
    print(github_links)

    print("\nEXTRACTED LINKEDIN LINKS:")
    print(linkedin_links)

    all_repositories = []

    aggregated_scores = defaultdict(float)

    for skill, score in resume_skill_hints.items():

        aggregated_scores[skill] += score

    for link in github_links:

        print(
            f"\nPROCESSING: {link}"
        )

        username = extract_username(
            link
        )

        print(
            f"USERNAME: {username}"
        )

        repos = fetch_repositories(
            username
        )

        print(
            f"REPOS FOUND: {len(repos)}"
        )

        analysis = analyze_repositories(
            repos
        )

        all_repositories.extend(
            analysis["repositories"]
        )

        for skill, score in analysis[
            "aggregated_skill_scores"
        ].items():

            aggregated_scores[
                skill
            ] += score

    final_result = {

        "github_links":
            github_links,

        "linkedin_links":
            linkedin_links,

        "project_snippets":
            project_snippets,

        "aggregated_skill_scores":
            dict(aggregated_scores),

        "repositories":
            all_repositories,
    }

    print(
        "\n========== EVIDENCE COMPLETE =========="
    )

    return final_result


# ========================================
# TEST
# ========================================

if __name__ == "__main__":

    sample_resume = """

    Jane Doe

    Skills:
    React, FastAPI, Python

    GitHub:
    https://github.com/vercel/next.js
    github.com/openai

    LinkedIn:
    https://www.linkedin.com/in/janedoe/

    Projects:
    - Built a FastAPI service with React dashboard

    """

    result = run_evidence_agent(
        sample_resume
    )

    import json

    print(
        json.dumps(
            result,
            indent=2
        )
    )
