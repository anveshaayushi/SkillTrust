import json
import os
import requests

# Start API:
# uvicorn auth_api:app --reload

BASE_URL = "http://127.0.0.1:8000"


# ==========================================
# FINAL LOCKED INPUT SCHEMA
# ==========================================

sample_input = {
    "candidate": "Jane Doe",
    "resume_text": "",
    "linkedin_text": "",
    "github_links": [],
    "code_samples": [],
    "resume_path": None,
}


# ==========================================
# FINAL LOCKED OUTPUT SCHEMA
# ==========================================

def build_final_report(
    candidate="",
    trust_score=None,
    risk_level="UNKNOWN",
    verified_skills=None,
    missing_skills=None,
    flags=None,
    recommendation="",
):
    return {
        "candidate": candidate,
        "trust_score": trust_score,
        "risk_level": risk_level,
        "verified_skills": verified_skills or [],
        "missing_skills": missing_skills or [],
        "flags": flags or [],
        "recommendation": recommendation,
    }


# ==========================================
# SHARED RESUME POST HELPER
# ==========================================

def _post_resume(endpoint: str, user_input: dict):

    resume_path = user_input.get("resume_path")

    # -----------------------------
    # FILE UPLOAD FLOW
    # -----------------------------

    if resume_path:

        with open(resume_path, "rb") as resume_file:

            files = {
                "resume": (
                    os.path.basename(resume_path),
                    resume_file,
                )
            }

            return requests.post(
                f"{BASE_URL}{endpoint}",
                files=files,
            )

    # -----------------------------
    # TEXT INPUT FLOW
    # -----------------------------

    payload = {
        "resume_text": user_input.get(
            "resume_text",
            ""
        ),

        "linkedin_text": user_input.get(
            "linkedin_text",
            ""
        ),

        "github_links": user_input.get(
            "github_links",
            []
        ),

        "code_samples": user_input.get(
            "code_samples",
            []
        ),
    }

    return requests.post(
        f"{BASE_URL}{endpoint}",
        json=payload,
    )


# ==========================================
# MAIN ORCHESTRATOR
# ==========================================

def orchestrate(user_input):

    try:

        # ======================================
        # PROFILE AGENT
        # ======================================

        profile_response = _post_resume(
            "/profile",
            user_input
        )

        profile_response.raise_for_status()

        profile_data = profile_response.json()

        print("\nPROFILE AGENT OUTPUT:")
        print(json.dumps(profile_data, indent=2))

        # ======================================
        # EVIDENCE AGENT
        # ======================================

        evidence_response = _post_resume(
            "/evidence",
            user_input
        )

        evidence_response.raise_for_status()

        evidence_data = evidence_response.json()

        print("\nEVIDENCE AGENT OUTPUT:")
        print(json.dumps(evidence_data, indent=2))

        # ======================================
        # AUTHENTICITY AGENT
        # ======================================

        authenticity_response = requests.post(
            f"{BASE_URL}/authenticity",

            json={

                "profile": profile_data,

                "evidence": evidence_data,

                "code": user_input.get(
                    "code_samples",
                    [""]
                )[0]
            },
        )

        authenticity_response.raise_for_status()

        authenticity_data = authenticity_response.json()

        print("\nAUTHENTICITY OUTPUT:")
        print(json.dumps(authenticity_data, indent=2))

        # ======================================
        # VERIFIED SKILLS
        # ======================================

        verified_skills = list(

            evidence_data.get(
                "aggregated_skill_scores",
                {}
            ).keys()
        )

        # ======================================
        # MISSING SKILLS
        # ======================================

        missing_skills = authenticity_data.get(
            "missing_skills",
            []
        )

        # ======================================
        # FLAGS
        # ======================================

        evidence_flags = evidence_data.get(
            "flags",
            []
        )

        authenticity_flags = authenticity_data.get(
            "flags",
            []
        )

        all_flags = (
            evidence_flags +
            authenticity_flags
        )

        # ======================================
        # FINAL REPORT
        # ======================================

        final_report = build_final_report(

            candidate=user_input.get(
                "candidate",
                "Unknown Candidate"
            ),

            trust_score=authenticity_data.get(
                "trust_score",
                None,
            ),

            risk_level=authenticity_data.get(
                "risk_level",
                "UNKNOWN",
            ),

            verified_skills=verified_skills,

            missing_skills=missing_skills,

            flags=all_flags,

            recommendation=authenticity_data.get(
                "recommendation",
                "Needs further review",
            ),
        )

        return final_report

    except Exception as e:

        print(f"\nPIPELINE ERROR: {e}")

        return {
            "error": str(e)
        }


# ==========================================
# LOCAL TEST
# ==========================================

if __name__ == "__main__":

    sample_input = {

        "candidate": "Jane Doe",

        "resume_text": (
            "Jane Doe\n"
            "Skills: React, FastAPI, Python\n"
            "GitHub: https://github.com/owner/repo\n"
        ),

        "linkedin_text": (
            "Software Engineer with React + FastAPI experience"
        ),

        "github_links": [
            "https://github.com/owner/repo"
        ],

        "code_samples": [
            "def hello(): return 'world'"
        ],

        "resume_path": None,
    }

    result = orchestrate(sample_input)

    print("\nFINAL REPORT:")
    print(json.dumps(result, indent=2))