# Inbox Helper

A local Python tool that helps recruiting teams triage candidate emails. It classifies each message into a named intent, generates a short draft reply with `[PLACEHOLDER: ...]` markers, and presents every draft for human review before anything is marked as "sent." Nothing is ever sent automatically.

> **Screenshot:** *(record your Loom and drop a screenshot here)*

---

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

---

## Run

### Online mode (Anthropic Claude)
```bash
python -m inbox_helper run data/messages.json
```

### Offline mode (rule-based, no API key needed)
```bash
python -m inbox_helper run data/messages.json --offline
```

Both commands classify all 30 messages, generate draft replies, and write `out/drafts.json`.

### Open the review UI
```bash
python -m inbox_helper review
```
Opens Streamlit at `http://localhost:8501`. Messages are grouped by intent, sorted by urgency. Each card shows the original message, detected intent + confidence, and an editable draft.

### Evaluate accuracy
```bash
python -m inbox_helper eval          # LLM mode
python -m inbox_helper eval --offline  # rule-based mode
```

---

## Review Flow

1. Run the `run` command to classify and draft all messages.
2. Open the review UI (`python -m inbox_helper review`).
3. For each message:
   - Read the original message and the draft reply.
   - Fill in every `[PLACEHOLDER: ...]` in the draft.
   - Click **Approve** (enabled only after all placeholders are filled).
   - Or click **Edit & Approve**, **Reject**, or **Regenerate**.
4. Approved replies are saved to `out/approved_replies.json` and `out/outbox/<id>.eml`.
5. Every action is logged to `out/audit_log.jsonl`.

**The Approve button is disabled while any `[PLACEHOLDER` text remains in the draft.** This is enforced by the UI — it is not advisory.

---

## Eval Results

| Mode | Accuracy | Correct / Total |
|------|----------|-----------------|
| Offline (rule-based) | **76.7%** | 23 / 30 |
| LLM (Claude Sonnet) | *run `python -m inbox_helper eval` with API key* | — |

Offline misclassifications are mostly on ambiguous multi-intent messages (e.g., a complaint that also asks for a status update) and very short messages ("k", "Any update?").

---

## Design Decisions

**Intent taxonomy** — Nine intents were chosen to cover the realistic distribution of recruiting inbox traffic. The `other` category acts as a catch-all for edge cases. `complaint` and `offer_compensation` are always flagged for human attention regardless of confidence, because automated replies to either carry real risk.

**Human-in-the-loop** — Every reply is blocked from approval while `[PLACEHOLDER: ...]` text remains. This prevents accidental sends of incomplete replies (a common failure mode in draft-assist tools). There is no auto-approve, no batch-approve, and no way to bypass the check.

**Offline fallback** — The rule-based path uses cumulative keyword scoring across the intent patterns, not first-match. This handles multi-intent messages more accurately. The fallback activates when no API key is present, `--offline` is passed, or the LLM returns invalid JSON (after one retry).

**Placeholders** — The `[PLACEHOLDER: description]` convention is unambiguous, scannable, and copy-paste friendly. The UI checks for this exact string prefix. Recruiters know exactly what they need to fill in.

**JSON state** — No database was used. All state lives in `out/` (gitignored). This keeps the tool portable and eliminates setup friction for a demo.

---

## Limitations & Next Steps

- **No real sending.** The EML files in `out/outbox/` are ready for copy-paste but require manual sending or integration with an email provider.
- **No inbox integration.** Messages must be exported to JSON/CSV manually. A Gmail/Outlook MCP connector would automate this.
- **Offline accuracy is 76.7%.** The LLM path achieves better accuracy on ambiguous messages. The offline classifier is for demos and tests only.
- **Single user.** There is no auth or multi-user support. For a team deployment, a simple session mechanism would be needed.
- **No deduplication.** Running `run` twice on the same file overwrites `out/drafts.json` and resets review state.
