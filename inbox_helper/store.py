"""Filesystem state store.

Reads/writes JSON files in the out/ directory.
No database — JSON files only.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Optional

from .models import Draft, Message, ReviewedDraft, ReviewStatus

_ROOT = Path(__file__).parent.parent
_OUT = _ROOT / "out"
_DATA = _ROOT / "data"


def _ensure_out() -> None:
    _OUT.mkdir(exist_ok=True)
    (_OUT / "outbox").mkdir(exist_ok=True)


# ------------------------------------------------------------------
# Message loading
# ------------------------------------------------------------------

def load_messages(path: str | Path) -> list[Message]:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return _load_csv(path)
    return _load_json(path)


def _load_json(path: Path) -> list[Message]:
    with open(path) as f:
        data = json.load(f)
    return [Message(**m) for m in data]


def _load_csv(path: Path) -> list[Message]:
    messages = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            messages.append(Message(**row))
    return messages


# ------------------------------------------------------------------
# Draft persistence
# ------------------------------------------------------------------

def save_drafts(drafts: list[Draft]) -> Path:
    _ensure_out()
    out_path = _OUT / "drafts.json"
    data = [d.model_dump() for d in drafts]
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    return out_path


def load_drafts() -> list[Draft]:
    path = _OUT / "drafts.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    return [Draft(**d) for d in data]


# ------------------------------------------------------------------
# Review state
# ------------------------------------------------------------------

def load_review_state() -> dict[str, ReviewedDraft]:
    path = _OUT / "review_state.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    return {k: ReviewedDraft(**v) for k, v in data.items()}


def save_review_state(state: dict[str, ReviewedDraft]) -> None:
    _ensure_out()
    path = _OUT / "review_state.json"
    with open(path, "w") as f:
        json.dump({k: v.model_dump() for k, v in state.items()}, f, indent=2)


# ------------------------------------------------------------------
# Approved replies
# ------------------------------------------------------------------

def save_approved_reply(reviewed: ReviewedDraft, msg: Optional[Message] = None) -> None:
    _ensure_out()
    # Append to approved_replies.json
    ar_path = _OUT / "approved_replies.json"
    existing = []
    if ar_path.exists():
        with open(ar_path) as f:
            existing = json.load(f)
    # Remove old entry for same message_id
    existing = [e for e in existing if e.get("message_id") != reviewed.message_id]
    existing.append(reviewed.model_dump())
    with open(ar_path, "w") as f:
        json.dump(existing, f, indent=2)

    # Write .eml file
    if msg and reviewed.final_reply:
        _write_eml(reviewed, msg)


def _write_eml(reviewed: ReviewedDraft, msg: Message) -> None:
    _ensure_out()
    eml_path = _OUT / "outbox" / f"{reviewed.message_id}.eml"
    reply = reviewed.final_reply or ""
    content = (
        f"To: {msg.from_email}\n"
        f"Subject: Re: {msg.subject}\n"
        f"Date: {reviewed.reviewed_at}\n"
        f"Content-Type: text/plain; charset=utf-8\n\n"
        f"{reply}\n"
    )
    with open(eml_path, "w", encoding="utf-8") as f:
        f.write(content)
