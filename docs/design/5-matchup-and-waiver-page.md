# Single-page flow: matchup summary and waiver recommendations

Issue: #5 (child of #1)

This is a personal, single-user, single-league tool. There is one page, no
login, no team or league picker, and no navigation to anywhere else. The page
loads and shows two things: an AI-written summary of the most recently
completed weekly matchup, and a ranked, reasoned waiver-wire pickup list. Both
are fetched from Modal backend functions built in #4 — one function per
section, called independently.

## Flow

1. **User opens the page's URL** (a static site, e.g. GitHub Pages — see
   `docs/decisions/` once #6 lands). There is no login screen and nothing to
   select: the page is bound to one hardcoded league. On load, the page
   immediately fires two independent requests — one to the matchup-summary
   function, one to the waiver-recommendations function — and renders two
   sections stacked vertically: **Matchup Summary** above **Waiver Wire**.
   Matchup Summary is on top because "did I win, and why" is the thing a
   returning user wants first; Waiver Wire is the secondary, planning-ahead
   question.
2. **Both sections show their own Loading state** the instant the page opens,
   before either request resolves. Loading is per-section, not page-wide —
   see "Independence of the two calls" below.
3. **Matchup Summary resolves.** The section replaces its Loading state with:
   the two team names, the final score, and an AI-written prose summary that
   references the actual final score and at least one specific player's
   performance from that matchup. The user can read it; there is nothing else
   to click.
4. **Waiver Wire resolves**, independently of step 3 (it may finish before,
   after, or fail while Matchup Summary succeeds, or vice versa). The section
   replaces its Loading state with a ranked, numbered list of pickup
   candidates. Each row shows the player's name, position, and a one-line
   stated reason for the recommendation, grounded in that player's own data.
   The user can read it; there is nothing else to click.
5. **User is done.** The happy path has no further action — no filters, no
   sort controls, no drill-down. Reading both sections is the entire
   interaction. Getting a new view (e.g. after next week's games complete)
   means reloading the page later; there is no in-page "check again" control
   outside the error-state Retry described below.

## Independence of the two calls

The Matchup Summary and Waiver Wire sections each own one backend call and
never wait on the other:

- They fire in parallel on page load, not sequentially.
- Each section's Loading, Loaded, and Error states are driven only by its own
  request. A slow or failed Waiver Wire call leaves Matchup Summary free to
  finish loading and display normally, and vice versa.
- Each section's Retry (see Error state below) re-fires only that section's
  request. Retrying Waiver Wire never re-fetches or re-renders Matchup
  Summary.
- There is no page-level "everything must be ready" gate. The page is
  interactive and readable as soon as either section resolves, not only once
  both have.

## States

Each of the four states below is scoped to one section (Matchup Summary or
Waiver Wire); both sections implement all four independently, with wording
appropriate to what that section shows.

### Loading

Shown the instant the page opens, replaced the instant that section's request
settles (success or failure). Displays an in-progress indicator and a label
naming what is loading (e.g. "Loading this week's matchup summary…" /
"Loading waiver recommendations…") — not a bare spinner with no label, since
the two sections load independently and a user glancing at the page should be
able to tell which one is still working.

### No matchup has completed yet this week (Matchup Summary only)

The backend call succeeds but reports there is no completed matchup for the
current week (e.g. games are still in progress, or the week hasn't started).
The section shows an explicit message stating that — e.g. "No matchup has
finished yet this week — check back after games wrap up." — never a blank
section, never a leftover spinner, and never the most recent past week's
summary silently substituted in its place.

### Waiver wire is empty (Waiver Wire only)

The backend call succeeds but returns zero recommendations (e.g. no
worthwhile pickups this week). The section shows an explicit message stating
that — e.g. "No waiver-wire pickups worth recommending this week." — never a
blank section and never a leftover spinner.

### A backend call fails

Either function's call errors, times out, or returns a response the page
can't parse. The section shows: a plain-language statement that this section
failed to load (not the raw error), and a **Retry** control that re-fires only
that section's request and returns the section to its Loading state while the
retry is in flight. The section never fabricates a summary or a
recommendation to fill the gap, and never blocks the other section, which
proceeds on its own outcome regardless (per "Independence of the two calls"
above).

Retry is manual (user-clicks-it), not automatic polling or an automatic
retry-with-backoff. The LLM inference behind both functions runs on free-tier
capacity (`docs/research/1-llm-inference-approach.md`, recommending
OpenRouter's free tier, which is rate-limited to 20 requests/minute and a
50–1,000/day cap depending on account age) — automatic retries on a
already-erroring call would spend that shared quota faster, not recover it.

### Not applicable to this page

**Offline**: not specified — this is a read-only page with no offline data to
show; a failed fetch is covered by the Error state above regardless of
whether the cause is the user's network or the backend.
**Post-destructive-action state**: not applicable — the page has no
destructive actions; it only ever reads.

## Components

**Page shell.** Purpose: the single static page itself. Inputs: none — no
route parameters, no query string, no user/session state. States: none of its
own; it always renders both sections below. Must never: render a login
screen, a team/league picker, or any navigation control — there is nowhere
else for this tool to send the user.

**Matchup Summary section.** Purpose: show the AI-written summary of the most
recently completed matchup. Inputs: the matchup-summary function's response
(team names, final score, summary text) or an error/empty signal. States:
Loading, No-matchup-yet, Error, Loaded (as specified above). Must never: show
placeholder or fabricated summary text, invent a score or player performance
not present in the backend's response, or block on the Waiver Wire section's
outcome.

**Waiver Wire section.** Purpose: show the ranked, reasoned pickup list.
Inputs: the waiver-recommendations function's response (an ordered list of
{player name, position, reason}) or an error/empty signal. States: Loading,
Empty, Error, Loaded (as specified above). Must never: show a fabricated
player or a recommendation with no stated reason, reorder or truncate the
list the backend returned, or block on the Matchup Summary section's outcome.

**Retry control.** Purpose: re-fire the owning section's backend call after
that section's Error state. Inputs: a callback bound to one section's fetch,
nothing else. States: default (clickable) and retrying (disabled, showing the
owning section's Loading state) while its request is in flight. Must never:
be shared between sections or re-fire the other section's request.

## Naming

- **Matchup Summary** — the top section, and the noun for its backend call
  ("the matchup-summary function/call").
- **Waiver Wire** — the bottom section, and the noun for its backend call
  ("the waiver-recommendations function/call").
- **Loading**, **Error**, **Loaded** — states shared by both sections.
- **No matchup has completed yet this week** and **Waiver wire is empty** —
  the two section-specific empty states; not called "Empty" generically in
  either copy or code, since the two backends reach this state for different
  reasons and the messages differ.
- **Retry** — the one interactive control on this page.

## Traceability to the parent objective (#1)

Every "what done looks like" bullet from #1 is covered here:

1. *AI-written matchup summary grounded in real data, not placeholder* → Flow
   step 3; Matchup Summary section's Loaded state and "must never" rule.
2. *Ranked waiver list with stated reasons, grounded in real data* → Flow
   step 4; Waiver Wire section's Loaded state and "must never" rule.
3. *Reachable at a URL — static frontend calling Modal backend functions* →
   Flow step 1 (page load fires two backend calls; no local-only step
   anywhere in this spec).
4. *LLM inference on free-tier capacity, no per-call cost* → Error state's
   Retry rationale, which is shaped specifically around the free-tier rate
   limits documented in `docs/research/1-llm-inference-approach.md`.
5. *Personal, single-user, single-league tool, no multi-tenant auth* → Flow
   step 1 and the Page shell component's "must never" rule (no login, no
   picker).

## Open questions

None. Everything above is buildable from the objective (#1) and this issue's
acceptance criteria alone, per this issue's own note that it has no
dependency on the other children.
