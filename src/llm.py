"""OpenAI-compatible LLM client wrapper for MemoryOS.

Reads configuration from ``src.config`` and lazily creates a client. No
network call happens at import time.
"""

import threading

from openai import OpenAI, OpenAIError

from src.config import get_llm_api_key, get_llm_base_url, get_llm_model

DEFAULT_TEMPERATURE = 0.2
# Generous cap: some OpenRouter free-tier routes pick reasoning models that spend
# a large share of the budget on "thinking" before answering. A higher cap ensures
# the final content is not truncated to an empty response.
DEFAULT_MAX_TOKENS = 1500

# Number of retries when the model returns an empty response (common on free /
# reasoning routes). The temperature is nudged up per retry to coax a reply.
EMPTY_RESPONSE_RETRIES = 2

_client: OpenAI | None = None
_client_lock = threading.Lock()


class LLMNotConfiguredError(RuntimeError):
    """Raised when an LLM call is attempted without a configured API key."""


class LLMAPIError(RuntimeError):
    """Raised when the LLM API request fails."""


class LLMEmptyResponseError(RuntimeError):
    """Raised when the LLM returns no usable text."""


def is_available() -> bool:
    """Return True when an API key is configured so LLM calls can be made."""
    return bool(get_llm_api_key())


def get_client() -> OpenAI:
    """Return the shared OpenAI-compatible client, creating it once on demand."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                api_key = get_llm_api_key()
                if not api_key:
                    raise LLMNotConfiguredError(
                        "LLM_API_KEY is not configured. Add it to your .env file "
                        "(e.g. an OpenRouter key) to enable AI answering."
                    )
                _client = OpenAI(api_key=api_key, base_url=get_llm_base_url())
    return _client


def generate_answer(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> str:
    """Send the prompts to the configured model and return its text response.

    Retries on empty responses (free-tier / reasoning-model flakiness) with a
    slightly higher temperature. Raises ``LLMEmptyResponseError`` after the
    retries are exhausted.
    """
    if not system_prompt or not user_prompt:
        raise ValueError("system_prompt and user_prompt must be non-empty")
    last_error: Exception | None = None
    for attempt in range(EMPTY_RESPONSE_RETRIES + 1):
        try:
            response = get_client().chat.completions.create(
                model=get_llm_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LLMNotConfiguredError:
            raise
        except OpenAIError as exc:
            raise LLMAPIError(f"LLM API request failed: {exc}") from exc

        try:
            text = (response.choices[0].message.content or "").strip()
        except (AttributeError, IndexError) as exc:
            raise LLMEmptyResponseError("LLM returned an unreadable response") from exc

        if text:
            return text
        last_error = LLMEmptyResponseError("LLM returned an empty response")
        if attempt < EMPTY_RESPONSE_RETRIES:
            temperature = min(1.0, temperature + 0.3)
    raise last_error