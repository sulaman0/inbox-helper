"""Top-level classification dispatcher.

Routes to LLM or offline path based on API key availability and --offline flag.
"""
from __future__ import annotations

import os

from .models import Classification, Message
from . import offline as _offline
from . import llm as _llm


def is_llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


def classify_message(msg: Message, offline: bool = False) -> tuple[Classification, str, bool]:
    """Classify a message.

    Returns (classification, source, used_fallback).
    source is "llm" or "offline".
    used_fallback is True if LLM was attempted but fell back to offline.
    """
    if offline or not is_llm_available():
        result = _offline.classify(msg.id, msg.subject, msg.body, msg.from_name)
        return result, "offline", False

    classification, fell_back = _llm.classify_with_llm(
        msg.id, msg.subject, msg.body, msg.from_name
    )
    source = "offline" if fell_back else "llm"
    return classification, source, fell_back
