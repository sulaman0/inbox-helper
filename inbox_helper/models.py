from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class IntentLabel(str, Enum):
    status_update = "status_update"
    interview_scheduling = "interview_scheduling"
    offer_compensation = "offer_compensation"
    documents = "documents"
    withdrawal = "withdrawal"
    role_question = "role_question"
    relocation_visa = "relocation_visa"
    complaint = "complaint"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    med = "med"
    high = "high"


class Message(BaseModel):
    id: str
    from_name: str
    from_email: str
    received_at: str
    subject: str
    body: str


class Classification(BaseModel):
    intent: IntentLabel
    secondary_intent: Optional[IntentLabel] = None
    confidence: float
    urgency: Urgency
    summary: str
    needs_human_attention: bool

    @field_validator("confidence")
    @classmethod
    def clamp_confidence(cls, v: float) -> float:
        return max(0.0, min(1.0, v))


class Draft(BaseModel):
    message_id: str
    draft: str
    classification: Classification
    generated_by: str  # "llm" or "offline"


class ReviewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ReviewedDraft(BaseModel):
    message_id: str
    original_draft: str
    final_reply: Optional[str] = None
    status: ReviewStatus = ReviewStatus.pending
    reviewed_at: Optional[str] = None
    edit_note: Optional[str] = None


class AuditAction(str, Enum):
    classified = "classified"
    drafted = "drafted"
    approved = "approved"
    edited = "edited"
    rejected = "rejected"
    regenerated = "regenerated"
    flagged = "flagged"


class AuditEntry(BaseModel):
    timestamp: str
    message_id: str
    action: AuditAction
    detail: Optional[str] = None

    @classmethod
    def now(cls, message_id: str, action: AuditAction, detail: str | None = None) -> "AuditEntry":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            message_id=message_id,
            action=action,
            detail=detail,
        )
