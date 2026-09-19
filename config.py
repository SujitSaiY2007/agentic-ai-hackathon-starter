from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# Agno's Gemini model examples use GOOGLE_API_KEY. Accept GEMINI_API_KEY too
# because that naming is common in Gemini projects.
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

MODEL_ID = os.getenv("AGNO_MODEL", "gemini-3.6-flash")
DB_PATH = str(ROOT / "tmp" / "agentos.db")


def require_google_key() -> None:
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY is missing. Create .env from .env.example and add your Gemini API key."
        )
