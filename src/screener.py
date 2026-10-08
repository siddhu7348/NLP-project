"""Core logic: build the prompt, call the LLM, parse + validate the JSON result."""
import json
import re

from . import llm_client
from .config import load_prompt


def _extract_json(text: str) -> dict:
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model output did not contain a JSON object.")
    return json.loads(text[start : end + 1])


def _as_list(value) -> list:
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)] if value else []


def _clean(data: dict, threshold: int) -> dict:
    try:
        score = int(round(float(data.get("match_score", 0))))
    except (TypeError, ValueError):
        score = 0
    score = max(0, min(100, score))

    if score >= threshold:
        decision = "Shortlist"
    elif score >= threshold - 20:
        decision = "Maybe"
    else:
        decision = "Reject"

    return {
        "match_score": score,
        "decision": decision,
        "matched_skills": _as_list(data.get("matched_skills")),
        "missing_skills": _as_list(data.get("missing_skills")),
        "strengths": _as_list(data.get("strengths")),
        "concerns": _as_list(data.get("concerns")),
        "suggestions": _as_list(data.get("suggestions")),
        "summary": str(data.get("summary", "")),
    }


def screen_resume(resume_text: str, job_description: str, cfg: dict) -> dict:
    """Compare a resume to a job description and return a structured result."""
    resume_text, job_description = resume_text.strip(), job_description.strip()
    if not resume_text or not job_description:
        raise ValueError("Both resume text and job description are required.")

    rules = cfg["screening"]
    resume_text = resume_text[: rules["max_resume_chars"]]
    job_description = job_description[: rules["max_jd_chars"]]

    system_prompt = load_prompt(cfg, "system")
    user_prompt = (
        load_prompt(cfg, "user")
        .replace("{job_description}", job_description)
        .replace("{resume}", resume_text)
    )

    last_error = None
    raw = ""
    for _ in range(rules.get("max_retries", 1) + 1):
        raw = llm_client.chat(cfg, system_prompt, user_prompt)
        try:
            return _clean(_extract_json(raw), rules["shortlist_threshold"])
        except (ValueError, json.JSONDecodeError) as err:
            last_error = err
    raise ValueError(
        f"Could not parse model output as JSON: {last_error}. "
        f"Raw output started with: {raw[:300]!r}"
    )