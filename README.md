# Resume Screener (LLM + API)

An NLP project that uses a pretrained Large Language Model, called through an API, to compare a **resume** against a **job description**. It returns a match score, matched and missing skills, strengths, concerns, improvement suggestions and a Shortlist / Maybe / Reject decision. It can be used from the command line or as a REST API (FastAPI).

## How the LLM is used
1. The resume and job description are cleaned and truncated (`src/screener.py`).
2. They are inserted into a prompt template (`prompts/user_prompt.txt`). A system prompt (`prompts/system_prompt.txt`) defines the recruiter role, fairness rules and a strict JSON output schema.
3. The prompt is sent to a hosted LLM through an OpenAI-compatible API (`src/llm_client.py`). The default provider is **Google Gemini**, and the model and provider are set in `config.yaml`. If the main model is busy or unavailable (404, 429, 5xx errors), the client automatically retries and then tries the `fallback_models` listed in the config.
4. The reply is parsed and validated as JSON (with one retry if it is malformed). The final decision is computed from a configurable score threshold.

## Project structure
```
resume-screener/
├── app.py                  # FastAPI service (/health, /screen, /screen/upload)
├── main.py                 # Command-line interface
├── config.yaml             # Provider, model, fallback models, thresholds, prompt paths
├── prompts/
│   ├── system_prompt.txt   # Role, rules, JSON schema
│   └── user_prompt.txt     # Template with {job_description} and {resume}
├── src/
│   ├── config.py           # Loads config, prompts and .env
│   ├── llm_client.py       # API call wrapper with retry and model fallback
│   ├── parser.py           # PDF / TXT text extraction
│   └── screener.py         # Prompting, parsing and validation
├── data/                   # Sample resume and job description
├── notebooks/              # Google Colab notebook
├── requirements.txt
└── .env.example            # Template for your API key
```

## Setup (VS Code)
1. Install Python 3.10 or newer and open the project folder in VS Code (`File > Open Folder`). Open the folder that directly contains `main.py`.
2. Open a terminal and (recommended) create a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS / Linux
```
   You can also use an existing environment such as Anaconda.
3. Install the dependencies:
```bash
   pip install -r requirements.txt
```
4. Get a free Gemini API key from https://aistudio.google.com/apikey.
5. Copy `.env.example` to `.env` and paste your key:
```
   GEMINI_API_KEY=your_real_key
```
   Do not use quotes or spaces around `=`. Never commit `.env` to GitHub (it is already listed in `.gitignore`).

## Run it
**Command line**
```bash
python main.py --resume data/sample_resume.txt --jd data/sample_job_description.txt
```
Add `--json` to print the raw JSON result.

**API server**
```bash
uvicorn app:app --reload
```
Open http://127.0.0.1:8000/docs to try the endpoints in the browser.

Example request:
```bash
curl -X POST http://127.0.0.1:8000/screen \
  -H "Content-Type: application/json" \
  -d '{"resume_text": "Python, pandas, scikit-learn, FastAPI...", "job_description": "ML engineer needing Python, SQL, PyTorch..."}'
```

Example response:
```json
{
  "match_score": 85,
  "decision": "Shortlist",
  "matched_skills": ["Python", "SQL", "Flask and FastAPI"],
  "missing_skills": ["Docker", "Cloud platforms", "PyTorch"],
  "strengths": ["..."],
  "concerns": ["..."],
  "suggestions": ["..."],
  "summary": "..."
}
```
To upload a PDF instead, send `POST /screen/upload` with the form fields `resume_file` (file) and `job_description` (text).

## Run in Google Colab
Open `notebooks/resume_screener_colab.ipynb` in Colab. Add your key under the key icon (Secrets) with the name `GEMINI_API_KEY`, then run the cells from top to bottom.

## Configuration (`config.yaml`)
| Setting | Purpose |
|---|---|
| `llm.base_url` | OpenAI-compatible endpoint of the provider |
| `llm.api_key_env` | Name of the variable in `.env` that holds the key |
| `llm.model` | Main model to use |
| `llm.fallback_models` | Backup models tried if the main one is busy or unavailable |
| `screening.shortlist_threshold` | Score for Shortlist (Maybe starts 20 points lower) |

Model names change over time. To see the models your key can use, run:
```bash
python -c "from src.config import load_config; from src import llm_client; c=load_config(); [print(m.id) for m in llm_client.get_client(c).models.list()]"
```
Use text models only (names containing `flash` or `pro`), not `tts`, `image`, `live` or `embedding` models. To switch provider, change `base_url`, `api_key_env` and `model`, and add the matching key to `.env`. No code changes are needed.

## Troubleshooting
- **`Missing API key`**: `.env` must be in the same folder as `main.py`, and the variable name must match `llm.api_key_env` in `config.yaml`.
- **404 model not found**: the model name is retired or not available to your key. Pick another from the list command above.
- **503 / 429 errors**: the model is overloaded or rate-limited. Retry after a minute, or add more `fallback_models`.
- **`KeyError: 'llm'`**: `config.yaml` is missing the top-level `llm:` section or its indentation is wrong.

## Notes and limitations
- This is a screening aid, not a hiring decision-maker. LLM output can be wrong or biased, so a human should review the results.
- Scanned (image-only) PDFs are not supported because there is no OCR.
- Free API tiers have rate limits, and model availability can change.