"""Application configuration for MemoryOS.

Loads environment variables from a local `.env` file (when present) and
exposes the LLM API configuration with sensible defaults.
"""

import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
DEFAULT_LLM_MODEL = "gpt-4o-mini"


def get_llm_api_key() -> str:
    """Return the configured LLM API key, or an empty string if unset."""
    return os.getenv("LLM_API_KEY", "")


def get_llm_base_url() -> str:
    """Return the LLM base URL, defaulting to the OpenAI API."""
    return os.getenv("LLM_BASE_URL", DEFAULT_LLM_BASE_URL)


def get_llm_model() -> str:
    """Return the LLM model name, defaulting to a sensible model."""
    return os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL)


def is_llm_configured() -> bool:
    """Return True if an LLM API key has been configured."""
    return bool(get_llm_api_key())