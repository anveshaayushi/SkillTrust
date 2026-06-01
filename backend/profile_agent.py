from fastapi import FastAPI, UploadFile, Request, HTTPException
import os
import json
import tempfile
import time

from google import genai
from docx import Document
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# ========================================
# SCHEMA
# ========================================

class SkillConfidence(BaseModel):
    skill: str
    score: float


class ProfileOutput(BaseModel):
    skills: List[str]
    vague_claims: List[str]
    confidence: List[SkillConfidence]


# ========================================
# TEXT EXTRACTOR
# ========================================

def extract_text(file_path: str) -> str:

    text = ""

    # =========================
    # PDF
    # =========================

    if file_path.endswith(".pdf"):

        import fitz  # PyMuPDF

        doc = fitz.open(file_path)

        for page in doc:
            text += page.get_text()

        doc.close()

    # =========================
    # DOCX
    # =========================

    elif file_path.endswith(".docx"):

        doc = Document(file_path)

        text = "\n".join(
            [para.text for para in doc.paragraphs]
        )

    # =========================
    # TXT
    # =========================

    elif file_path.endswith(".txt"):

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

    else:

        raise ValueError(
            "Only PDF, DOCX, TXT supported"
        )

    print("\n========== EXTRACTED RESUME TEXT ==========\n")

    print(text[:5000])

    return text


# ========================================
# FALLBACK (Gemini unavailable)
# ========================================

def _fallback_profile(resume_text: str) -> ProfileOutput:

    text = (resume_text or "").lower()

    hints = [
        ("python", "Python"),
        ("fastapi", "FastAPI"),
        ("flask", "Flask"),
        ("django", "Django"),
        ("react", "React"),
        ("typescript", "TypeScript"),
        ("javascript", "JavaScript"),
        ("node", "JavaScript"),
        ("sql", "SQL"),
        ("postgres", "SQL"),
        ("mysql", "SQL"),
        ("tensorflow", "Machine Learning"),
        ("pytorch", "Machine Learning"),
        ("kubernetes", "Kubernetes"),
        ("docker", "Docker"),
        ("aws", "AWS"),
        ("azure", "Azure"),
        ("gcp", "GCP"),
    ]

    skills: list[str] = []

    confidence: list[SkillConfidence] = []

    for needle, label in hints:

        if needle in text and label not in skills:

            skills.append(label)

            confidence.append(
                SkillConfidence(
                    skill=label,
                    score=0.45,
                )
            )

    vague: list[str] = []

    if not skills:

        vague.append(
            "Could not infer skills (LLM unavailable); upload a clearer resume"
        )

    return ProfileOutput(
        skills=skills,
        vague_claims=vague,
        confidence=confidence,
    )


def _is_transient_llm_error(err: Exception) -> bool:

    msg = str(err).lower()

    return any(

        token in msg

        for token in (

            "503",

            "429",

            "unavailable",

            "overloaded",

            "deadline",

            "timed out",

            "timeout",

            "500",

            "resource exhausted",

            "internal error",

            "try again",

        )

    )


# ========================================
# CORE AGENT
# ========================================

def run_profile_agent(
    resume_text: str
) -> ProfileOutput:

    if not (resume_text or "").strip():

        return ProfileOutput(
            skills=[],
            vague_claims=["Empty resume text"],
            confidence=[],
        )

    prompt = f"""
    You are a resume analysis agent.

    Given this resume text, extract:

    1. All technical skills mentioned
    2. Vague or unverifiable claims
    3. Confidence score (0.0 to 1.0) for each skill

    Rules:
    - Specific tools (React, FastAPI, SQL) → higher confidence
    - Buzzwords with no proof → low confidence
    - Return ONLY valid JSON

    Resume:
    {resume_text}

    Return exactly this format:

    {{
        "skills": ["React", "Python"],
        "vague_claims": ["problem-solving"],
        "confidence": [
            {{
                "skill": "React",
                "score": 0.8
            }},
            {{
                "skill": "Python",
                "score": 0.6
            }}
        ]
    }}
    """

    last_err: Optional[Exception] = None

    for attempt in range(3):

        try:

            client = genai.Client(
                api_key=GEMINI_API_KEY
            )

            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,

                config={
                    "response_mime_type":
                        "application/json",

                    "response_schema":
                        ProfileOutput,
                }
            )

            parsed_json = json.loads(
                response.text
            )

            return ProfileOutput(
                **parsed_json
            )

        except Exception as e:

            last_err = e

            print(
                f"\nPROFILE AGENT ATTEMPT {attempt + 1} FAILED: {e}"
            )

            if _is_transient_llm_error(e) and attempt < 2:

                time.sleep(1.5 * (attempt + 1))

                continue

            break

    print(
        "\nPROFILE AGENT: using fallback profile after LLM failure:",
        last_err,
    )

    return _fallback_profile(resume_text)


# ========================================
# PROFILE ENDPOINT
# ========================================

@app.post("/profile")
async def profile_endpoint(
    request: Request
):

    content_type = request.headers.get(
        "content-type",
        ""
    )

    # =========================
    # JSON MODE
    # =========================

    if "application/json" in content_type:

        data = await request.json()

        resume_text = data.get(
            "resume_text"
        )

        if not resume_text:

            raise HTTPException(
                status_code=400,
                detail="resume_text required"
            )

        result = run_profile_agent(
            resume_text
        )

        return result.model_dump()

    # =========================
    # FILE MODE
    # =========================

    elif "multipart/form-data" in content_type:

        form = await request.form()

        resume: UploadFile = form.get(
            "resume"
        )

        if resume is None:

            raise HTTPException(
                status_code=400,
                detail="resume file required"
            )

        suffix = os.path.splitext(
            resume.filename
        )[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            temp_file.write(
                await resume.read()
            )

            temp_path = temp_file.name

        try:

            resume_text = extract_text(
                temp_path
            )

            result = run_profile_agent(
                resume_text
            )

            return result.model_dump()

        finally:

            os.remove(temp_path)

    # =========================
    # INVALID TYPE
    # =========================

    raise HTTPException(
        status_code=415,
        detail=
            "Use application/json or multipart/form-data"
    )


# ========================================
# ROOT
# ========================================

@app.get("/")
def home():

    return {
        "message":
            "Profile Agent API running"
    }


# ========================================
# START SERVER
# ========================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )