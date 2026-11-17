"""Append-only audit log writer.

Each line in out/audit_log.jsonl is a JSON-serialised AuditEntry.
"""
from __future__ import annotations

import json
from pathlib import Path

from .models import AuditAction, AuditEntry

_OUT = Path(__file__).parent.parent / "out"
_LOG = _OUT / "audit_log.jsonl"


def _ensure_out() -> None:
    _OUT.mkdir(exist_ok=True)


def log(message_id: str, action: AuditAction, detail: str | None = None) -> None:
    _ensure_out()
    entry = AuditEntry.now(message_id, action, detail)
    with open(_LOG, "a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


def read_log() -> list[AuditEntry]:
    if not _LOG.exists():
        return []
    entries = []
    with open(_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(AuditEntry(**json.loads(line)))
    return entries
