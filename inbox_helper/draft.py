"""Top-level draft dispatcher.

Routes to LLM or offline path based on API key availability and --offline flag.
"""
from __future__ import annotations

from .models import Classification, Draft, Message
from .classify import is_llm_available
from . import offline as _offline
from . import llm as _llm


def generate_draft(msg: Message, classification: Classification, offline: bool = False) -> tuple[Draft, bool]:
    """Generate a reply draft.

    Returns (draft, used_fallback).
    """
    if offline or not is_llm_available():
        draft = _offline.generate_reply(msg.id, msg.from_name, classification)
        return draft, False

    draft, fell_back = _llm.draft_with_llm(
        msg.id, msg.from_name, msg.subject, msg.body, classification
    )
    return draft, fell_back
