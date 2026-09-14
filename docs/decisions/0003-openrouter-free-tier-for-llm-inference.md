### ADR 0003: Call OpenRouter's free tier for matchup-summary and waiver-recommendation text

Date: 2026-09-14
Status: accepted

## Context

`docs/research/1-llm-inference-approach.md` (#2) compared self-hosting an
open-weight model on Modal's free tier against calling a free model through
OpenRouter, for generating matchup-summary prose and waiver-recommendation
reasons. This ADR records the LLM-inference half of that decision as this
repository's first dependency on OpenRouter; ADR 0002 records the separate
decision to run the calling code on Modal.

## Decision

Call OpenRouter's chat-completions API (`backend/llm.py`, stdlib `urllib`
only - no OpenRouter SDK dependency) using a specific pinned free model,
`nvidia/nemotron-3.5-lightning:free`, rather than an auto-router alias. The
model id is defined in exactly one place, `backend/config.py`'s
`OPENROUTER_MODEL` (overridable via the `OPENROUTER_MODEL` environment
variable) - both `backend/matchup_summary.py` and
`backend/waiver_recommendations.py` reach the model only through
`backend/llm.complete`, never by naming a model id themselves.

## Consequences

**Free-tier limits, from the research this ADR builds on:** `:free`-suffixed
models are rate-limited to 20 requests/minute and a 50-requests/day cap
until the account has purchased $10 of lifetime credit (1,000/day after).
The research estimated 15-25 calls/week for this project's two batches,
comfortably inside either cap.

**Model churn:** the free-model roster is documented to change on
OpenRouter's and upstream providers' own schedule, with no deprecation
notice guaranteed - the research observed the roster itself change between
two queries made minutes apart while it was being written. Pinning the
model id in one config constant (rather than inline at each call site) is
this repository's mitigation: if `nvidia/nemotron-3.5-lightning:free`
disappears or degrades, switching to the research's documented fallbacks
(`nex-agi/nex-n2.5-pro:free` or `inclusionai/ling-3.0-flash-fin:free`) is a
one-line change to `backend/config.py` or an `OPENROUTER_MODEL` environment
variable, not an edit at every call site.

**Data-training tradeoff of `:free` models:** OpenRouter's own documentation
states free models are "usually not suitable for production use," and using
a `:free` model means accepting that some providers may train on the
prompts sent to them (team names, rosters, and matchup data, for this
project), with no way to opt out while staying on the free tier - disabling
that data policy for free traffic leaves no endpoint available. This project
accepts that tradeoff for now because the data involved (fantasy football
team/player stats) is not sensitive, and because the free tier removes any
billing setup; if that changes, ADR 0002's self-hosting option (Modal, a
model this project controls) is the documented alternative.

**Reliability:** the calling code (`backend/matchup_summary.py`,
`backend/waiver_recommendations.py`) takes its OpenRouter call as an
injectable `complete` callable specifically so it can be tested without a
live API call or an `OPENROUTER_API_KEY` - `backend/llm.py`'s real
`complete` function reads that key from the environment at call time, not
at import time, and is never exercised by the test suite.

## Alternatives rejected

- **An auto-router alias** (letting OpenRouter pick among free models per
  request). Rejected per the research's explicit recommendation: a pinned
  model id is a known quantity the backend can build and test against,
  where an alias could silently change output quality or availability
  between calls.
- **Self-hosting an open-weight model on Modal (Option A in the research)**.
  Rejected as the default for the reasons ADR 0002 does not re-litigate: it
  avoids the data-training and model-churn risks above, but costs a serving
  stack (container image, weight loading, cold starts) this project does
  not need to build yet. Revisit if model continuity or prompt privacy
  starts to matter more than that engineering cost, per the research's own
  "single strongest argument against this recommendation."
