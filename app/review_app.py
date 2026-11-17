"""Streamlit human-review UI for Inbox Helper."""
from __future__ import annotations

import sys
import os
from datetime import datetime
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

from inbox_helper.models import AuditAction, Draft, Message, ReviewedDraft, ReviewStatus
from inbox_helper import audit, store
from inbox_helper.classify import is_llm_available
from inbox_helper import classify as _classify, draft as _draft

# ------------------------------------------------------------------
# Page config
# ------------------------------------------------------------------

st.set_page_config(
    page_title="Inbox Helper — Review",
    page_icon="📬",
    layout="wide",
)

# ------------------------------------------------------------------
# State helpers
# ------------------------------------------------------------------

URGENCY_COLOR = {"high": "🔴", "med": "🟡", "low": "🟢"}
INTENT_EMOJI = {
    "status_update": "📋",
    "interview_scheduling": "📅",
    "offer_compensation": "💰",
    "documents": "📎",
    "withdrawal": "🚪",
    "role_question": "❓",
    "relocation_visa": "✈️",
    "complaint": "⚠️",
    "other": "📩",
}


def _load_state():
    if "drafts" not in st.session_state:
        st.session_state.drafts = {d.message_id: d for d in store.load_drafts()}
    if "messages" not in st.session_state:
        msgs = store.load_messages(Path("data/messages.json"))
        st.session_state.messages = {m.id: m for m in msgs}
    if "review" not in st.session_state:
        st.session_state.review = store.load_review_state()
        # Seed pending entries for any draft without a review entry
        for mid in st.session_state.drafts:
            if mid not in st.session_state.review:
                d = st.session_state.drafts[mid]
                st.session_state.review[mid] = ReviewedDraft(
                    message_id=mid,
                    original_draft=d.draft,
                    status=ReviewStatus.pending,
                )
        store.save_review_state(st.session_state.review)


def _save_reviewed(mid: str, status: ReviewStatus, final_reply: str | None = None, note: str = "") -> None:
    rv = st.session_state.review[mid]
    rv.status = status
    rv.final_reply = final_reply
    rv.reviewed_at = datetime.utcnow().isoformat() + "Z"
    rv.edit_note = note or None
    store.save_review_state(st.session_state.review)
    if status == ReviewStatus.approved and final_reply:
        msg = st.session_state.messages.get(mid)
        store.save_approved_reply(rv, msg)
    action = AuditAction.approved if status == ReviewStatus.approved else AuditAction.rejected
    if note:
        action = AuditAction.edited
    audit.log(mid, action, detail=note or status.value)


def _has_placeholder(text: str) -> bool:
    return "[PLACEHOLDER" in text


# ------------------------------------------------------------------
# Sidebar stats
# ------------------------------------------------------------------

def _sidebar(drafts: dict, review: dict) -> None:
    st.sidebar.title("📬 Inbox Helper")
    total = len(drafts)
    approved = sum(1 for r in review.values() if r.status == ReviewStatus.approved)
    rejected = sum(1 for r in review.values() if r.status == ReviewStatus.rejected)
    pending = total - approved - rejected
    flagged = sum(1 for d in drafts.values() if d.classification.needs_human_attention)

    st.sidebar.metric("Total messages", total)
    st.sidebar.metric("✅ Approved", approved)
    st.sidebar.metric("❌ Rejected", rejected)
    st.sidebar.metric("⏳ Pending", pending)
    st.sidebar.metric("🚩 Needs attention", flagged)

    st.sidebar.divider()
    st.sidebar.caption("Approved replies → `out/approved_replies.json`")
    st.sidebar.caption("EML files → `out/outbox/`")
    st.sidebar.caption("Audit log → `out/audit_log.jsonl`")

    # Regenerate all button
    st.sidebar.divider()
    if st.sidebar.button("🔄 Re-run classification on all messages"):
        offline = not is_llm_available()
        with st.spinner("Re-classifying..."):
            msgs = list(st.session_state.messages.values())
            new_drafts = []
            for msg in msgs:
                cl, _, _ = _classify.classify_message(msg, offline=offline)
                dr, _ = _draft.generate_draft(msg, cl, offline=offline)
                new_drafts.append(dr)
            store.save_drafts(new_drafts)
            st.session_state.drafts = {d.message_id: d for d in new_drafts}
            # Reset review state for regenerated
            for d in new_drafts:
                st.session_state.review[d.message_id] = ReviewedDraft(
                    message_id=d.message_id,
                    original_draft=d.draft,
                    status=ReviewStatus.pending,
                )
                audit.log(d.message_id, AuditAction.regenerated)
            store.save_review_state(st.session_state.review)
        st.rerun()


# ------------------------------------------------------------------
# Main app
# ------------------------------------------------------------------

def main() -> None:
    _load_state()
    drafts: dict[str, Draft] = st.session_state.drafts
    messages: dict[str, Message] = st.session_state.messages
    review: dict[str, ReviewedDraft] = st.session_state.review

    if not drafts:
        st.warning("No drafts found. Run `python -m inbox_helper run data/messages.json` first.")
        st.code("python -m inbox_helper run data/messages.json --offline")
        return

    _sidebar(drafts, review)

    st.title("📬 Inbox Helper — Human Review")
    st.caption("Every draft must be reviewed before it is sent. Nothing is sent automatically.")

    # Group by intent, sort by urgency
    urgency_rank = {"high": 0, "med": 1, "low": 2}
    intent_groups: dict[str, list[Draft]] = {}
    for d in drafts.values():
        intent_groups.setdefault(d.classification.intent.value, []).append(d)
    for intent in intent_groups:
        intent_groups[intent].sort(key=lambda d: urgency_rank.get(d.classification.urgency.value, 2))

    intent_order = sorted(intent_groups.keys(), key=lambda i: (
        min(urgency_rank.get(d.classification.urgency.value, 2) for d in intent_groups[i]),
        i,
    ))

    # Filter tabs
    filter_col, _ = st.columns([2, 8])
    with filter_col:
        status_filter = st.selectbox("Show", ["All", "Pending", "Approved", "Rejected"], index=0)

    for intent in intent_order:
        group = intent_groups[intent]
        emoji = INTENT_EMOJI.get(intent, "📩")

        # Apply filter
        filtered = []
        for d in group:
            rv = review.get(d.message_id)
            rv_status = rv.status.value if rv else "pending"
            if status_filter == "All" or rv_status.lower() == status_filter.lower():
                filtered.append(d)

        if not filtered:
            continue

        with st.expander(f"{emoji} **{intent.replace('_', ' ').title()}** — {len(filtered)} message(s)", expanded=True):
            for d in filtered:
                msg = messages.get(d.message_id)
                rv = review.get(d.message_id)
                _render_card(d, msg, rv)


def _render_card(d: Draft, msg: Message | None, rv: ReviewedDraft | None) -> None:
    mid = d.message_id
    cl = d.classification
    urgency_icon = URGENCY_COLOR.get(cl.urgency.value, "⚪")
    status_badge = {
        ReviewStatus.pending: "⏳ Pending",
        ReviewStatus.approved: "✅ Approved",
        ReviewStatus.rejected: "❌ Rejected",
    }.get(rv.status if rv else ReviewStatus.pending, "⏳")

    card_key = f"card_{mid}"
    with st.container():
        col1, col2 = st.columns([7, 3])
        with col1:
            st.markdown(f"**{msg.from_name if msg else mid}** `{msg.from_email if msg else ''}`  {urgency_icon} `{cl.urgency.value}`  {status_badge}")
            st.caption(f"Subject: *{msg.subject if msg else ''}* | Intent: `{cl.intent.value}` ({cl.confidence:.0%}) | Summary: {cl.summary}")
            if cl.needs_human_attention:
                st.warning("🚩 Flagged for human attention", icon="⚠️")
        with col2:
            st.caption(f"ID: `{mid}` | Mode: `{d.generated_by}`")

        # Original message
        with st.expander("📧 Original message", expanded=False):
            if msg:
                st.markdown(f"**From:** {msg.from_name} &lt;{msg.from_email}&gt;  \n**Date:** {msg.received_at}  \n**Subject:** {msg.subject}")
                st.text_area("Body", value=msg.body, height=120, disabled=True, key=f"orig_{mid}", label_visibility="collapsed")

        # Draft reply (editable)
        current_draft = rv.final_reply if (rv and rv.final_reply) else d.draft
        edited = st.text_area(
            "Draft reply (editable)",
            value=current_draft,
            height=160,
            key=f"draft_{mid}",
        )

        # Placeholder warning
        if _has_placeholder(edited):
            st.info("ℹ️ This draft contains `[PLACEHOLDER: ...]` text. Fill in all placeholders before approving.", icon="📝")

        # Action buttons
        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)

        with btn_col1:
            approve_disabled = _has_placeholder(edited)
            if st.button("✅ Approve", key=f"approve_{mid}", disabled=approve_disabled, use_container_width=True):
                _save_reviewed(mid, ReviewStatus.approved, edited)
                st.success(f"Approved! Reply saved to out/approved_replies.json")
                st.rerun()

        with btn_col2:
            if st.button("✏️ Edit & Approve", key=f"editapprove_{mid}", disabled=approve_disabled, use_container_width=True):
                _save_reviewed(mid, ReviewStatus.approved, edited, note="edited before approval")
                st.success("Edited and approved!")
                st.rerun()

        with btn_col3:
            if st.button("❌ Reject", key=f"reject_{mid}", use_container_width=True):
                _save_reviewed(mid, ReviewStatus.rejected)
                st.rerun()

        with btn_col4:
            if st.button("🔄 Regenerate", key=f"regen_{mid}", use_container_width=True):
                offline = not is_llm_available()
                msg_obj = st.session_state.messages.get(mid)
                if msg_obj:
                    new_cl, _, _ = _classify.classify_message(msg_obj, offline=offline)
                    new_draft, _ = _draft.generate_draft(msg_obj, new_cl, offline=offline)
                    st.session_state.drafts[mid] = new_draft
                    st.session_state.review[mid] = ReviewedDraft(
                        message_id=mid,
                        original_draft=new_draft.draft,
                        status=ReviewStatus.pending,
                    )
                    store.save_drafts(list(st.session_state.drafts.values()))
                    store.save_review_state(st.session_state.review)
                    audit.log(mid, AuditAction.regenerated)
                    st.rerun()

        st.divider()


if __name__ == "__main__":
    main()
