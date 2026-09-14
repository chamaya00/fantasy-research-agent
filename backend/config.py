"""Configuration shared by the matchup-summary and waiver-recommendation functions.

The OpenRouter free-model roster churns - see
docs/research/1-llm-inference-approach.md and
docs/decisions/0003-openrouter-free-tier-for-llm-inference.md. `OPENROUTER_MODEL`
is the one place that names a model id; nothing else in this codebase should
hardcode one, so swapping models is a one-line change here (or an environment
variable override) rather than an edit at every call site.
"""

import os

OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
