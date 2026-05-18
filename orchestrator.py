import json
import os

import requests

# Start the API first: uvicorn auth_api:app --reload
BASE_URL = "http://127.0.0.1:8000"


def _post_resume(endpoint: str, user_input: dict):
    resume_path = user_input.get("resume_path")

    if resume_path:
        with open(resume_path, "rb") as resume_file:
            files = {"resume": (os.path.basename(resume_path), resume_file)}
            return requests.post(f"{BASE_URL}{endpoint}", files=files)

    resume_text = user_input.get("resume_text") or user_input.get("resume", "")
    return requests.post(
        f"{BASE_URL}{endpoint}",
        json={"resume_text": resume_text},
    )


def orchestrate(user_input):
    profile_response = _post_resume("/profile", user_input)
    profile_response.raise_for_status()
    profile_data = profile_response.json()

    print("\nPROFILE AGENT OUTPUT:")
    print(json.dumps(profile_data, indent=2))

    evidence_response = _post_resume("/evidence", user_input)
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

    return {
        "profile": profile_data,
        "evidence": evidence_data,
        "authenticity": authenticity_data,
    }


if __name__ == "__main__":
    sample_input = {
        "resume_text": (
            "Jane Doe\n"
            "Skills: React, FastAPI, Python\n"
            "GitHub: https://github.com/owner/repo\n"
        ),
    }

    result = orchestrate(sample_input)

    print("\nFINAL REPORT:")
    print(json.dumps(result, indent=2))
