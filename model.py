# pyrefly: ignore [missing-import]
from agno.models.google import Gemini

from config import MODEL_ID, require_google_key


def gemini() -> Gemini:
    require_google_key()
    return Gemini(
    id=MODEL_ID,
    retries=3,
    delay_between_retries=2,
    exponential_backoff=True,
)
