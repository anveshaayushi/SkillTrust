import json

import requests

from skill_testing_agent import run_agent

# Start the API first: uvicorn auth_api:app --reload
BASE_URL = "http://127.0.0.1:8000"


def _resume_payload(user_input: dict) -> dict:
    return {
        "resume_text": user_input.get("resume_text") or user_input.get("resume", ""),
    }


def orchestrate(user_input):
    resume_payload = _resume_payload(user_input)

    profile_response = requests.post(
        f"{BASE_URL}/profile",
        json=resume_payload,
    )
    profile_response.raise_for_status()
    profile_data = profile_response.json()

    print("\nPROFILE AGENT OUTPUT:")
    print(json.dumps(profile_data, indent=2))

    evidence_response = requests.post(
        f"{BASE_URL}/evidence",
        json=resume_payload,
    )
    evidence_response.raise_for_status()
    evidence_data = evidence_response.json()

    print("\nEVIDENCE AGENT OUTPUT:")
    print(json.dumps(evidence_data, indent=2))

    authenticity_response = requests.post(
        f"{BASE_URL}/authenticity",
        json={
            "profile": profile_data,
            "evidence": evidence_data,
        },
    )
    authenticity_response.raise_for_status()
    authenticity_data = authenticity_response.json()

    print("\nAUTHENTICITY OUTPUT:")
    print(json.dumps(authenticity_data, indent=2))

    skill_results = []
    for skill in profile_data.get("skills", []):
        evidence_score = evidence_data.get("aggregated_skill_scores", {}).get(skill, 0.5)
        result = run_agent(
            skill=skill,
            claimed_level="intermediate",
            evidence=evidence_score,
            answer="sample answer for demo",
        )
        skill_results.append({skill: result})

    print("\nSKILL TESTING OUTPUT:")
    print(json.dumps(skill_results, indent=2))

    final_report = {
        "profile": profile_data,
        "evidence": evidence_data,
        "authenticity": authenticity_data,
        "skill_testing": skill_results,
    }

    return final_report


if __name__ == "__main__":
    sample_input = {
        "resume": (
            "Jane Doe\n"
            "Skills: React, FastAPI, Python\n"
            "GitHub: https://github.com/owner/repo\n"
        ),
    }

    result = orchestrate(sample_input)

    print("\nFINAL REPORT:")
    print(json.dumps(result, indent=2))
