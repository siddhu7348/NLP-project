"""Loads config.yaml, prompt files and the .env file."""
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_config(path=None) -> dict:
    load_dotenv(ROOT / ".env")
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_prompt(cfg: dict, name: str) -> str:
    """name is 'system' or 'user' (paths come from config.yaml)."""
    return (ROOT / cfg["prompts"][name]).read_text(encoding="utf-8")
