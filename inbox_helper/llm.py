"""LLM client wrapper for Anthropic Claude.

Handles prompt building, JSON parsing, pydantic validation, and
retry-once-then-fallback logic.
"""
from __future__ import annotations

import json
import os
from typing import Optional

import anthropic
from pydantic import ValidationError

from .models import Classification, Draft, IntentLabel, Urgency
from . import offline as _offline

_DEFAULT_MODEL = "claude-sonnet-4-6"


def _get_model() -> str:
    return os.environ.get("LLM_MODEL", _DEFAULT_MODEL)


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _classify_prompt(subject: str, body: str) -> str:
    return f"""You are a recruiting-inbox classifier. Classify the candidate message below.

Return ONLY a JSON object — no prose, no markdown fences — with exactly these fields:
{{
  "intent": one of [status_update, interview_scheduling, offer_compensation, documents,
                    withdrawal, role_question, relocation_visa, complaint, other],
  "secondary_intent": same enum or null,
  "confidence": float 0.0-1.0,
  "urgency": one of [low, med, high],
  "summary": "one sentence ≤15 words",
  "needs_human_attention": true/false
}}

Rules for needs_human_attention: set true if confidence < 0.6, or intent is complaint,
offer_compensation, or withdrawal.

---
Subject: {subject}
Body:
{body}
---"""


def _draft_prompt(from_name: str, subject: str, body: str, intent: str, guidelines: str) -> str:
    first_name = from_name.split()[0] if from_name else "there"
    return f"""You are a friendly, professional recruiter. Draft a short reply (≤90 words) to this candidate message.

Guidelines for intent "{intent}":
{guidelines}

Rules:
- Address the candidate by first name: {first_name}
- Never invent facts (dates, salary numbers, decisions)
- Use [PLACEHOLDER: description] for anything the recruiter must fill in
- Be warm, specific, and professional
- End with a sign-off and [PLACEHOLDER: Recruiter name]

---
Subject: {subject}
Body:
{body}
---

Return only the reply text, no extra commentary."""


def _load_guidelines() -> str:
    path = os.path.join(os.path.dirname(__file__), "..", "prompts", "reply_guidelines.md")
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return "Be polite, concise, and use placeholders for unknown information."


def _parse_classification(raw: str) -> Classification:
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])
    data = json.loads(raw.strip())
    return Classification(**data)


def classify_with_llm(message_id: str, subject: str, body: str, from_name: str) -> tuple[Classification, bool]:
    """Returns (classification, used_fallback)."""
    prompt = _classify_prompt(subject, body)
    attempts = 0
    last_exc: Optional[Exception] = None

    while attempts < 2:
        attempts += 1
        try:
            client = _client()
            resp = client.messages.create(
                model=_get_model(),
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = resp.content[0].text
            classification = _parse_classification(raw)
            return classification, False
        except (json.JSONDecodeError, ValidationError, KeyError) as e:
            last_exc = e
            continue
        except Exception as e:
            last_exc = e
            break

    # Fallback
    fallback = _offline.classify(message_id, subject, body, from_name)
    return fallback, True


def draft_with_llm(message_id: str, from_name: str, subject: str, body: str,
                   classification: Classification) -> tuple[Draft, bool]:
    """Returns (draft, used_fallback)."""
    guidelines = _load_guidelines()
    prompt = _draft_prompt(from_name, subject, body, classification.intent.value, guidelines)

    try:
        client = _client()
        resp = client.messages.create(
            model=_get_model(),
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        reply_text = resp.content[0].text.strip()
        draft = Draft(
            message_id=message_id,
            draft=reply_text,
            classification=classification,
            generated_by="llm",
        )
        return draft, False
    except Exception:
        fallback = _offline.generate_reply(message_id, from_name, classification)
        return fallback, True
