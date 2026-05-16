import requests
import json

BASE_URL = "http://127.0.0.1:8000"


def orchestrate(user_input):

    # STEP 1 → Profile Agent
    profile_response = requests.post(
        f"{BASE_URL}/profile",
        json=user_input
    )

    profile_data = profile_response.json()

    print("\nPROFILE AGENT OUTPUT:")
    print(json.dumps(profile_data, indent=2))


    # STEP 2 → Evidence Agent
    evidence_response = requests.post(
        f"{BASE_URL}/evidence",
        json=profile_data
    )

    evidence_data = evidence_response.json()

    print("\nEVIDENCE AGENT OUTPUT:")
    print(json.dumps(evidence_data, indent=2))


    # STEP 3 → Authenticity Agent
    authenticity_response = requests.post(
        f"{BASE_URL}/authenticity",
        json={
            "profile": profile_data,
            "evidence": evidence_data
        }
    )

    authenticity_data = authenticity_response.json()

    print("\nAUTHENTICITY OUTPUT:")
    print(json.dumps(authenticity_data, indent=2))


    # FINAL REPORT
    final_report = {
        "profile": profile_data,
        "evidence": evidence_data,
        "authenticity": authenticity_data
    }

    return final_report
if __name__ == "__main__":

    sample_input = {
        "resume": "Sample resume",
        "github": "github.com/test"
    }

    result = orchestrate(sample_input)

    print("\nFINAL REPORT:")
    print(json.dumps(result, indent=2))    