# Intent: Inbox Helper

## The Problem

A recruiting team receives hundreds of candidate emails every week. These arrive in a shared inbox with no structure: status checks, interview reschedule requests, salary questions, document submissions, visa inquiries, and the occasional angry complaint — all jumbled together. A recruiter spends 60–90 minutes a day just triaging and writing almost-identical replies.

## Who It's For

A recruiter (or recruiting coordinator) who is drowning in candidate email and needs to respond promptly without each reply requiring full concentration. The tool surfaces the signal — what does this person want? how urgent is it? — and drafts the first version of a reply so the recruiter can focus on editing and approving rather than composing from scratch.

## What "Done" Looks Like

1. A recruiter drops a JSON (or CSV) export of their inbox into the tool and runs one command.
2. Every message is classified into a known intent with a confidence score.
3. A short, polite reply draft is generated for each message, with `[PLACEHOLDER: ...]` markers for anything that requires a human judgment call (dates, offer numbers, decisions).
4. The recruiter opens a browser UI, sees messages grouped by intent and sorted by urgency, reads each draft, edits it if needed, and clicks Approve or Reject.
5. Approved replies are written to `out/approved_replies.json` and EML files in `out/outbox/` — ready for copy-paste or future inbox integration.
6. Every action is recorded in an append-only audit log.

## Non-Goals

- **No auto-send.** Nothing is ever sent automatically. Every reply requires a human approval click.
- **No inbox integration.** The tool reads exported files; it does not connect to Gmail, Outlook, or any email provider.
- **No candidate database.** Messages are processed in memory; there is no persistent candidate record.
- **No authentication layer.** This is a local demo tool, not a multi-user SaaS product.

## Success Criteria

| Criterion | Target |
|-----------|--------|
| Classification accuracy (offline mode) | ≥ 75% on 30-message test set |
| Classification accuracy (LLM mode) | ≥ 90% on 30-message test set |
| Every draft reviewed before output | Enforced by UI (approve button blocked while `[PLACEHOLDER]` text remains) |
| Demo completable | ≤ 5 minutes end-to-end |
| Tests pass without network | Yes — LLM is mocked in all tests |
| `--offline` mode fully functional | Yes |
