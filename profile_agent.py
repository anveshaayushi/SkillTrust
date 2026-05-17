from fastapi import FastAPI, UploadFile, File
import os
import json
import re
import tempfile
from urllib import response
import pdfplumber
from google import genai
from docx import Document
from pydantic import BaseModel
from typing import List, Dict
from dotenv import load_dotenv
app = FastAPI()
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# Schema — stays exactly the same
class ProfileOutput(BaseModel):
    skills: List[str]
    vague_claims: List[str]
    confidence: Dict[str, float]

# Text extractor — stays exactly the same
def extract_text(file_path: str) -> str:
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
        if not text.strip():
            raise ValueError("No text found in PDF")
        return text
    elif file_path.endswith(".docx"):
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Only PDF or DOCX supported")

# Core agent — only this function changes


def run_profile_agent(resume_text: str) -> ProfileOutput:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
    You are a resume analysis agent.

    Given this resume text, extract:
    1. All technical skills mentioned
    2. Vague or unverifiable claims (like "problem-solving", "ML", "Full-Stack")
    3. Confidence score (0.0 to 1.0) for each skill

    Rules:
    - Specific tools (React, FastAPI, SQL) → higher confidence
    - Buzzwords with no proof → low confidence, add to vague_claims
    - Return ONLY valid JSON, absolutely no explanation text

    Resume:
    {resume_text}

    Return exactly this format:
    {{
        "skills": ["skill1", "skill2"],
        "vague_claims": ["vague1"],
        "confidence": {{"skill1": 0.8, "skill2": 0.4}}
    }}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": ProfileOutput,  # Gemini validates against your Pydantic model
        }
    )
# response.text is already clean JSON — no regex needed
    return ProfileOutput(**json.loads(response.text))

# Entry point — stays exactly the same

@app.post("/profile")
async def profile_endpoint(resume: UploadFile = File(...)):

    suffix = os.path.splitext(resume.filename)[1]

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(await resume.read())
        temp_path = temp_file.name

    try:
        resume_text = extract_text(temp_path)

        result = run_profile_agent(resume_text)

        return result.model_dump()

    finally:
        os.remove(temp_path)

