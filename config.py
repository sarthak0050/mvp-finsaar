"""Reads settings from st.secrets, falling back to environment variables. Never hard-code keys."""
from __future__ import annotations

import os

DEFAULT_MODEL = "gemini-3.1-flash-lite"
DEFAULT_FALLBACK_MODEL = "gemini-3.5-flash-lite"
EMBED_MODEL = "gemini-embedding-001"
DEFAULT_AMFI_LINK = "https://www.amfiindia.com"
DEFAULT_SEBI_LINK = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13"
SESSION_QUESTION_LIMIT = 20
TIMEOUT_SECONDS = 15


def get(key: str, default: str | None = None) -> str | None:
    try:
        import streamlit as st
        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:  # no secrets file / not running in Streamlit
        pass
    return os.environ.get(key, default)


def api_key() -> str | None:
    return get("GEMINI_API_KEY")


def model_name() -> str:
    return get("GEMINI_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL


def amfi_link() -> str:
    return get("AMFI_LINK", DEFAULT_AMFI_LINK) or DEFAULT_AMFI_LINK


def fallback_model() -> str | None:
    """Tried once when the main model is busy / over quota. Set GEMINI_FALLBACK_MODEL="" to disable."""
    m = get("GEMINI_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)
    return m or None


def sebi_link() -> str:
    """SEBI's list of registered investment advisers (shown on the decline path)."""
    return get("SEBI_LINK", DEFAULT_SEBI_LINK) or DEFAULT_SEBI_LINK
