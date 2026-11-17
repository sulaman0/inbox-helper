"""Tests for offline classifier and LLM path (mocked)."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from inbox_helper.models import IntentLabel, Urgency, Classification
from inbox_helper import offline
from inbox_helper import classify as classify_mod


# ------------------------------------------------------------------
# Offline classifier tests
# ------------------------------------------------------------------

class TestOfflineClassify:
    def test_status_update_detected(self):
        result = offline.classify("1", "Following up", "Any update on my application status?", "John Doe")
        assert result.intent == IntentLabel.status_update

    def test_withdrawal_detected(self):
        result = offline.classify("2", "Withdrawing", "I would like to withdraw my application. I no longer interested.", "Jane")
        assert result.intent == IntentLabel.withdrawal

    def test_withdrawal_high_urgency(self):
        result = offline.classify("3", "Pulling out", "I'm pulling out of the application process.", "Jane")
        assert result.urgency == Urgency.high

    def test_complaint_needs_human_attention(self):
        result = offline.classify("4", "Terrible process", "This is terrible and unacceptable treatment!", "Angry Person")
        assert result.needs_human_attention is True
        assert result.intent == IntentLabel.complaint

    def test_offer_compensation_detected(self):
        result = offline.classify("5", "Salary question", "What is the salary range and equity for this role?", "Alice")
        assert result.intent == IntentLabel.offer_compensation
        assert result.needs_human_attention is True

    def test_interview_scheduling_detected(self):
        result = offline.classify("6", "Schedule interview", "I'd like to schedule my interview for next Tuesday.", "Bob")
        assert result.intent == IntentLabel.interview_scheduling

    def test_visa_relocation_detected(self):
        result = offline.classify("7", "H1B visa", "Do you sponsor H-1B visas for this role?", "Wei")
        assert result.intent == IntentLabel.relocation_visa

    def test_documents_detected(self):
        result = offline.classify("8", "Submitting CV", "Please find my resume and portfolio attached.", "Sam")
        assert result.intent == IntentLabel.documents

    def test_role_question_detected(self):
        result = offline.classify("9", "Team question", "What does the day-to-day look like for this role?", "Pat")
        assert result.intent == IntentLabel.role_question

    def test_empty_message_falls_to_other(self):
        result = offline.classify("10", "k", "k", "Victor")
        assert result.intent == IntentLabel.other
        assert result.confidence < 0.6

    def test_confidence_range(self):
        result = offline.classify("11", "Status", "Following up on my application status.", "Chris")
        assert 0.0 <= result.confidence <= 1.0

    def test_secondary_intent_set_for_multi_topic(self):
        result = offline.classify(
            "12",
            "Offer + visa",
            "I have a question about the salary and I also need visa sponsorship.",
            "Priya",
        )
        # Both offer_compensation and relocation_visa patterns fire
        assert result.secondary_intent is not None

    def test_needs_human_low_confidence(self):
        result = offline.classify("13", "k", "k", "Victor")
        assert result.needs_human_attention is True  # confidence < 0.6

    def test_summary_is_string(self):
        result = offline.classify("14", "Interview", "I want to schedule an interview.", "Alice")
        assert isinstance(result.summary, str)
        assert len(result.summary) > 0


# ------------------------------------------------------------------
# Reply generation tests
# ------------------------------------------------------------------

class TestOfflineReply:
    def _make_cl(self, intent: IntentLabel) -> Classification:
        return Classification(
            intent=intent,
            confidence=0.9,
            urgency=Urgency.low,
            summary="test",
            needs_human_attention=False,
        )

    def test_reply_uses_first_name(self):
        cl = self._make_cl(IntentLabel.status_update)
        draft = offline.generate_reply("1", "Priya Nair", cl)
        assert "Priya" in draft.draft

    def test_reply_has_placeholder(self):
        cl = self._make_cl(IntentLabel.status_update)
        draft = offline.generate_reply("1", "Alice", cl)
        assert "[PLACEHOLDER" in draft.draft

    def test_withdrawal_reply_no_reconsider(self):
        cl = self._make_cl(IntentLabel.withdrawal)
        draft = offline.generate_reply("2", "Zoe", cl)
        # Should not ask them to reconsider
        assert "reconsider" not in draft.draft.lower()

    def test_complaint_reply_has_apology(self):
        cl = self._make_cl(IntentLabel.complaint)
        draft = offline.generate_reply("3", "Tyler", cl)
        lower = draft.draft.lower()
        assert "sorry" in lower or "apologize" in lower or "apolog" in lower

    def test_reply_generated_by_offline(self):
        cl = self._make_cl(IntentLabel.role_question)
        draft = offline.generate_reply("4", "Liam", cl)
        assert draft.generated_by == "offline"

    def test_all_intents_have_templates(self):
        for intent in IntentLabel:
            cl = self._make_cl(intent)
            draft = offline.generate_reply("x", "Test User", cl)
            assert len(draft.draft) > 10


# ------------------------------------------------------------------
# LLM path tests (mocked)
# ------------------------------------------------------------------

class TestLLMClassify:
    def _make_response(self, payload: dict) -> MagicMock:
        resp = MagicMock()
        resp.content = [MagicMock(text=json.dumps(payload))]
        return resp

    def test_llm_classify_happy_path(self):
        payload = {
            "intent": "status_update",
            "secondary_intent": None,
            "confidence": 0.92,
            "urgency": "low",
            "summary": "Candidate asking for a status update",
            "needs_human_attention": False,
        }
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("inbox_helper.llm._client") as mock_client:
                mock_client.return_value.messages.create.return_value = self._make_response(payload)
                from inbox_helper import llm
                cl, fell_back = llm.classify_with_llm("1", "Status", "Any update?", "Alice")
        assert cl.intent == IntentLabel.status_update
        assert cl.confidence == 0.92
        assert fell_back is False

    def test_llm_classify_falls_back_on_bad_json(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("inbox_helper.llm._client") as mock_client:
                mock_client.return_value.messages.create.return_value = MagicMock(
                    content=[MagicMock(text="not valid json at all")]
                )
                from inbox_helper import llm
                cl, fell_back = llm.classify_with_llm("2", "Status", "Any update?", "Bob")
        assert fell_back is True
        assert isinstance(cl, Classification)

    def test_llm_classify_falls_back_on_api_error(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("inbox_helper.llm._client") as mock_client:
                mock_client.return_value.messages.create.side_effect = Exception("API error")
                from inbox_helper import llm
                cl, fell_back = llm.classify_with_llm("3", "Subject", "Body", "Carol")
        assert fell_back is True

    def test_classify_message_offline_mode(self):
        from inbox_helper.models import Message
        msg = Message(
            id="1",
            from_name="Alice",
            from_email="alice@test.com",
            received_at="2024-01-01T00:00:00Z",
            subject="Following up",
            body="Any update on my application status?",
        )
        cl, source, fell_back = classify_mod.classify_message(msg, offline=True)
        assert source == "offline"
        assert fell_back is False
        assert isinstance(cl, Classification)

    def test_classify_message_no_api_key_uses_offline(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from inbox_helper.models import Message
        msg = Message(
            id="2",
            from_name="Bob",
            from_email="bob@test.com",
            received_at="2024-01-01T00:00:00Z",
            subject="Withdrawal",
            body="I withdraw my application.",
        )
        cl, source, _ = classify_mod.classify_message(msg)
        assert source == "offline"
