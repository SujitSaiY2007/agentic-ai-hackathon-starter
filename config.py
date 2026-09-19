from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL_ID = os.getenv("OPENROUTER_MODEL", os.getenv("AGNO_MODEL", "openai/gpt-4o-mini"))
DB_PATH = str(ROOT / "tmp" / "agentos.db")


def require_openrouter_key() -> None:
    if not os.getenv("OPENROUTER_API_KEY"):
        raise RuntimeError(
            "OPENROUTER_API_KEY is missing. Add your OpenRouter API key to .env file."
        )


# Backward compatibility alias
def require_google_key() -> None:
    require_openrouter_key()
