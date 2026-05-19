import json

from profile_agent import run_profile_agent
from evidence_agent import run_evidence_agent
from skill_testing_agent import run_agent, TASK_BANK


def _resume_payload(user_input: dict) -> dict:

    return {
        "resume_text": user_input.get("resume_text")
        or user_input.get("resume", ""),
    }


def _skill_for_agent(label: str) -> str:

    s = (label or "").strip().lower()

    if s in TASK_BANK:

        return s

    if "sql" in s:

        return "sql"

    if "machine" in s or "tensorflow" in s or "pytorch" in s or s == "ml":

        return "ml"

    if "react" in s or "next" in s:

        return "react"

    if "fastapi" in s:

        return "fastapi"

    if "python" in s or "django" in s or "flask" in s:

        return "python"

    return "python"


def orchestrate(user_input):

    print("\n========== STARTED ORCHESTRATION ==========\n")

    resume_payload = _resume_payload(user_input)

    try:

        # ==============================
        # PROFILE AGENT
        # ==============================

        print("CALLING PROFILE AGENT...")

        profile_data = run_profile_agent(
            resume_payload["resume_text"]
        ).model_dump()

        print("PROFILE DONE")

        print(json.dumps(
            profile_data,
            indent=2
        ))

        # ==============================
        # EVIDENCE AGENT
        # ==============================

        print("\nCALLING EVIDENCE AGENT...")

        try:

            evidence_data = run_evidence_agent(
                resume_payload["resume_text"]
            )

        except Exception as ev_err:

            print("\nEVIDENCE AGENT FAILED:", ev_err)

            evidence_data = {
                "github_links": [],
                "linkedin_links": [],
                "project_snippets": [],
                "aggregated_skill_scores": {},
                "repositories": [],
                "error": str(ev_err),
            }

        print("EVIDENCE DONE")

        print(json.dumps(
            evidence_data,
            indent=2
        ))

        # ==============================
        # AUTHENTICITY LOGIC
        # ==============================

        print("\nRUNNING AUTHENTICITY CHECK...")

        claimed_skills = profile_data.get(
            "skills",
            []
        )

        evidence_skills = evidence_data.get(
            "aggregated_skill_scores",
            {}
        )

        fraud_risk = 0

        missing_skills = []

        for skill in claimed_skills:

            if skill not in evidence_skills:

                fraud_risk += 0.2

                missing_skills.append(skill)

        authenticity_score = max(
            0,
            1 - fraud_risk
        )

        fraud_flag = fraud_risk > 0.3

        if authenticity_score > 0.8:

            trust_level = "High"

        elif authenticity_score > 0.5:

            trust_level = "Medium"

        else:

            trust_level = "Low"

        authenticity_data = {
            "authenticity_score": round(
                authenticity_score,
                2
            ),
            "fraud_flag": fraud_flag,
            "missing_skills": missing_skills,
            "trust_level": trust_level,
        }

        print("AUTHENTICITY DONE")

        print(json.dumps(
            authenticity_data,
            indent=2
        ))

        # ==============================
        # SKILL TESTING
        # ==============================

        skill_results = []

        for skill in profile_data.get("skills", [])[:12]:

            try:

                evidence_score = evidence_data.get(
                    "aggregated_skill_scores",
                    {},
                ).get(skill, 0.5)

                print(f"RUNNING SKILL TEST FOR {skill}")

                result = run_agent(
                    skill=_skill_for_agent(skill),
                    claimed_level="intermediate",
                    evidence=evidence_score,
                    answer="sample answer for demo",
                )

                skill_results.append({skill: result})

            except Exception as se:

                print(f"SKILL TEST FAILED FOR {skill}:", se)

                skill_results.append({
                    skill: {
                        "status": "error",
                        "error": str(se),
                    }
                })

        print("\nSKILL TESTING COMPLETE")

        print(json.dumps(
            skill_results,
            indent=2
        ))

        # ==============================
        # FINAL REPORT
        # ==============================

        final_report = {
            "success": True,
            "profile": profile_data,
            "evidence": evidence_data,
            "authenticity": authenticity_data,
            "skill_testing": skill_results,
        }

        print("\n========== FINAL REPORT ==========\n")

        print(json.dumps(
            final_report,
            indent=2
        ))

        return final_report

    except Exception as e:

        print("\nERROR IN ORCHESTRATOR:")

        print(str(e))

        return {
            "success": False,
            "error": str(e),
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

    print(json.dumps(
        result,
        indent=2
    ))
