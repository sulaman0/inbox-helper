# Day 2

**Date:** 2026-11-18

## Goal
Test the full flow end-to-end, run LLM eval with real API key, record the Loom demo.

## What I did
- Ran `python -m inbox_helper run data/messages.json --offline` and walked through the output
- Opened the Streamlit review UI, tested approve / edit & approve / reject / regenerate on several messages
- Verified the placeholder block works — Approve button stays disabled until all `[PLACEHOLDER]` text is filled
- Checked `out/approved_replies.json` and `out/outbox/` EML files after approvals
- Ran `python -m inbox_helper eval --offline` — confirmed 76.7% accuracy (23/30)
- Ran `python -m inbox_helper eval` with real `ANTHROPIC_API_KEY` — LLM mode accuracy to be updated in README
- Recorded Loom demo (5 min) using `docs/loom_script.md` as the script

## What I verified or corrected
- Streamlit was initially launching with system Python instead of venv — fixed by running via `.venv/bin/python -m streamlit run`
- Placeholder blocking confirmed working in UI before approval

## Time spent
~2 hours

## Next
- Push to GitHub
- Submit
