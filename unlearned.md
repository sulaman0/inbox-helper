# Unlearned: What Working AI-First Changed

*Draft — fill in with your own words before submitting.*

---

## 1. Writing the spec before the code

**Old habit:** Open editor, start typing code, figure out the shape of the problem while writing it.

**What I did instead:** Asked AI to reason through the pydantic schemas and output contracts before any implementation existed. The intent taxonomy, the `needs_human_attention` rule, the placeholder-blocking UI constraint — all defined in the directive first, then built to spec.

**Result:** No schema churn. The models written on day one matched what the UI needed without revision.

**What I'll keep:** Always define the data contracts (schemas, enums, field names) before writing any logic that depends on them.

---

## 2. Generating test data instead of inventing it by hand

**Old habit:** Write three or four minimal fixture objects by hand, declare them "good enough," and move on.

**What I did instead:** Asked AI to generate 30 realistic candidate messages with deliberately tricky cases: multi-intent messages, non-English phrases, near-empty bodies, an angry tone. The edge cases came for free.

**Result:** The offline classifier was tested against real-world messiness from day one, not clean hypotheticals.

**What I'll keep:** Generate sample data at scale and include intentional edge cases. If the data is unrealistic, the eval numbers are meaningless.

---

## 3. Writing tests before the implementation is finished

**Old habit:** Write tests after the code, treating them as a chore rather than a design tool.

**What I did instead:** Defined the test cases (happy path, bad JSON fallback, API error fallback, placeholder detection, confidence clamping) while building the offline path. Tests ran against mocked LLM calls — no network required.

**Result:** Caught three real bugs: an off-by-one in confidence scoring, a case where the fallback wasn't triggered correctly, and a Pydantic validator that wasn't clamping the confidence range.

**What I'll keep:** Write tests that document the contract, not just the implementation. The mock-LLM pattern made the whole test suite network-free.

---

## 4. Reviewing rather than typing

**Old habit:** Write every line myself. AI-generated code = code I don't understand.

**What I did instead:** Let AI generate the boilerplate (Streamlit layout, CLI wiring, .gitignore, Makefile) and focused my attention on reviewing the contracts, edge cases, and the human-review rule.

**Result:** The human-review enforcement (placeholder block + audit log) got more attention than it would have if I'd been heads-down writing Streamlit widgets.

**What I'll keep:** Use AI for the parts that are formulaic; apply my own judgment to the parts that are consequential.

---

## 5. The fallback-first mindset

**Old habit:** Build the happy path, add error handling later (or never).

**What I did instead:** Built the offline (rule-based) path first and made it the fallback for the LLM path. The system degrades gracefully by design rather than by accident.

**Result:** The demo runs without an API key. Tests run without a network. The classifier is never unavailable.

**What I'll keep:** For any AI feature, always ask: "What does this do when the model is unavailable, slow, or returns garbage?" Build that path first.
