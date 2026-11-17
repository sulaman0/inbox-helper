# Career Video Outline — ≤5 Minutes

*Fill in the bracketed sections with your own words before recording.*

---

## [0:00–1:00] Career Path (1 minute)

> "I'm [your name], a full-stack and AI engineer with 8 years of production experience. I've shipped backend systems in Go and Node.js, built Python ML pipelines, and for the last [X] years I've been working as an AI Application Engineer — building LLM systems, RAG pipelines, and multi-agent workflows."

> "I also freelance building AI features into SaaS products. Most recently I shipped [brief description of Shopify AI app — 1–2 sentences about what it does and what it taught you]."

> "[Add anything specific about your current role or team — what kind of problems you're solving day-to-day.]"

---

## [1:00–2:30] Career Leverage (1.5 minutes)

> "The thing I keep coming back to is the gap between what AI can do in a lab demo and what it actually takes to put it in front of users who depend on it."

> "[Pick one or two of these to expand on with a real story from your work:]"

- "The hardest part isn't the model — it's the scaffolding: validation, fallbacks, audit trails, human-in-the-loop controls."
- "RAG systems fail in predictable ways when you don't control the retrieval quality. I've learned to design for retrieval failure first."
- "LLM output is probabilistic. The only way to ship confidently is to define what 'good enough' means before you build, not after."
- "Agent orchestration is mostly prompt engineering + error handling. The interesting problems are in the edges."

> "[Add your own framing for what makes you different from someone who just calls an API and ships it.]"

---

## [2:30–4:00] Quest Connection (1.5 minutes)

> "This quest is called 'Unlearn, Use, Raise the Load' — the evaluators want to see how I work with AI, not just what I know."

> "The tool I built is an Inbox Helper for recruiting teams. The core insight was: the hard part isn't the classification — it's making sure the AI can't do anything irreversible without a human in the loop."

> "[Walk through one specific decision you made while building it, and why:]"

- "I built the offline fallback first — before the LLM path — because I wanted the system to degrade gracefully, not fail catastrophically."
- "The placeholder-blocking rule in the review UI came from thinking about what goes wrong in production: a recruiter approves a draft that still says `[PLACEHOLDER: salary figure]`. That's a real incident waiting to happen."
- "The eval harness runs against labelled data with no network required, so accuracy isn't a vibe — it's a number I can track."

> "[Reflect on what changed in how you work:]"

> "What I unlearned: the instinct to type first. I wrote the data contracts before any code, generated the sample data instead of inventing three fixtures, and treated the review step as the product — not the classifier."

---

## [4:00–5:00] Close (1 minute)

> "[What you're looking for in your next role — be specific. Connect it to what you built here if you can.]"

> "If this resonates with how your team builds, I'd love to talk. [Your contact / GitHub / LinkedIn.]"
