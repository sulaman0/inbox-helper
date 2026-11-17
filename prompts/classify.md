# Classification Prompt

## Intent Taxonomy

| Intent | Description |
|--------|-------------|
| `status_update` | Candidate asking for news, following up, checking where they stand |
| `interview_scheduling` | Scheduling, confirming, rescheduling, or cancelling an interview |
| `offer_compensation` | Questions about salary, equity, signing bonus, benefits, offer letter details |
| `documents` | Submitting CV/resume, references, certificates, background check forms |
| `withdrawal` | Pulling out of the process, no longer interested, accepted another offer |
| `role_question` | Questions about the role, team, tech stack, day-to-day responsibilities |
| `relocation_visa` | Visa sponsorship, work permit, relocation support, international move |
| `complaint` | Expressing frustration, anger, dissatisfaction with the process |
| `other` | Anything that doesn't clearly fit the above categories |

## Confidence Guidelines

- **0.9–1.0**: Single, unambiguous intent with strong keywords
- **0.7–0.89**: Clear primary intent, possibly minor secondary signals
- **0.5–0.69**: Multiple intents present or ambiguous wording
- **Below 0.5**: Very short message, non-English, or genuinely unclear

## Urgency Rules

- **high**: complaints, withdrawals, compensation negotiations, messages mentioning "urgent", "ASAP", "deadline"
- **med**: interview scheduling, visa/relocation questions
- **low**: general status checks, role questions, document submissions

## needs_human_attention = true when:
- confidence < 0.6
- intent is `complaint`, `offer_compensation`, or `withdrawal`
