from __future__ import annotations

from typing import Any

from agno.models.openrouter import OpenRouter

from config import MODEL_ID, OPENROUTER_API_KEY, require_openrouter_key


class OpenRouterModels:
    """Convenient presets for popular OpenRouter models across categories."""

    # Fast & Cost-Effective
    GPT_4O_MINI = "openai/gpt-4o-mini"
    CLAUDE_3_5_HAIKU = "anthropic/claude-3.5-haiku"
    GEMINI_2_FLASH = "google/gemini-2.0-flash-001"
    LLAMA_3_3_70B = "meta-llama/llama-3.3-70b-instruct"
    QWEN_2_5_72B = "qwen/qwen-2.5-72b-instruct"
    MISTRAL_NEMO = "mistralai/mistral-nemo"

    # Flagship & Advanced
    CLAUDE_3_5_SONNET = "anthropic/claude-3.5-sonnet"
    CLAUDE_3_7_SONNET = "anthropic/claude-3.7-sonnet"
    GPT_4O = "openai/gpt-4o"

    # Deep Reasoning & Math/Code
    DEEPSEEK_R1 = "deepseek/deepseek-r1"
    DEEPSEEK_V3 = "deepseek/deepseek-chat"
    O3_MINI = "openai/o3-mini"
    QWEN_QWQ_32B = "qwen/qwq-32b-preview"

    # Free Tier (subject to OpenRouter availability)
    FREE_DEEPSEEK_R1 = "deepseek/deepseek-r1:free"
    FREE_DEEPSEEK_V3 = "deepseek/deepseek-chat:free"
    FREE_LLAMA_3_3_70B = "meta-llama/llama-3.3-70b-instruct:free"
    FREE_GEMINI_2_FLASH = "google/gemini-2.0-flash-exp:free"

    # OpenRouter Auto Router (automatically selects best model for the prompt)
    AUTO = "openrouter/auto"


def openrouter(
    id: str | None = None,
    fallback_models: list[str] | None = None,
    max_retries: int = 3,
    **kwargs: Any,
) -> OpenRouter:
    """Create an OpenRouter model instance.

    Args:
        id: OpenRouter model string (e.g., 'anthropic/claude-3.5-sonnet',
            'deepseek/deepseek-r1', or presets from OpenRouterModels).
            If omitted, uses OPENROUTER_MODEL from .env or 'openai/gpt-4o-mini'.
        fallback_models: Optional list of fallback model IDs to try in order
            if the primary model encounters rate limits or errors.
        max_retries: Number of request retry attempts.
        **kwargs: Additional parameters passed to OpenRouter (e.g. temperature, max_tokens).
    """
    require_openrouter_key()
    selected_id = id or MODEL_ID
    models_list = None
    if fallback_models:
        # OpenRouter dynamic routing includes primary model + fallbacks
        models_list = [selected_id] + [m for m in fallback_models if m != selected_id]

    return OpenRouter(
        id=selected_id,
        api_key=OPENROUTER_API_KEY,
        max_retries=max_retries,
        models=models_list,
        **kwargs,
    )


# Short aliases
MODELS = OpenRouterModels
gemini = openrouter

