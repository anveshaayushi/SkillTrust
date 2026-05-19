from fastapi import FastAPI, UploadFile, Request, HTTPException
import os
import json
import tempfile
import pdfplumber
import fitz

from google import genai
from docx import Document
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# =========================
# SCHEMA
# =========================

class SkillConfidence(BaseModel):
    skill: str
    score: float


class ProfileOutput(BaseModel):
    skills: List[str]
    vague_claims: List[str]
    confidence: List[SkillConfidence]


# =========================
# TEXT EXTRACTOR
# =========================

def extract_text(file_path: str) -> str:

    # =====================
    # PDF
    # =====================

    if file_path.endswith(".pdf"):

        text = ""

        # ---------- TRY PDFPLUMBER ----------

        try:

            with pdfplumber.open(file_path) as pdf:

                for page in pdf.pages:

                    extracted = page.extract_text()

                    if extracted:
                        text += extracted + "\n"

        except Exception as e:

            print("PDFPLUMBER ERROR:", e)

        # ---------- FALLBACK TO PYMUPDF ----------

        if len(text.strip()) < 100:

            print("\nUSING PYMUPDF FALLBACK...\n")

            try:

                doc = fitz.open(file_path)

                text = ""

                for page in doc:
                    text += page.get_text()

            except Exception as e:

                print("PYMUPDF ERROR:", e)

        print("\n========== EXTRACTED PDF TEXT ==========\n")
        print(text[:5000])
        print("\n=======================================\n")

        if not text.strip():

            raise ValueError("No text found in PDF")

        return text

    # =====================
    # DOCX
    # =====================

    elif file_path.endswith(".docx"):

        doc = Document(file_path)

        return "\n".join(
            para.text
            for para in doc.paragraphs
        )

    # =====================
    # TXT
    # =====================

    elif file_path.endswith(".txt"):

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            return f.read()

    # =====================
    # INVALID FORMAT
    # =====================

    else:

        raise ValueError(
            "Only PDF, DOCX, TXT supported"
        )


# =========================
# CORE AGENT
# =========================

def run_profile_agent(resume_text: str) -> ProfileOutput:

    client = genai.Client(
        api_key=GEMINI_API_KEY
    )

    prompt = f"""
    You are a resume analysis agent.

    Given this resume text, extract:

    1. All technical skills mentioned
    2. Vague or unverifiable claims
    3. Confidence score (0.0 to 1.0) for each skill

    IMPORTANT:
    - Extract ONLY real technical skills
    - Ignore soft skills unless vague
    - Extract GitHub technologies if present
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

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ProfileOutput,
        }
    )

    parsed_json = json.loads(response.text)

    print("\n========== PROFILE OUTPUT ==========\n")
    print(parsed_json)
    print("\n===================================\n")

    return ProfileOutput(**parsed_json)


# =========================
# PROFILE ENDPOINT
# =========================

@app.post("/profile")
async def profile_endpoint(request: Request):

    content_type = request.headers.get(
        "content-type",
        ""
    )

    # =====================
    # JSON MODE
    # =====================

    if "application/json" in content_type:

        data = await request.json()

        resume_text = data.get("resume_text")

        if not resume_text:

            raise HTTPException(
                status_code=400,
                detail="resume_text required"
            )

        result = run_profile_agent(
            resume_text
        )

        return result.model_dump()

    # =====================
    # FILE UPLOAD MODE
    # =====================

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

    # =====================
    # INVALID CONTENT TYPE
    # =====================

    raise HTTPException(
        status_code=415,
        detail="Use application/json or multipart/form-data"
    )


# =========================
# ROOT ENDPOINT
# =========================

@app.get("/")
def home():

    return {
        "message": "Profile Agent API running"
    }


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True
    )