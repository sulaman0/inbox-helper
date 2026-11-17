"""Deterministic rule-based classifier and template reply generator.

Used when ANTHROPIC_API_KEY is not set, --offline is passed, or as fallback
when LLM validation fails. All outputs are deterministic given the same input.
"""
from __future__ import annotations

import re
from typing import Optional

from .models import Classification, Draft, IntentLabel, Urgency

# ------------------------------------------------------------------
# Keyword tables
# ------------------------------------------------------------------

_INTENT_PATTERNS: list[tuple[IntentLabel, list[str]]] = [
    (IntentLabel.withdrawal, [
        r"\bwithdraw\b", r"\bno longer interested\b", r"\bpulling out\b",
        r"\bremove my (application|candidacy)\b", r"\baccept(ed)? another offer\b",
        r"\bdecline\b",
    ]),
    (IntentLabel.complaint, [
        r"\bunacceptable\b", r"\bdisgusting\b", r"\bterrible\b", r"\bhorrible\b",
        r"\bfurious\b", r"\bangry\b", r"\bcomplain\b", r"\bwaste of (my )?time\b",
        r"\bghostd?\b", r"\bdisrespect\b",
    ]),
    (IntentLabel.offer_compensation, [
        r"\bsalary\b", r"\bcompensation\b", r"\bpay\b", r"\boffer letter\b",
        r"\bbase( pay)?\b", r"\bbonus\b", r"\bequity\b", r"\bstock\b",
        r"\bbenefits?\b", r"\botal comp\b",
    ]),
    (IntentLabel.interview_scheduling, [
        r"\bschedul\b", r"\breschedul\b", r"\binterview\b", r"\btime slot\b",
        r"\bavailability\b", r"\bcalendar\b", r"\bconfirm.{0,20}(meet|call|interview)\b",
        r"\bcancel.{0,20}(interview|meeting)\b",
    ]),
    (IntentLabel.relocation_visa, [
        r"\bvisa\b", r"\breloc\b", r"\bwork (permit|authorization)\b",
        r"\bsponsor(ship)?\b", r"\bh[- ]?1b?\b", r"\bgreen card\b",
        r"\binternational\b", r"\bmov(e|ing) to\b",
    ]),
    (IntentLabel.documents, [
        r"\bresume\b", r"\bcv\b", r"\battach\b", r"\bportfolio\b",
        r"\breference(s)?\b", r"\bbackground check\b", r"\bdocument\b",
        r"\bsign\b.*\bform\b", r"\bform\b.*\bsign\b", r"\bonboarding\b",
        r"\btranscript\b", r"\bcertif\b",
    ]),
    (IntentLabel.status_update, [
        r"\bstatus\b", r"\bupdate\b", r"\bheard back\b", r"\bany news\b",
        r"\bfollowing up\b", r"\bfollow[ -]up\b", r"\bwhere (do|am) (things|I) stand\b",
        r"\bstill consider\b", r"\bdecision\b",
    ]),
    (IntentLabel.role_question, [
        r"\bresponsibilit\b", r"\bteam\b", r"\bday[- ]to[- ]day\b",
        r"\bculture\b", r"\bstack\b", r"\btechnolog\b", r"\brole\b",
        r"\bposition\b", r"\bjob description\b", r"\blearn more\b",
        r"\bwhat does .{0,30}(do|involve|look like)\b",
    ]),
]

# ------------------------------------------------------------------
# Reply templates (≤90 words, all placeholders use [PLACEHOLDER: ...])
# ------------------------------------------------------------------

_TEMPLATES: dict[IntentLabel, str] = {
    IntentLabel.status_update: (
        "Hi {name},\n\nThank you for following up! Your application is currently "
        "[PLACEHOLDER: at which stage, e.g., under review / with the hiring manager]. "
        "We expect to have an update for you by [PLACEHOLDER: date]. "
        "We appreciate your patience and will be in touch shortly.\n\nBest regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.interview_scheduling: (
        "Hi {name},\n\nThank you for reaching out about your interview. "
        "[PLACEHOLDER: Confirm, reschedule, or propose new time slots here]. "
        "Please reply to confirm, and I'll send a calendar invite right away.\n\n"
        "Best regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.offer_compensation: (
        "Hi {name},\n\nThank you for your question regarding compensation. "
        "I'd be happy to discuss the details of the offer. "
        "[PLACEHOLDER: Address their specific question or note that you'll arrange a call]. "
        "Please let me know your availability for a quick call.\n\nBest regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.documents: (
        "Hi {name},\n\nThank you for submitting your documents. "
        "[PLACEHOLDER: Confirm what was received, or note what is still needed]. "
        "If you have any questions about the process, don't hesitate to reach out.\n\n"
        "Best regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.withdrawal: (
        "Hi {name},\n\nThank you for letting us know. We completely understand and "
        "respect your decision. We wish you the very best in your next opportunity. "
        "Please don't hesitate to reach out if your circumstances change in the future.\n\n"
        "Best regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.role_question: (
        "Hi {name},\n\nGreat question! [PLACEHOLDER: Answer their specific question about "
        "the role, team, or responsibilities]. "
        "If you'd like more detail, I'm happy to arrange a brief call with the hiring manager.\n\n"
        "Best regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.relocation_visa: (
        "Hi {name},\n\nThank you for raising the relocation/visa question. "
        "[PLACEHOLDER: Confirm whether the company sponsors visas / offers relocation support, "
        "and next steps]. "
        "I'll follow up with more details shortly.\n\nBest regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.complaint: (
        "Hi {name},\n\nI'm truly sorry to hear about your experience — this is not the "
        "standard we hold ourselves to. I'd like to address your concerns directly. "
        "[PLACEHOLDER: Describe the corrective action or escalation step]. "
        "Thank you for bringing this to our attention.\n\nBest regards,\n[PLACEHOLDER: Recruiter name]"
    ),
    IntentLabel.other: (
        "Hi {name},\n\nThank you for your message. I want to make sure I address your "
        "question properly. [PLACEHOLDER: Provide a specific response to their inquiry]. "
        "Please feel free to reach out if you have any further questions.\n\n"
        "Best regards,\n[PLACEHOLDER: Recruiter name]"
    ),
}

# ------------------------------------------------------------------
# Urgency rules
# ------------------------------------------------------------------

_HIGH_URGENCY_INTENTS = {IntentLabel.complaint, IntentLabel.withdrawal, IntentLabel.offer_compensation}
_HIGH_URGENCY_PATTERNS = [r"\burgent\b", r"\bASAP\b", r"\bimmediately\b", r"\bdeadline\b"]
_MED_URGENCY_INTENTS = {IntentLabel.interview_scheduling, IntentLabel.relocation_visa}


def _urgency(intent: IntentLabel, text: str) -> Urgency:
    combined = text.lower()
    if intent in _HIGH_URGENCY_INTENTS:
        return Urgency.high
    for pat in _HIGH_URGENCY_PATTERNS:
        if re.search(pat, combined, re.IGNORECASE):
            return Urgency.high
    if intent in _MED_URGENCY_INTENTS:
        return Urgency.med
    return Urgency.low


def _needs_human(intent: IntentLabel, confidence: float, secondary: Optional[IntentLabel]) -> bool:
    if confidence < 0.6:
        return True
    if intent in {IntentLabel.complaint, IntentLabel.offer_compensation, IntentLabel.withdrawal}:
        return True
    return False


def _one_liner(intent: IntentLabel, text: str) -> str:
    snippets = {
        IntentLabel.status_update: "asking for a status update on their application",
        IntentLabel.interview_scheduling: "requesting to schedule or reschedule an interview",
        IntentLabel.offer_compensation: "inquiring about salary, compensation, or offer details",
        IntentLabel.documents: "submitting or asking about required documents",
        IntentLabel.withdrawal: "withdrawing their application",
        IntentLabel.role_question: "asking questions about the role or team",
        IntentLabel.relocation_visa: "asking about visa sponsorship or relocation support",
        IntentLabel.complaint: "raising a complaint about their experience",
        IntentLabel.other: "sending a message with unclear intent",
    }
    return snippets.get(intent, "sending a general inquiry")


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def classify(message_id: str, subject: str, body: str, from_name: str) -> Classification:
    text = f"{subject} {body}"
    scores: dict[IntentLabel, int] = {label: 0 for label in IntentLabel}

    for label, patterns in _INTENT_PATTERNS:
        for pat in patterns:
            if re.search(pat, text, re.IGNORECASE):
                scores[label] += 1

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_intent, top_score = ranked[0]
    second_intent, second_score = ranked[1]

    if top_score == 0:
        top_intent = IntentLabel.other
        confidence = 0.45
        secondary = None
    else:
        total = sum(s for _, s in ranked[:3]) or 1
        confidence = min(0.95, 0.5 + (top_score / total) * 0.5)
        secondary = second_intent if second_score > 0 and second_intent != top_intent else None

    # Multi-intent messages get slightly lower confidence
    if secondary is not None:
        confidence = max(0.4, confidence - 0.1)

    urgency = _urgency(top_intent, text)
    needs_human = _needs_human(top_intent, confidence, secondary)

    return Classification(
        intent=top_intent,
        secondary_intent=secondary,
        confidence=round(confidence, 2),
        urgency=urgency,
        summary=_one_liner(top_intent, text),
        needs_human_attention=needs_human,
    )


def generate_reply(message_id: str, from_name: str, classification: Classification) -> Draft:
    first_name = from_name.split()[0] if from_name else "there"
    template = _TEMPLATES.get(classification.intent, _TEMPLATES[IntentLabel.other])
    reply = template.format(name=first_name)

    return Draft(
        message_id=message_id,
        draft=reply,
        classification=classification,
        generated_by="offline",
    )
