import uuid
from datetime import datetime

from backend.profile_agent import run_profile_agent
from backend.evidence_agent import run_evidence_agent
from backend.skill_testing_agent import run_agent, TASK_BANK
from backend.github_ai_agent import run_github_ai_agent

WEAK_EVIDENCE_THRESHOLD = 0.5

CANDIDATE_DB: list[dict] = []


def _resume_payload(user_input: dict) -> dict:
    return {
        "resume_text": user_input.get("resume_text") or user_input.get("resume", ""),
    }


def _skill_for_agent(label: str) -> str:
    s = (label or "").strip().lower()
    if s in TASK_BANK:
        return s
    if "sql" in s:                                                    return "sql"
    if "machine" in s or "tensorflow" in s or "pytorch" in s or s == "ml": return "ml"
    if "react" in s or "next" in s:                                   return "react"
    if "fastapi" in s:                                                return "fastapi"
    if "python" in s or "django" in s or "flask" in s:               return "python"
    return "python"


def _is_weak_skill(skill: str, evidence_scores: dict) -> bool:
    if skill not in evidence_scores:
        return True
    return evidence_scores[skill] < WEAK_EVIDENCE_THRESHOLD


def _extract_name(profile_data: dict) -> str:
    for key in ("name", "full_name", "candidate_name", "Name", "fullName",
                "person_name", "applicant_name"):
        val = profile_data.get(key)
        if val and str(val).strip() and str(val).strip().lower() not in ("none", "unknown", "n/a"):
            return str(val).strip()
    return ""


def _extract_role(profile_data: dict) -> str:
    for key in ("role", "title", "job_title", "current_role", "position",
                "Role", "Title", "designation", "current_title"):
        val = profile_data.get(key)
        if val and str(val).strip() and str(val).strip().lower() not in ("none", "unknown", "n/a"):
            return str(val).strip()
    return ""


def _extract_email(profile_data: dict) -> str:
    for key in ("email", "email_address", "Email", "contact_email"):
        val = profile_data.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def _extract_location(profile_data: dict) -> str:
    for key in ("location", "city", "address", "Location", "city_state"):
        val = profile_data.get(key)
        if val and str(val).strip():
            return str(val).strip()
    return ""


def orchestrate(user_input):
    print("\n========== STARTED ORCHESTRATION ==========\n")

    resume_payload = _resume_payload(user_input)
    override_name  = (user_input.get("candidate_name") or "").strip()
    agent_trace: list[str] = []

    try:
        # ----------------------------------------------------------
        # AGENT 1 — Profile Agent
        # ----------------------------------------------------------
        agent_trace.append("profile_agent")
        raw_profile  = run_profile_agent(resume_payload["resume_text"])
        profile_data = raw_profile.model_dump()
        print("DEBUG profile_data keys:", list(profile_data.keys()))
        print("DEBUG profile_data:", profile_data)

        # ----------------------------------------------------------
        # AGENT 2 — Evidence Agent
        # ----------------------------------------------------------
        agent_trace.append("evidence_agent")
        try:
            evidence_data = run_evidence_agent(resume_payload["resume_text"])
        except Exception as e:
            print("Evidence agent failed:", e)
            evidence_data = {"aggregated_skill_scores": {}}

        evidence_scores   = evidence_data.get("aggregated_skill_scores", {}) or {}
        has_any_evidence  = bool(evidence_scores)   # True if agent found any external data
        print("DEBUG evidence_scores:", evidence_scores)

        # ----------------------------------------------------------
        # AGENT 3 — Authenticity Check
        # ----------------------------------------------------------
        agent_trace.append("authenticity_agent")
        claimed_skills = profile_data.get("skills", []) or []
        claimed_skills = [
            s if isinstance(s, str) else (s.get("name") or s.get("skill") or str(s))
            for s in claimed_skills if s
        ]

        missing_skills  = []
        verified_skills = []
        pending_skills  = []   # claimed but no external evidence found (neutral — not fraud)

        for skill in claimed_skills:
            ev = evidence_scores.get(skill, None)
            if ev is None:
                # No evidence found for this skill — neutral, generate test
                pending_skills.append(skill)
                missing_skills.append(skill)
            elif ev < WEAK_EVIDENCE_THRESHOLD:
                # Evidence found but score too low — suspicious
                missing_skills.append(skill)
            else:
                verified_skills.append(skill)

        total_skills = len(claimed_skills) or 1

        # ---------------------------------------------------------------
        # Auth score logic:
        # - If no external evidence at all (no GitHub/LinkedIn found):
        #     Give benefit of the doubt — score based on profile completeness
        #     Not flagged as suspicious — just "unverified"
        # - If external evidence was found but skills don't match:
        #     Lower score, possibly flag
        # ---------------------------------------------------------------
        if not has_any_evidence:
            # No external links found — can't verify but can't condemn
            # Score = 0.5 (neutral) + boost for verified ratio (all neutral here)
            authenticity_score = 0.5
            fraud_risk         = 0.0
            verification_status = "No External Evidence"
        else:
            contradicted = sum(
                1 for skill in claimed_skills
                if skill in evidence_scores and evidence_scores[skill] < WEAK_EVIDENCE_THRESHOLD
            )
            fraud_risk         = min(contradicted / total_skills, 1.0)
            authenticity_score = round(max(0.2, 1.0 - fraud_risk), 2)
            verification_status = "Evidence Checked"

        # Only flag when external evidence actively contradicts >50% of claims
        fraud_flag = has_any_evidence and fraud_risk > 0.5

        print(f"DEBUG has_evidence={has_any_evidence} fraud_risk={fraud_risk:.2f} "
              f"auth={authenticity_score} verified={verified_skills} "
              f"pending={pending_skills} missing={missing_skills}")

        authenticity_data = {
            "authenticity_score":   authenticity_score,
            "fraud_flag":           fraud_flag,
            "missing_skills":       missing_skills,
            "verified_skills":      verified_skills,
            "pending_skills":       pending_skills,
            "verification_status":  verification_status,
            "trust_level": (
                "High"   if authenticity_score > 0.7 else
                "Medium" if authenticity_score > 0.4 else
                "Low"
            ),
        }

        # ----------------------------------------------------------
        # AGENT 4 — Skill Testing Agent
        # ----------------------------------------------------------
        agent_trace.append("skill_testing_agent")
        skill_results   = []
        skill_questions = {}
        skill_tests     = []

        for skill in claimed_skills[:12]:
            needs_test = _is_weak_skill(skill, evidence_scores)
            ev         = evidence_scores.get(skill, None)

            if needs_test:
                try:
                    effective_ev = ev if ev is not None else 0.0
                    result       = run_agent(
                        skill=_skill_for_agent(skill),
                        claimed_level="intermediate",
                        evidence=effective_ev,
                        answer=None,
                    )
                    question_text = result.get("task_description", "")
                    difficulty    = result.get("calibrated_level", "medium")

                    skill_results.append({
                        "skill":      skill,
                        "passed":     True,
                        "score":      "Pending",
                        "difficulty": difficulty,
                        "needs_test": True,
                        "category":   "pending",
                    })
                    skill_questions[skill] = question_text
                    skill_tests.append({
                        "skill": skill, "difficulty": difficulty,
                        "question": question_text, "status": "pending",
                        "agent": "skill_testing_agent",
                    })
                except Exception as e:
                    print(f"Skill test failed for {skill}:", e)
                    skill_results.append({
                        "skill": skill, "passed": False, "score": "Error",
                        "difficulty": "N/A", "needs_test": True, "category": "error",
                    })
                    skill_questions[skill] = ""
                    skill_tests.append({
                        "skill": skill, "difficulty": "N/A",
                        "question": "", "status": "error",
                        "agent": "skill_testing_agent",
                    })
            else:
                skill_results.append({
                    "skill":      skill,
                    "passed":     True,
                    "score":      "Verified",
                    "difficulty": "—",
                    "needs_test": False,
                    "category":   "verified",
                })
                skill_questions[skill] = ""
                skill_tests.append({
                    "skill": skill, "difficulty": "—",
                    "question": "", "status": "verified",
                    "agent": "evidence_agent",
                })

        # ----------------------------------------------------------
        # AGENT 5 — Score Aggregator
        # ----------------------------------------------------------
        agent_trace.append("score_aggregator")

        verified_count = len(verified_skills)
        pending_count  = sum(1 for r in skill_results if r["score"] == "Pending")

        # Profile score (0–100)
        profile_nonempty = sum([
            1 if _extract_name(profile_data)     else 0,
            1 if _extract_email(profile_data)    else 0,
            1 if _extract_role(profile_data)     else 0,
            1 if _extract_location(profile_data) else 0,
            1 if claimed_skills                  else 0,
            1 if profile_data.get("experience") or profile_data.get("work_experience") else 0,
            1 if profile_data.get("education")   else 0,
        ])
        profile_score = round((profile_nonempty / 7) * 100)

        # ── SAS score decomposition ──────────────────────────────────────────
        # SAS = authenticity (60%) + profile completeness (40%)
        # Split each half into two equal sub-components so we get 4 bars:
        #
        #   Profile Completeness  = 40% of SAS  → profile_score  * 0.40
        #   Evidence Score        = 30% of SAS  → auth_score     * 0.30
        #   Skill Coverage        = 20% of SAS  → verified_ratio * 0.20
        #   Fraud Risk (inverse)  = 10% of SAS  → (1-fraud_risk) * 0.10
        #
        # Each component is stored as its CONTRIBUTION to the SAS total (0–100
        # scale), so they add up exactly to sas_score.
        # ─────────────────────────────────────────────────────────────────────

        verified_ratio   = verified_count / total_skills          # 0–1
        fraud_inv        = 1.0 - fraud_risk                       # 0–1
        auth_pct         = authenticity_score * 100               # 0–100

        # Weighted contributions (each in 0–100 range, weights sum to 1.0)
        W_PROFILE   = 0.40
        W_EVIDENCE  = 0.30
        W_COVERAGE  = 0.20
        W_FRAUD_INV = 0.10

        contrib_profile   = profile_score  * W_PROFILE    # max 40
        contrib_evidence  = auth_pct       * W_EVIDENCE   # max 30
        contrib_coverage  = verified_ratio * 100 * W_COVERAGE   # max 20
        contrib_fraud_inv = fraud_inv      * 100 * W_FRAUD_INV  # max 10

        sas_raw   = contrib_profile + contrib_evidence + contrib_coverage + contrib_fraud_inv
        sas_score = max(20, round(sas_raw))

        # Store breakdown as rounded contributions — they sum to sas_score
        # (minor rounding diff absorbed into profile_completeness)
        bd_profile   = round(contrib_profile)
        bd_evidence  = round(contrib_evidence)
        bd_coverage  = round(contrib_coverage)
        bd_fraud_inv = round(contrib_fraud_inv)

        # Absorb any rounding delta (±1) into the largest component
        rounding_delta = sas_score - (bd_profile + bd_evidence + bd_coverage + bd_fraud_inv)
        bd_profile += rounding_delta   # largest component absorbs it

        # Skill score — partial credit for pending (50%), floor 10
        partial_credit = (verified_count + 0.5 * pending_count) / total_skills
        skill_score    = max(10, round(partial_credit * 100))

        # Overall
        overall_score = max(10, round(
            0.25 * profile_score +
            0.40 * sas_score     +
            0.35 * skill_score
        ))

        recommendation = (
            "HIRE"   if overall_score >= 70 and not fraud_flag else
            "REVIEW" if overall_score >= 45                    else
            "REJECT"
        )

        print(f"DEBUG profile={profile_score} sas={sas_score} "
              f"(breakdown: {bd_profile}+{bd_evidence}+{bd_coverage}+{bd_fraud_inv}="
              f"{bd_profile+bd_evidence+bd_coverage+bd_fraud_inv}) "
              f"skill={skill_score} overall={overall_score}")

        # ----------------------------------------------------------
        # AGENT 6 — GitHub AI Detection
        # ----------------------------------------------------------
        agent_trace.append("github_ai_agent")
        try:
            github_ai_data = run_github_ai_agent(resume_payload["resume_text"])
            print(f"GitHub AI Agent: {github_ai_data.get('overall_verdict')} "
                  f"(prob={github_ai_data.get('overall_ai_probability')})")
        except Exception as e:
            print(f"GitHub AI agent failed (non-critical): {e}")
            github_ai_data = {
                "github_urls":            [],
                "repos_analysed":         0,
                "repo_results":           [],
                "overall_ai_probability": 0.0,
                "overall_verdict":        "Analysis unavailable",
                "agent":                  "github_ai_agent",
            }

        # ----------------------------------------------------------
        # Identity
        # ----------------------------------------------------------
        extracted_name = _extract_name(profile_data)
        final_name     = override_name or extracted_name or "Unknown"
        final_role     = _extract_role(profile_data)
        final_email    = _extract_email(profile_data)
        final_location = _extract_location(profile_data)

        # Status — use "REVIEW" instead of "FRAUD" for softer language
        status = "REVIEW" if fraud_flag else "DONE"

        candidate_record = {
            "id":               str(uuid.uuid4()),
            "timestamp":        datetime.utcnow().isoformat() + "Z",
            "status":           status,

            "name":             final_name,
            "email":            final_email,
            "role":             final_role,
            "location":         final_location,
            "skills":           claimed_skills,
            "missing_skills":   missing_skills,
            "verified_skills":  verified_skills,
            "pending_skills":   pending_skills,

            "overall_score":    overall_score,
            "profile_score":    profile_score,
            "sas_score":        sas_score,
            "skill_score":      skill_score,
            "authenticity_score": authenticity_score,

            "fraud_flag":       fraud_flag,
            "fraud_confidence": round(fraud_risk, 2),
            "trust_level":      authenticity_data["trust_level"],
            "verification_status": verification_status,

            "recommendation":   recommendation,
            "agent_trace":      agent_trace,
            "skill_tests":      skill_tests,
            "skill_results":    skill_results,
            "skill_questions":  skill_questions,

            "profile":          profile_data,
            "evidence":         evidence_data,
            "authenticity":     authenticity_data,

            "sas_breakdown": {
                "profile_completeness": bd_profile,    # 40% weight → max 40
                "evidence_score":       bd_evidence,   # 30% weight → max 30
                "skill_coverage":       bd_coverage,   # 20% weight → max 20
                "fraud_risk_inverse":   bd_fraud_inv,  # 10% weight → max 10
            },  # these 4 values sum exactly to sas_score

            "skills_matched":      verified_skills[:5],
            "resume_improvements": [],
            "github_ai":           github_ai_data,
        }

        CANDIDATE_DB.append(candidate_record)
        print(f"CANDIDATE STORED: {final_name} (id={candidate_record['id']})")

        return {
            "success":              True,
            "candidate_id":         candidate_record["id"],
            "profile":              profile_data,
            "evidence":             evidence_data,
            "authenticity":         authenticity_data,
            "skill_results":        skill_results,
            "skill_questions":      skill_questions,
            "agent_trace":          agent_trace,
            "overall_score":        overall_score,
            "sas_score":            sas_score,
            "skill_score":          skill_score,
            "profile_score":        profile_score,
            "recommendation":       recommendation,
            "name":                 final_name,
            "role":                 final_role,
            "verified_skills":      verified_skills,
            "pending_skills":       pending_skills,
            "missing_skills":       missing_skills,
            "verification_status":  verification_status,
            "github_ai":            github_ai_data,
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}