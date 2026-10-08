"""Simple web UI.  Run:  python gradio_app.py   then open http://127.0.0.1:7860"""
import gradio as gr

from src.config import load_config
from src.parser import text_from_file
from src.screener import screen_resume

cfg = load_config()


def _bullets(items):
    return "\n".join(f"- {item}" for item in items) if items else "- None"


def format_result(r: dict) -> str:
    return (
        f"## Match score: {r['match_score']}/100 - {r['decision']}\n\n"
        f"**Summary:** {r['summary']}\n\n"
        f"### Matched skills\n{_bullets(r['matched_skills'])}\n\n"
        f"### Missing skills\n{_bullets(r['missing_skills'])}\n\n"
        f"### Strengths\n{_bullets(r['strengths'])}\n\n"
        f"### Concerns\n{_bullets(r['concerns'])}\n\n"
        f"### Suggestions\n{_bullets(r['suggestions'])}\n"
    )


def ui_fn(jd, resume_file, resume_text):
    if not jd or not jd.strip():
        return "Please paste a job description."
    try:
        if resume_file is not None:
            path = resume_file if isinstance(resume_file, str) else resume_file.name
            resume_text = text_from_file(path)
        if not resume_text or not resume_text.strip():
            return "Please upload a PDF or TXT resume, or paste the resume text."
        return format_result(screen_resume(resume_text, jd, cfg))
    except Exception as err:
        return f"**Error:** {err}"


demo = gr.Interface(
    fn=ui_fn,
    inputs=[
        gr.Textbox(lines=8, label="Job description"),
        gr.File(label="Upload resume (PDF or TXT)", file_types=[".pdf", ".txt"]),
        gr.Textbox(lines=8, label="...or paste resume text"),
    ],
    outputs=gr.Markdown(label="Screening result"),
    title="AI Resume Screener",
)

if __name__ == "__main__":
    demo.launch()