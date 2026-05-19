import re
import requests
from collections import defaultdict


# =========================
# GITHUB LINK EXTRACTION
# =========================

def extract_github_links(text: str):

    pattern = r"https?://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"

    matches = re.findall(pattern, text)

    clean_links = []

    for link in matches:

        cleaned = link.rstrip(").,]}>")

        if cleaned not in clean_links:
            clean_links.append(cleaned)

    return clean_links


# =========================
# FETCH README
# =========================

def fetch_readme(owner: str, repo: str):

    url = f"https://api.github.com/repos/{owner}/{repo}/readme"

    headers = {
        "Accept": "application/vnd.github.raw"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        print(f"README STATUS ({repo}):", response.status_code)

        if response.status_code == 200:
            return response.text

        return ""

    except Exception as e:

        print("README ERROR:", e)

        return ""


# =========================
# FETCH REPO FILE TREE
# =========================

def fetch_repo_tree(owner: str, repo: str):

    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"

    try:

        response = requests.get(
            url,
            timeout=15
        )

        print(f"TREE STATUS ({repo}):", response.status_code)

        if response.status_code != 200:
            return []

        data = response.json()

        files = []

        for item in data.get("tree", []):

            path = item.get("path", "")

            files.append(path.lower())

        return files

    except Exception as e:

        print("TREE ERROR:", e)

        return []


# =========================
# TECH STACK DETECTION
# =========================

TECH_KEYWORDS = {
    "react": ["react", "jsx", "tsx"],
    "python": ["python", ".py", "fastapi", "flask", "django"],
    "fastapi": ["fastapi"],
    "docker": ["docker", "dockerfile"],
    "sql": ["sql", "postgres", "mysql", "sqlite"],
    "nodejs": ["node", "express", "package.json"],
    "mongodb": ["mongodb", "mongoose"],
    "tensorflow": ["tensorflow"],
    "pytorch": ["pytorch"],
    "java": [".java", "spring"],
}


# =========================
# DETECT SKILLS FROM REPO
# =========================

def detect_skills(readme: str, files: list):

    detected = defaultdict(float)

    combined_text = (
        readme.lower()
        + " "
        + " ".join(files)
    )

    for skill, keywords in TECH_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            if keyword in combined_text:
                score += 1

        if score > 0:

            confidence = min(
                round(score / len(keywords), 2),
                1.0
            )

            detected[skill] = confidence

    return dict(detected)


# =========================
# MAIN EVIDENCE AGENT
# =========================

def run_evidence_agent(resume_text: str):

    print("\n========== EVIDENCE AGENT ==========")

    github_links = extract_github_links(
        resume_text
    )

    print("\nEXTRACTED GITHUB LINKS:")
    print(github_links)

    projects = []

    aggregated_skill_scores = defaultdict(float)

    aggregated_flags = []

    # =====================
    # NO LINKS FOUND
    # =====================

    if not github_links:

        print("\nNO GITHUB LINKS FOUND")

        return {
            "projects": [],
            "aggregated_skill_scores": {},
            "aggregated_flags": [
                "No GitHub repositories detected"
            ]
        }

    # =====================
    # PROCESS EACH REPO
    # =====================

    for link in github_links:

        try:

            repo_path = link.replace(
                "https://github.com/",
                ""
            )

            owner, repo = repo_path.split("/")[:2]

            print(f"\nPROCESSING: {owner}/{repo}")

            readme = fetch_readme(
                owner,
                repo
            )

            files = fetch_repo_tree(
                owner,
                repo
            )

            detected_skills = detect_skills(
                readme,
                files
            )

            print("DETECTED SKILLS:")
            print(detected_skills)

            # aggregate scores

            for skill, score in detected_skills.items():

                aggregated_skill_scores[skill] = max(
                    aggregated_skill_scores[skill],
                    score
                )

            # repo score

            if detected_skills:
                repo_score = round(
                    sum(detected_skills.values())
                    / len(detected_skills),
                    2
                )
            else:
                repo_score = 0.0

            projects.append({
                "repo": f"{owner}/{repo}",
                "repo_url": link,
                "detected_skills": detected_skills,
                "project_score": repo_score,
                "repo_quality":
                    "good"
                    if repo_score >= 0.5
                    else "weak"
            })

        except Exception as e:

            print("REPO PROCESS ERROR:", e)

            aggregated_flags.append(
                f"Failed processing {link}"
            )

    # =====================
    # FINAL OUTPUT
    # =====================

    final_scores = {
        k: round(v, 2)
        for k, v in aggregated_skill_scores.items()
    }

    print("\nFINAL AGGREGATED SCORES:")
    print(final_scores)

    return {
        "projects": projects,
        "aggregated_skill_scores": final_scores,
        "aggregated_flags": aggregated_flags,
    }