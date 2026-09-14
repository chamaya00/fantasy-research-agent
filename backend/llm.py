"""Minimal OpenRouter chat-completions client, stdlib only.

Only imported for its `complete` function, which the two batch functions in
`backend/matchup_summary.py` and `backend/waiver_recommendations.py` use as
their default completion callable. Tests never call this - they inject a
fake in its place - so nothing here runs, and no API key is required, when
the test suite runs.
"""

import json
import os
import urllib.request

from .config import OPENROUTER_MODEL

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class LLMError(RuntimeError):
    """Raised when OpenRouter returns a response `complete` can't use."""


def complete(prompt: str) -> str:
    """Send `prompt` to the configured OpenRouter model and return its reply text.

    Reads the API key from `OPENROUTER_API_KEY` at call time, not import
    time, so importing this module never requires credentials.
    """
    api_key = os.environ["OPENROUTER_API_KEY"]
    body = json.dumps(
        {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    request = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        payload = json.load(response)
    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"unexpected OpenRouter response shape: {payload!r}") from exc
