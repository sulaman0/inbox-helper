"""Tests for draft generation."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from inbox_helper.models import Classification, Draft, IntentLabel, Message, Urgency
from inbox_helper import draft as draft_mod


def _make_msg(mid: str = "1", subject: str = "Test", body: str = "Hello") -> Message:
    return Message(
        id=mid,
        from_name="Test User",
        from_email="test@example.com",
        received_at="2024-01-01T00:00:00Z",
        subject=subject,
        body=body,
    )


def _make_cl(intent: IntentLabel = IntentLabel.status_update) -> Classification:
    return Classification(
        intent=intent,
        confidence=0.85,
        urgency=Urgency.low,
        summary="test summary",
        needs_human_attention=False,
    )


class TestOfflineDraft:
    def test_offline_draft_returns_draft_object(self):
        msg = _make_msg()
        cl = _make_cl()
        d, fell_back = draft_mod.generate_draft(msg, cl, offline=True)
        assert isinstance(d, Draft)
        assert fell_back is False

    def test_offline_draft_has_placeholder(self):
        msg = _make_msg()
        cl = _make_cl(IntentLabel.status_update)
        d, _ = draft_mod.generate_draft(msg, cl, offline=True)
        assert "[PLACEHOLDER" in d.draft

    def test_offline_draft_uses_first_name(self):
        msg = _make_msg()
        cl = _make_cl()
        d, _ = draft_mod.generate_draft(msg, cl, offline=True)
        assert "Test" in d.draft

    def test_complaint_draft_has_apology(self):
        msg = _make_msg()
        cl = _make_cl(IntentLabel.complaint)
        d, _ = draft_mod.generate_draft(msg, cl, offline=True)
        assert any(word in d.draft.lower() for word in ["sorry", "apolog"])

    def test_withdrawal_draft_wishes_well(self):
        msg = _make_msg()
        cl = _make_cl(IntentLabel.withdrawal)
        d, _ = draft_mod.generate_draft(msg, cl, offline=True)
        lower = d.draft.lower()
        assert any(word in lower for word in ["best", "wish", "understand"])


class TestLLMDraft:
    def test_llm_draft_happy_path(self):
        msg = _make_msg()
        cl = _make_cl()
        reply_text = "Hi Test,\n\nYour application is currently [PLACEHOLDER: stage].\n\nBest regards,\n[PLACEHOLDER: Recruiter name]"
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("inbox_helper.llm._client") as mock_client:
                mock_client.return_value.messages.create.return_value = MagicMock(
                    content=[MagicMock(text=reply_text)]
                )
                d, fell_back = draft_mod.generate_draft(msg, cl, offline=False)
        assert d.generated_by == "llm"
        assert fell_back is False
        assert d.draft == reply_text

    def test_llm_draft_falls_back_on_error(self):
        msg = _make_msg()
        cl = _make_cl()
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("inbox_helper.llm._client") as mock_client:
                mock_client.return_value.messages.create.side_effect = Exception("Network error")
                d, fell_back = draft_mod.generate_draft(msg, cl, offline=False)
        assert fell_back is True
        assert d.generated_by == "offline"

    def test_no_api_key_uses_offline(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        msg = _make_msg()
        cl = _make_cl()
        d, fell_back = draft_mod.generate_draft(msg, cl, offline=False)
        assert d.generated_by == "offline"
        assert fell_back is False
