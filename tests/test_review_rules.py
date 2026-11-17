"""Tests for review business rules: placeholder blocking, audit log, store."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from inbox_helper.models import (
    AuditAction,
    Classification,
    Draft,
    IntentLabel,
    Message,
    ReviewedDraft,
    ReviewStatus,
    Urgency,
)


# ------------------------------------------------------------------
# Placeholder detection
# ------------------------------------------------------------------

def _has_placeholder(text: str) -> bool:
    return "[PLACEHOLDER" in text


class TestPlaceholderRule:
    def test_detects_placeholder(self):
        assert _has_placeholder("Hi [PLACEHOLDER: name]") is True

    def test_no_placeholder(self):
        assert _has_placeholder("Hi Alice, your application is under review.") is False

    def test_partial_no_trigger(self):
        assert _has_placeholder("[NOTE: this is a note]") is False

    def test_multiple_placeholders(self):
        assert _has_placeholder("[PLACEHOLDER: a] and [PLACEHOLDER: b]") is True


# ------------------------------------------------------------------
# Audit log tests
# ------------------------------------------------------------------

class TestAuditLog:
    def test_audit_entry_creation(self):
        from inbox_helper.models import AuditEntry
        e = AuditEntry.now("msg_001", AuditAction.classified, "intent=status_update")
        assert e.message_id == "msg_001"
        assert e.action == AuditAction.classified
        assert e.detail == "intent=status_update"
        assert "Z" in e.timestamp

    def test_audit_log_write_read(self, tmp_path, monkeypatch):
        from inbox_helper import audit
        monkeypatch.setattr(audit, "_OUT", tmp_path)
        monkeypatch.setattr(audit, "_LOG", tmp_path / "audit_log.jsonl")
        (tmp_path).mkdir(exist_ok=True)

        audit.log("msg_001", AuditAction.classified, "intent=status_update")
        audit.log("msg_001", AuditAction.drafted)
        audit.log("msg_001", AuditAction.approved)

        entries = audit.read_log()
        assert len(entries) == 3
        assert entries[0].action == AuditAction.classified
        assert entries[2].action == AuditAction.approved

    def test_all_actions_loggable(self, tmp_path, monkeypatch):
        from inbox_helper import audit
        monkeypatch.setattr(audit, "_OUT", tmp_path)
        monkeypatch.setattr(audit, "_LOG", tmp_path / "audit_log.jsonl")

        for action in AuditAction:
            audit.log("test", action)

        entries = audit.read_log()
        assert len(entries) == len(list(AuditAction))


# ------------------------------------------------------------------
# Store tests
# ------------------------------------------------------------------

class TestStore:
    def _make_draft(self, mid: str) -> Draft:
        return Draft(
            message_id=mid,
            draft="Hi [PLACEHOLDER: name], test reply.",
            classification=Classification(
                intent=IntentLabel.status_update,
                confidence=0.8,
                urgency=Urgency.low,
                summary="test",
                needs_human_attention=False,
            ),
            generated_by="offline",
        )

    def test_save_and_load_drafts(self, tmp_path, monkeypatch):
        from inbox_helper import store
        monkeypatch.setattr(store, "_OUT", tmp_path)

        drafts = [self._make_draft(f"msg_{i:03d}") for i in range(3)]
        store.save_drafts(drafts)
        loaded = store.load_drafts()
        assert len(loaded) == 3
        assert loaded[0].message_id == "msg_000"

    def test_save_and_load_review_state(self, tmp_path, monkeypatch):
        from inbox_helper import store
        monkeypatch.setattr(store, "_OUT", tmp_path)

        state = {
            "msg_001": ReviewedDraft(
                message_id="msg_001",
                original_draft="Hi [PLACEHOLDER]",
                status=ReviewStatus.pending,
            )
        }
        store.save_review_state(state)
        loaded = store.load_review_state()
        assert "msg_001" in loaded
        assert loaded["msg_001"].status == ReviewStatus.pending

    def test_save_approved_reply_creates_eml(self, tmp_path, monkeypatch):
        from inbox_helper import store
        monkeypatch.setattr(store, "_OUT", tmp_path)
        (tmp_path / "outbox").mkdir(exist_ok=True)

        rv = ReviewedDraft(
            message_id="msg_001",
            original_draft="original",
            final_reply="Hi Alice, your application is under review.\n\nBest regards,\nSarah",
            status=ReviewStatus.approved,
            reviewed_at="2024-11-10T10:00:00Z",
        )
        msg = Message(
            id="msg_001",
            from_name="Alice",
            from_email="alice@test.com",
            received_at="2024-11-10T09:00:00Z",
            subject="Status update",
            body="Any news?",
        )
        store.save_approved_reply(rv, msg)

        eml_path = tmp_path / "outbox" / "msg_001.eml"
        assert eml_path.exists()
        content = eml_path.read_text()
        assert "alice@test.com" in content
        assert "Hi Alice" in content

    def test_load_messages_json(self):
        from inbox_helper import store
        path = Path(__file__).parent.parent / "data" / "messages.json"
        messages = store.load_messages(path)
        assert len(messages) == 30
        assert messages[0].id == "msg_001"

    def test_load_messages_csv(self, tmp_path):
        from inbox_helper import store
        csv_content = "id,from_name,from_email,received_at,subject,body\n"
        csv_content += "csv_001,Test User,test@example.com,2024-01-01T00:00:00Z,Hello,Hello body\n"
        csv_path = tmp_path / "test.csv"
        csv_path.write_text(csv_content)
        messages = store.load_messages(csv_path)
        assert len(messages) == 1
        assert messages[0].id == "csv_001"


# ------------------------------------------------------------------
# Model validation tests
# ------------------------------------------------------------------

class TestModels:
    def test_confidence_clamped_above_1(self):
        cl = Classification(
            intent=IntentLabel.status_update,
            confidence=1.5,  # should clamp
            urgency=Urgency.low,
            summary="test",
            needs_human_attention=False,
        )
        assert cl.confidence == 1.0

    def test_confidence_clamped_below_0(self):
        cl = Classification(
            intent=IntentLabel.status_update,
            confidence=-0.5,
            urgency=Urgency.low,
            summary="test",
            needs_human_attention=False,
        )
        assert cl.confidence == 0.0

    def test_reviewed_draft_default_pending(self):
        rv = ReviewedDraft(message_id="1", original_draft="test")
        assert rv.status == ReviewStatus.pending
