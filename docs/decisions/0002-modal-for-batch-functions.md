### ADR 0002: Use Modal to host the matchup-summary and waiver-recommendation functions

Date: 2026-09-14
Status: accepted

## Context

#4 needs somewhere to run two batch functions - one that generates a
matchup-summary, one that generates waiver recommendations - that a static
frontend (#5) can call over HTTP. `docs/research/1-llm-inference-approach.md`
(#2) compared self-hosting an open-weight model on Modal against calling a
free model through OpenRouter, and recommended OpenRouter for the *inference*
call. That research leaves open where the two functions themselves - the
code that fetches Yahoo data, builds a prompt, and calls whichever inference
approach is chosen - run. This ADR is that separate decision, and it is this
repository's first dependency on Modal.

## Decision

Host `matchup_summary_function` and `waiver_recommendation_function`
(`backend/app.py`) as Modal Functions, deployed with `modal deploy
backend/app.py`. Modal is infrastructure-as-code for running containers on
demand; it is not the inference provider here (OpenRouter is, per ADR 0003) -
Modal just runs the Python that calls OpenRouter, on a schedule or on
request, without the project needing to operate its own always-on server for
what is, per the research, two batches a week.

## Consequences

**Free-tier limits, from the research this ADR builds on:** Modal's free
("Starter") plan grants $30/month of compute credit, 100 containers and 10
GPU-container concurrency, 5 deployed crons, and 1-day log retention. Neither
function needs a GPU (the GPU estimates in the research were for Option A,
self-hosting a model; these functions only call OpenRouter's API and do
CPU-only parsing/prompt-building), so the relevant ceiling is CPU-container
concurrency and the 5-cron limit - both far above what two weekly batches
need. 1-day log retention means a failed run's logs must be read within a
day of the run, not retroactively investigated weeks later.

This adds a real, non-stdlib dependency (`modal`, in `requirements.txt`) to a
repository whose Yahoo data layer is deliberately stdlib-only - `backend/`
is a different layer with a different constraint, and this dependency is
confined to it. Deploying requires a Modal account and API token, and a
Modal secret named `openrouter` holding `OPENROUTER_API_KEY` (see ADR 0003);
neither exists in this build/test environment, which is why
`backend/matchup_summary.py` and `backend/waiver_recommendations.py` take an
injectable `complete` callable and are tested against that injection,
never against `backend/app.py`'s Modal-decorated functions directly.

## Alternatives rejected

- **A conventional always-on server** (e.g. a small Flask/FastAPI app on a
  free-tier host). Would need to be kept warm and paid for (or slept and
  cold-started) regardless of whether either batch has run recently; Modal's
  scale-to-zero billing matches a twice-a-week workload better than a
  process that exists whether or not it's doing anything.
- **Running the two functions as scheduled GitHub Actions jobs**, writing
  their output to a file the static frontend fetches. Rejected because #5's
  design spec calls each function synchronously per page load (independent
  per-section fetches with their own Loading/Error states), not from a
  pre-computed file on a schedule; that shape needs an HTTP-callable
  function, which a GitHub Actions job is not.
