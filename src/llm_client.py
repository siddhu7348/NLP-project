"""Thin wrapper around an OpenAI-compatible chat API, with retry and model fallback."""
import os

from openai import APIStatusError, OpenAI

_client = None


def get_client(cfg: dict) -> OpenAI:
    global _client
    if _client is None:
        env_name = cfg["llm"]["api_key_env"]
        api_key = os.getenv(env_name)
        if not api_key:
            raise RuntimeError(
                f"Missing API key. Set {env_name} in your .env file or environment."
            )
        _client = OpenAI(
            api_key=api_key,
            base_url=cfg["llm"]["base_url"],
            timeout=cfg["llm"].get("timeout_seconds", 60),
            max_retries=3,
            default_headers={"Accept-Encoding": "identity"},
        )
    return _client


def chat(cfg: dict, system_prompt: str, user_prompt: str) -> str:
    """Try the main model, then each fallback model if it is busy or unavailable."""
    llm = cfg["llm"]
    models = [llm["model"]] + llm.get("fallback_models", [])
    last_error = None
    for model in models:
        try:
            kwargs = dict(
                model=model,
                temperature=llm.get("temperature", 0),
                max_tokens=llm.get("max_tokens", 2500),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            # JSON mode only for Gemini models (Gemma etc. may reject it)
            if model.startswith("gemini"):
                kwargs["response_format"] = {"type": "json_object"}

            response = get_client(cfg).chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except APIStatusError as err:
            if err.status_code in (404, 429, 500, 502, 503, 504):
                last_error = err
                continue
            raise
    raise last_error