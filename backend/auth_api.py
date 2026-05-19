from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import tempfile
import os
import traceback

from orchestrator import orchestrate
from profile_agent import extract_text

app = FastAPI()


# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_payload(code: str, message: str, status: int):

    return JSONResponse(
        status_code=status,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


# =========================
# ROOT
# =========================

@app.get("/")
def home():

    return {
        "status": "Backend running",
        "success": True,
    }


# =========================
# ANALYZE ENDPOINT
# =========================

@app.post("/analyze")
async def analyze(
    resume: UploadFile = File(...)
):

    temp_path = None

    try:

        print("\n========== FILE RECEIVED ==========")
        print("Filename:", resume.filename)

        suffix = os.path.splitext(
            resume.filename or ""
        )[1].lower()

        if suffix not in (".pdf", ".txt", ".docx"):

            return _error_payload(
                "UNSUPPORTED_FILE_TYPE",
                "Only PDF, TXT, and DOCX files are supported.",
                400,
            )

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix
        ) as temp_file:

            contents = await resume.read()

            temp_file.write(contents)

            temp_path = temp_file.name

        print("TEMP FILE:", temp_path)

        resume_text = extract_text(
            temp_path
        )

        print("\n========== EXTRACTED TEXT (preview) ==========")
        print((resume_text or "")[:1000])

        if not (resume_text or "").strip():

            return _error_payload(
                "EMPTY_RESUME",
                "No text could be extracted from the file.",
                400,
            )

        result = orchestrate({
            "resume_text": resume_text
        })

        if not isinstance(result, dict):

            return _error_payload(
                "INVALID_PIPELINE_RESULT",
                "Orchestrator returned an unexpected result.",
                502,
            )

        if result.get("success") is False or (

            result.get("error") and not result.get("profile")

        ):

            return _error_payload(
                "PIPELINE_ERROR",
                str(result.get("error", "Unknown orchestration error")),
                502,
            )

        result["success"] = True

        print("\n========== PIPELINE SUCCESS ==========")

        return result

    except ValueError as e:

        return _error_payload(
            "BAD_FILE",
            str(e),
            400,
        )

    except Exception as e:

        print("\n========== BACKEND ERROR ==========")

        traceback.print_exc()

        return _error_payload(
            "INTERNAL_ERROR",
            str(e),
            500,
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            try:

                os.remove(temp_path)

            except OSError:

                pass


# =========================
# START SERVER
# =========================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "auth_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
