# Unlearned: What Working AI-First Changed

---

## 1. Writing the spec before the code

For most of my career, I'd open the editor and start typing. The shape of the problem would emerge as I wrote it — which sounds productive but usually meant I'd refactor the data model halfway through once I realized I'd modelled it wrong.

This time I didn't touch implementation until the pydantic schemas were locked. Intent taxonomy, output fields, the `needs_human_attention` rule, the placeholder convention — all defined upfront. By the time I wrote the first function, I already knew exactly what it needed to return.

No schema churn. The models I defined in hour one were the same ones the UI consumed. That's not something I can say about most projects I've built the old way.

---

## 2. Letting AI generate the messy test data

I would normally write three or four minimal fixture objects, call them "representative," and move on. That's what I've done on every project I can remember.

Here I asked for 30 realistic messages with deliberate edge cases — multi-intent, near-empty body, non-English opener, angry tone. I wouldn't have invented those edge cases by hand. I would have discovered them in production.

The offline classifier got tested against real-world messiness from the start. The eval number (76.7%) is honest because the data wasn't clean.

---

## 3. Tests as a design tool, not a chore

I've always written tests after the code. Not because I think that's right — I know TDD exists — but because writing tests first felt slow when I was the one doing all the typing.

When AI is writing the implementation, the tests become the thing I actually control. I wrote the test cases first (happy path, bad JSON fallback, API error, placeholder detection, confidence clamping), then let the implementation be built to satisfy them. Caught three real bugs in the process.

The mock-LLM pattern made the whole suite network-free. That's not an afterthought — it's the reason the tests are actually useful.

---

## 4. Reviewing instead of typing

My default when reading AI-generated code used to be mild suspicion — "I should rewrite this properly." This time I deliberately flipped it: let AI handle the formulaic parts (Streamlit layout, CLI wiring, Makefile), and put my attention on the parts that matter.

The human-review enforcement — placeholder blocking, audit log, no auto-approve path — got more design attention than it would have if I'd been heads-down writing widgets. That's the part that makes this a real tool rather than a demo.

---

## 5. Building the fallback first

Old habit: build the happy path, wire up the API, add error handling when something breaks in staging.

This time the offline rule-based classifier came first. The LLM path was built on top of it, with the offline path as the fallback. The system degrades gracefully by design.

The result: the demo runs without an API key. Tests run without a network. The classifier is never unavailable. That's not something I'd have done naturally — I'd have built the LLM path first because it's the interesting part, and the fallback would have been an afterthought.
