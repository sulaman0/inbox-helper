# Loom Demo Script — Inbox Helper (≤5 min)

---

## [0:00–0:20] The problem (20 seconds)

> "Recruiting teams get hundreds of candidate emails a week — status checks, interview reschedules, salary questions, visa inquiries, angry complaints — all mixed together. A recruiter spends an hour a day just triaging and writing almost-identical replies. This tool fixes that."

*Show the `data/messages.json` file briefly — 30 messages visible.*

---

## [0:20–1:05] Run the CLI (45 seconds)

> "One command to process the whole inbox."

```bash
python -m inbox_helper run data/messages.json --offline
```

*Show the terminal output: the intent summary table with counts and urgency.*

> "Every message is classified into one of nine intents — status updates, interview scheduling, compensation questions, and so on. The rule-based classifier runs with no API key. When you have an Anthropic key set, it uses Claude instead and accuracy goes up."

---

## [1:05–3:05] Review UI (2 minutes)

```bash
python -m inbox_helper review
```

*Open `http://localhost:8501`.*

> "The UI groups messages by intent and sorts by urgency. High-urgency items — complaints, compensation questions, withdrawals — appear first."

**Show a complaint message:**
> "This candidate is frustrated. The classifier detected it as a complaint with high urgency and flagged it for human attention. The draft starts with an apology and uses a placeholder for the specific corrective action."

**Show the placeholder block:**
> "Notice the Approve button is disabled — there's a `[PLACEHOLDER: Recruiter name]` still in the draft. I can't approve this until I fill it in."

*Type a recruiter name into the placeholder.*

> "Now the button is enabled. I'll click Approve."

*Click Approve.*

> "The reply is saved to `out/approved_replies.json` and an EML file is written to `out/outbox/`. The action is logged."

**Show a withdrawal message:**
> "Here's a candidate withdrawing. The draft thanks them and wishes them well — it doesn't ask them to reconsider, which is by design. I'll approve this one as-is."

**Show Edit & Approve:**
> "For this status update, the draft is good but I want to add the specific timeline. I'll edit it inline, then click Edit & Approve."

**Show Reject:**
> "This one doesn't need a reply — I'll reject it. It's logged but nothing goes to the outbox."

---

## [3:05–3:50] Eval numbers + offline mode (45 seconds)

```bash
python -m inbox_helper eval --offline
```

*Show the confusion matrix.*

> "76.7% accuracy on 30 labelled messages in offline mode — no API key, fully deterministic. The misses are mostly multi-intent messages and very short ones like a one-character body. With the LLM path enabled, accuracy jumps significantly — I'll run that with the API key set off-screen and you can see the number in the README."

---

## [3:50–4:20] Audit log (30 seconds)

```bash
cat out/audit_log.jsonl | head -10
```

> "Every action is recorded — classified, drafted, approved, edited, rejected, regenerated — with a timestamp and message ID. This gives you a full audit trail of the recruiter's review session."

---

## [4:20–5:00] What I'd do next (40 seconds)

> "Three things I'd add:

> First, a Gmail or Outlook connector so the tool pulls directly from the inbox instead of requiring a JSON export.

> Second, a team mode — right now it's single-user; a small auth layer would let multiple recruiters share the queue.

> Third, fine-tune the classifier on your own inbox data. 76.7% offline accuracy is a demo floor, not a production target. With 200 labelled examples specific to your recruiting workflow, you'd push well past 90%."
