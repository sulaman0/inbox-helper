# Directive: Inbox Helper

## Goals

Build a local Python tool that helps a recruiting team triage candidate emails. The tool must:

1. Load a pile of candidate messages from a JSON or CSV file.
2. Classify each message into a fixed intent taxonomy, returning structured output with confidence, urgency, and a human-attention flag.
3. Generate a short (≤ 90 words) reply draft for each message, using `[PLACEHOLDER: ...]` for anything requiring human judgment.
4. Present drafts for human review in a Streamlit UI before any reply is considered "sent." **Nothing is ever sent automatically.**
5. Write approved replies to `out/approved_replies.json` and EML files in `out/outbox/`.
6. Maintain an append-only audit log of every action.
7. Support both LLM mode (Anthropic Claude via API) and offline mode (rule-based, no network required).

## Constraints

- Python 3.11+, no database, JSON files for state.
- LLM: Anthropic Claude (`anthropic` SDK), model from env `LLM_MODEL`, API key from `ANTHROPIC_API_KEY`.
- Offline fallback when no key is set or `--offline` is passed.
- Structured LLM output: request JSON, validate with pydantic, retry once on failure, then fall back to offline.
- Tests: `pytest`, LLM always mocked, tests run with no network.

## Human-in-the-Loop Rule (Non-Negotiable)

The Approve button in the UI is disabled while any `[PLACEHOLDER: ...]` text remains in the reply draft. The recruiter must fill in every placeholder before the reply can be approved. No reply ever reaches `out/approved_replies.json` without an explicit human click.

## Intent Taxonomy

```
status_update | interview_scheduling | offer_compensation | documents
withdrawal    | role_question        | relocation_visa    | complaint | other
```

## Output Schemas

### Classification
```json
{
  "intent": "<taxonomy value>",
  "secondary_intent": "<taxonomy value or null>",
  "confidence": 0.0–1.0,
  "urgency": "low | med | high",
  "summary": "one sentence ≤15 words",
  "needs_human_attention": true/false
}
```

`needs_human_attention = true` if: confidence < 0.6, or intent is `complaint`, `offer_compensation`, or `withdrawal`.

### Draft
```json
{
  "message_id": "...",
  "draft": "≤90 word reply text",
  "classification": { <Classification> },
  "generated_by": "llm | offline"
}
```

### AuditEntry
```json
{
  "timestamp": "ISO-8601Z",
  "message_id": "...",
  "action": "classified | drafted | approved | edited | rejected | regenerated | flagged",
  "detail": "optional string"
}
```

## Prompts

**Classification prompt** (`prompts/classify.md`): asks Claude to return JSON matching the Classification schema. No prose, no markdown fences. Provides the full taxonomy and urgency rules inline.

**Reply prompt** (`prompts/reply_guidelines.md`): per-intent guidelines (90 words max, use placeholders, never invent facts, end with sign-off placeholder).

## Revisions

| # | What changed | Why |
|---|-------------|-----|
| 1 | Added `secondary_intent` to classification schema | Multi-intent messages (visa + salary, scheduling + status) are common in recruiting inboxes; surfacing the secondary intent helps the recruiter respond more completely |
| 2 | Offline classifier uses cumulative pattern scoring rather than first-match | First-match produced wrong results on messages with strong keywords from two intent categories |
| 3 | Approval button blocked while `[PLACEHOLDER]` text remains | Early version would have let reviewers approve drafts with unfilled placeholders — a likely real-world error |
| 4 | Added `--offline` flag in addition to key-absence detection | Evaluators and demos need to run without a key; explicit flag also aids testing |
| 5 | LLM draft prompt wraps `reply_guidelines.md` content rather than repeating it inline | Keeps the prompt maintainable and lets guidelines evolve without touching code |
