# LLM inference approach for matchup summaries and waiver recommendations

Issue: #2 (child of #1)

**Decision this research serves:** should AI-generated matchup summaries and
waiver-wire recommendations run on a model self-hosted on Modal's free tier,
or on a model called through OpenRouter's free tier, as the default to build
the backend child against?

## Options

### Option A: Self-host an open-weight model on Modal (free tier)

What it does: you package an open-weight model (e.g. Llama 3.1 8B Instruct,
Mistral 7B) into a Modal Function running on a GPU, and call that Function
from the backend instead of a third-party inference API. Modal is
infrastructure-as-code for running containers, not an inference API itself,
so "the model" is whatever weights you choose to deploy.

**Cost.** Modal's free ("Starter") plan grants **$30/month of free compute
credit**, usable against the same metered GPU/CPU/memory pricing as paid
plans, with **100 containers and 10 GPU-container concurrency** as the plan's
concurrency ceiling, 5 deployed crons, and 1-day log retention
([modal.com/pricing](https://modal.com/pricing)). GPU compute is billed per
second: T4 at **$0.000164/s** ($0.59/hr), L4 at **$0.000222/s** ($0.80/hr),
A10 at **$0.000306/s** ($1.10/hr), A100 40GB at **$0.000583/s** ($2.10/hr)
([modal.com/pricing](https://modal.com/pricing)). Modal bills only while a
container is running, not while idle
([modal.com/pricing](https://modal.com/pricing)), so a workload that runs
twice a week and scales to zero between calls stays a small fraction of the
$30 credit — see Constraints below for the estimate. Running the same GPU
*continuously* (kept warm, no scale-to-zero) would blow through the credit
in days (T4 continuous ≈ $425/month), so the free tier only works for this
use case if the deployment scales to zero between the two weekly batches.

**Latency.** Modal's own guidance is that a cold container "can range from
seconds to minutes" to become ready, that plain container boot is about one
second, and that pre-downloading model weights (rather than fetching them at
boot) "can reduce boot times from minutes to seconds" for models in the tens
of gigabytes, with memory snapshots offered as a further mitigation
([modal.com/docs/guide/cold-start](https://modal.com/docs/guide/cold-start)).
Modal does not publish a concrete seconds figure for loading an LLM-sized
model onto a GPU and serving a first token — that number is specific to the
model, quantization, and serving framework chosen, and is not knowable from
documentation alone (see Constraints/verification below). Because this
workload is two scheduled batches a week rather than a live user-facing
request, a cold start of tens of seconds is tolerable if the batch job is
allowed to wait for it; it would not be for an interactive feature.

**Output quality.** Not fixed by the platform — quality is entirely a
function of which open-weight model you choose to deploy and how you
quantize it to fit the GPU you can afford. This is a real degree of freedom
Option A has that Option B doesn't (you can swap models freely), but it also
means quality is an engineering decision this document can't make for you:
an 8B-class open model is a reasonable default for the free-tier compute
above, and it is a materially weaker writer than the larger models available
free through Option B.

**Reliability.** You own the serving stack: container image, model
download/caching, request handling, and retries are all code you write and
operate. Modal's platform-level rate limit for a new workspace is 200
Function calls or HTTP requests per second
([modal.com/docs/guide/webhooks](https://modal.com/docs/guide/webhooks)),
far above what this workload needs, so the ceiling here is engineering
effort, not quota. There is no external provider that can silently remove
"the model" out from under you, in contrast with Option B — but there is
also no one else keeping the serving code working.

### Option B: Call a free model through OpenRouter

What it does: OpenRouter is a hosted API that proxies requests to many
providers' models over one interface; models with an id ending `:free` are
served at no cost, subject to platform-wide rate limits.

**Cost.** $0 in direct spend. No payment method or account tier is required
to reach the base free-tier rate limit.

**Latency.** OpenRouter does not publish a latency/throughput SLA for free
variants. Its own provider-routing documentation offers a `:nitro` suffix
and a `sort: "throughput"` option specifically to prioritize speed
([openrouter.ai/docs/guides/routing/provider-selection](https://openrouter.ai/docs/guides/routing/provider-selection)),
which implies default (non-nitro) routing, and free variants in particular,
are not tuned for lowest latency — free requests share capacity with every
other free user of that provider slot, with no throughput guarantee. For a
weekly batch job this is a tolerable trade-off; it would not be for a
synchronous user-facing request.

**Output quality.** No fixed answer — the free roster is large (OpenRouter's
free-models collection currently lists on the order of 15+ models, including
NVIDIA Nemotron 3 Ultra at 1M context and several 250K+ context models from
NVIDIA, inclusionAI, Poolside, Cohere, Nex AGI, and Thinking Machines;
[openrouter.ai/collections/free-models](https://openrouter.ai/collections/free-models))
and **it churns**: models are added and removed by OpenRouter and upstream
providers on their own schedule, with no deprecation notice guaranteed to
you. Whichever model you pick today is not guaranteed to be free, or to
exist, in three months.

**Reliability.** OpenRouter's own documentation states free models "usually
[are] not suitable for production use"
([openrouter.ai/docs/faq](https://openrouter.ai/docs/faq)). Rate limits for
`:free`-suffixed models are **20 requests/minute**, plus a per-day cap of
**50 requests/day** until the account has purchased at least $10 of credit
lifetime, after which the cap rises to **1,000 requests/day**
([openrouter.ai/docs/api-reference/limits](https://openrouter.ai/docs/api-reference/limits)).
There is a data-handling trade-off tied to "free": OpenRouter lets you
disable routing to providers that may train on your data, separately for
paid and free traffic, but disabling it for free traffic leaves "no
endpoints available matching your ... data policy" for `:free` models
([support article title, OpenRouter Help Center: "Why do all free models
return a 404: 'No endpoints available matching your guardrail restrictions
and data policy'"](https://openrouter.zendesk.com/hc/en-us/articles/51690904755227) —
fetched via search snippet only, page itself returned HTTP 403 to automated
fetch; a human should open this link directly to confirm before relying on
it). In practice this means using free models means accepting that at least
some providers may train on the prompts you send them, which for this
project would include team names, rosters, and matchup data.

## Constraints

This tool runs one weekly matchup-summary batch and one weekly
waiver-recommendation batch, for a single league. Estimating generously —
a matchup batch making one call per matchup (a single league is typically
5–6 matchups/week) and a waiver batch making one call per candidate
recommendation (order 10–15 free agents considered) — puts weekly volume at
roughly **15–25 LLM calls/week**, each with an estimated 500–1,500 input
tokens (stats, projections, recent news) and 200–500 output tokens (the
generated summary or recommendation text). That's on the order of
**15,000–40,000 tokens/week**.

Checked against OpenRouter's free-tier quota (Option B): even at the
unfunded-account floor of 50 requests/day (350/week), 15–25 calls/week uses
under 10% of the daily cap on any single day it runs, and sits comfortably
under the 20-requests/minute ceiling since nothing about this workload
requires concurrent requests. **This usage fits inside OpenRouter's free
quota with wide headroom**, on either the 50/day or 1,000/day tier.

Checked against Modal's free credit (Option A): 15–25 calls/week against a
GPU billed per second of *actual compute time* (not per call) means the
relevant cost driver is total GPU-seconds per week, not call count. Two
batch jobs a week, each running for the duration of a cold start plus
generation — plausibly a few minutes of GPU time per batch even including a
cold start — comes to roughly 10–20 GPU-minutes/week. At the A10 rate
($0.000306/s ≈ $1.10/hr), that's under $0.40/week, well inside the
$30/month credit. **This usage also fits inside Modal's free credit**, with
far more headroom than the concurrency/container caps would ever bind on
this workload. Cost is not the differentiator between the two options here;
engineering effort, latency behavior, and reliability are.

## Recommendation

**Default to Option B: OpenRouter's free tier**, calling a specific pinned
free model rather than an auto-router alias, so the backend child can build
against one known model id. As of this research (queried directly against
`https://openrouter.ai/api/v1/models`, OpenRouter's public model list),
recommend **`nvidia/nemotron-3.5-lightning:free`** (1,000,000-token context)
as the model to build against, with a fallback to another free entry from
the same API response — e.g. `nex-agi/nex-n2.5-pro:free` or
`inclusionai/ling-3.0-flash-fin:free` (both 262,144-token context) — if
Nemotron 3.5 Lightning's availability or latency proves unworkable in the
backend child's own spike. Building a one-line-swap model id into the
backend (config, not code, per call) is cheap insurance against the free
roster's churn noted above; the free-model roster returned by that same API
endpoint changed between two queries made minutes apart while writing this
document, which is itself evidence of the churn this recommendation warns
about.

**The single strongest argument against this recommendation:** OpenRouter's
own documentation says free models are "usually not suitable for production
use," the specific free model available today is not guaranteed to still be
free — or to exist — by the time the backend child ships, and using it means
accepting that some providers may train on this project's prompt data with
no way to opt out while staying on the free tier. Option A (Modal) avoids
all three of those risks — you control the model, it doesn't disappear, and
nothing you send it leaves your own account — at the cost of building and
maintaining a small serving stack (container image, weight loading, cold
starts) for a workload of two batches a week. If model continuity or data
privacy for prompts turns out to matter more than the engineering cost of
self-hosting, Option A is the correct default instead, and this
recommendation should be revisited.

## Verification

Neither a Yahoo Developer App nor a Modal account exists yet. A Yahoo
Developer App is not relevant to this decision at all — it gates access to
Yahoo's fantasy data API, which is a separate concern (pulling stats/rosters)
from which LLM inference approach generates text from that data, and no
claim in this document depends on it.

A Modal account **is** relevant if Option A is later chosen: the cold-start
timing, actual first-token latency for a specific model/quantization/GPU
combination, and real observed cost per batch are not stated anywhere in
Modal's public documentation with concrete numbers — they can only be
measured by deploying something, which requires an account. Every claim
about Option A above that has a concrete number (pricing, credit, concurrency
caps, the general shape of cold-start behavior) is sourced from Modal's
public docs and needs no account to verify; the specific latency this
project would actually see for a chosen model does need one, as a follow-up
spike, if Option A is ever picked over Option B.

Option B needs no account-creation approval process — an OpenRouter API key
is free and self-serve — so its rate limits and free-model roster can be, and
were, verified from public documentation and the live models page alone,
without signing up.
