### ADR 0004: Use FastAPI to expose the batch functions as HTTP endpoints

Date: 2026-09-14
Status: accepted

## Context

#6 wires a static frontend (#5) to the two Modal Functions #4 shipped
(`matchup_summary_function`, `waiver_recommendation_function` in
`backend/app.py`). Those functions are `@app.function`-decorated Modal
Functions only - callable from Python via the Modal SDK/CLI
(`modal run backend/app.py::...`), not from a browser `fetch()`. Modal's
supported way to give a function (or a group of them) a real HTTP route is
`@modal.asgi_app()`, mounting a FastAPI application inside the container;
FastAPI is not part of the base `debian_slim` image and has to be installed
into it.

## Decision

Add one more Modal Function, `web` (`backend/app.py`), decorated with
`@modal.asgi_app()`, that builds and returns a small FastAPI `app` with two
routes: `POST /matchup-summary` and `POST /waiver-recommendations`. Each
route wraps the same parsing/summarizing call the corresponding
`@app.function` makes (`parse_matchup` + `summarize_matchup`,
`parse_available_players` + `recommend_waivers`), and returns a JSON shape
the frontend (#6) renders directly - see `docs/design/5-matchup-and-waiver-page.md`
for the states that shape drives. `CORSMiddleware` is attached to the
FastAPI app with `allow_origins=["*"]`, since this is read-only and has no
credentials of its own to leak, and a static frontend hosted on GitHub Pages
(a different origin than `*.modal.run`) needs the preflight `OPTIONS`
request CORS requires to succeed, not just the `POST` itself.

`fastapi[standard]` is added to the container image only
(`image.pip_install("fastapi[standard]")` in `backend/app.py`), not to
`requirements.txt` - nothing outside the Modal container needs to import
FastAPI; `requirements.txt` lists what the *local* environment needs to run
`modal deploy`/`modal run` and `pytest`, and FastAPI is neither.

The original two `@app.function`-decorated functions are unchanged and kept
alongside `web` - the SDK/CLI invocation path #4 already documented still
works exactly as before.

## Consequences

**Same known-untested-here boundary as ADR 0002.** `backend/app.py` is still
not imported by the test suite - `web`'s routes call straight through to
`parse_matchup`/`summarize_matchup` and `parse_available_players`/
`recommend_waivers`, which are tested (with an injected `complete`) in
`tests/test_matchup_summary.py` and `tests/test_waiver_recommendations.py`.
The routes themselves are verified by a documented `curl` against the
deployed endpoint (see `CLAUDE.md`'s Commands section), not by a pytest
test that would need `modal`, `fastapi`, and a live Modal deployment to
import and exercise `backend/app.py` directly.

**The routes take the same payload shape the SDK functions always did** - a
raw Yahoo matchup or available-players JSON dict in the POST body - because
changing that contract is a product decision about where a live Yahoo
payload comes from for a per-request call from a *credential-less* static
page, which neither #4 nor #5 decided and this issue does not decide either
(see the note on this gap in #6's pull request). Today, calling `web`'s
routes for real still requires supplying that payload by hand (e.g. from a
fixture, via `curl`); the frontend built in #6 POSTs an empty body and
therefore always sees the `no_matchup` / empty-list states until that gap
is closed in a follow-up issue.

**Wildcard CORS is scoped to these two read-only routes.** Nothing behind
them accepts a credential from the caller or mutates state, so any origin
being able to call them is a read-only-tool tradeoff, not a widened
capability - but it is worth another look if either route ever grows a
write side effect or a per-caller identity.

## Alternatives rejected

- **`@modal.fastapi_endpoint()` on each function individually** (the
  pattern the two existing `@app.function`s already use as a base).
  Rejected because CORS needs an `OPTIONS` preflight handled for the `POST`
  routes a browser calls, and a FastAPI app with `CORSMiddleware` handles
  that once for every route it mounts; two separately decorated endpoint
  functions would each need their own preflight handling wired by hand.
- **Changing `matchup_summary_function`/`waiver_recommendation_function` to
  fetch Yahoo data themselves** (dropping the payload parameter, calling
  `yahoo_data.client.fetch_json` with a hardcoded league/team key).
  Rejected here as out of scope for #6: no prior issue or ADR names which
  league/team key to hardcode or which Yahoo resource path represents "the
  most recently completed matchup," and deciding that silently, inside a
  frontend/publishing issue, is exactly the kind of product decision the
  house rules reserve for a person. Flagged as a gap for a follow-up issue
  instead.
