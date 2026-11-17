# Day 1 — Build Session

**Date:** 2024-11-17

## Goal
Build the full Inbox Helper from scratch: offline classifier, LLM path, CLI, Streamlit review UI, sample data, tests, and all quest documents.

## What I asked AI to do
1. Plan the full project structure and pydantic schemas before writing any code.
2. Build the offline rule-based classifier and reply templates first (so tests could run offline).
3. Build the LLM path with pydantic validation and retry-then-fallback logic.
4. Generate 30 realistic candidate messages with edge cases (multi-intent, angry, near-empty, non-English phrase).
5. Write the full pytest suite with mocked LLM calls.
6. Build the Streamlit review UI with approval blocking on `[PLACEHOLDER]` text.
7. Write all quest documents (intent.md, directive.md, unlearned.md, day logs, Loom script, career outline).

## What AI did
- Defined all pydantic schemas upfront (Message, Classification, Draft, ReviewedDraft, AuditEntry) before any implementation.
- Built the full offline.py with cumulative keyword scoring (not first-match, which was initially tried and caused wrong results on multi-intent messages).
- Built classify.py and draft.py as thin dispatchers that route between LLM and offline paths.
- Generated 30 messages covering all intent categories including 3 edge cases (msg_028: near-empty "k", msg_020: French opener, msg_029: 4-part multi-intent).
- Implemented placeholder-blocking in Streamlit: approve button disabled while `[PLACEHOLDER` text remains.
- Wrote 30+ tests across test_classify.py, test_draft.py, test_review_rules.py — all LLM calls mocked.

## What I verified or corrected
- Caught a bug in the offline classifier: first-match logic gave wrong results on messages containing both salary and visa keywords. Fixed by switching to cumulative pattern scoring.
- Added `secondary_intent` to handle multi-intent messages — was missing from initial schema draft.
- Strengthened the approval UI: initially the block was advisory only; changed it to `disabled=True` on the button.
- Confirmed tests run with no network required.

## Time spent
~3 hours (AI-assisted full build)

## Next
- Record Loom demo (5 min)
- Fill in personal sections of unlearned.md
- Run eval with LLM mode (requires API key)
- Push to GitHub
