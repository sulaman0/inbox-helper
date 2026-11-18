# Day 2

**Date:** [fill in]

## Goal
Test the full flow end-to-end, run LLM eval with real API key, record the Loom demo.

## What I did
- Ran `python -m inbox_helper run data/messages.json --offline` and walked through the output
- Opened the Streamlit review UI, tested approve / edit & approve / reject / regenerate on several messages
- Verified the placeholder block works — Approve button stays disabled until all `[PLACEHOLDER]` text is filled
- Checked `out/approved_replies.json` and `out/outbox/` EML files after approvals
- Ran `python -m inbox_helper eval --offline` — confirmed 76.7% accuracy (23/30)
- Ran `python -m inbox_helper eval` with real `ANTHROPIC_API_KEY` set — [fill in LLM accuracy number]
- Updated README eval table with LLM accuracy result
- Recorded Loom demo (5 min) using `docs/loom_script.md` as the script

## What I verified or corrected
- [Note anything that looked wrong or needed a fix during testing]
- [Note anything that felt awkward on camera and how you adjusted the script]

## Time spent
~[X] hours

## Next
- Push to GitHub
- Submit
