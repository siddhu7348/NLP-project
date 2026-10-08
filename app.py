"""FastAPI service.  Run:  uvicorn app:app --reload   then open http://127.0.0.1:8000/docs"""
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.config import load_config
from src.parser import text_from_bytes
from src.screener import screen_resume

app = FastAPI(title="Resume Screener API", version="1.0.0")
cfg = load_config()


class ScreenRequest(BaseModel):
    resume_text: str
    job_description: str


def _run(resume_text: str, job_description: str) -> dict:
    try:
        return screen_resume(resume_text, job_description, cfg)
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
    except RuntimeError as err:  # e.g. missing API key
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as err:  # upstream LLM/API failure
        raise HTTPException(status_code=502, detail=f"LLM call failed: {err}")


@app.get("/health")
def health():
    return {"status": "ok", "model": cfg["llm"]["model"]}


@app.post("/screen")
def screen(req: ScreenRequest):
    """Screen a resume given as plain text."""
    return _run(req.resume_text, req.job_description)


@app.post("/screen/upload")
async def screen_upload(
    resume_file: UploadFile = File(...), job_description: str = Form(...)
):
    """Screen an uploaded resume (.pdf or .txt)."""
    try:
        text = text_from_bytes(resume_file.filename or "", await resume_file.read())
    except ValueError as err:
        raise HTTPException(status_code=422, detail=str(err))
    return _run(text, job_description)
