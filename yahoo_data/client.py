"""The single entry point for talking to the real Yahoo Fantasy Sports API.

Nothing else in this codebase should call Yahoo directly or handle OAuth -
`fetch_json` is it. Everything upstream (`yahoo_data.parsing`, and whatever
summarization/recommendation logic consumes it later) works against the
plain dicts this returns, the same shape as a fixture loaded with
`json.load`, so a real credential can be dropped in later without callers
changing.

Credentials come from three environment variables, obtained once via
Yahoo's OAuth2 authorization-code flow out of band (a Yahoo Developer App
does not exist yet, so this path is untested against the real API):

- `YAHOO_CLIENT_ID`
- `YAHOO_CLIENT_SECRET`
- `YAHOO_REFRESH_TOKEN`

Uses only the standard library (`urllib.request` for HTTP) - no Yahoo SDK
or third-party HTTP client.
"""

import base64
import json
import os
import urllib.error
import urllib.parse
import urllib.request

TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
API_BASE = "https://fantasysports.yahooapis.com/fantasy/v2"

_REQUIRED_ENV_VARS = ("YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET", "YAHOO_REFRESH_TOKEN")


class YahooCredentialsError(RuntimeError):
    """Raised when a required Yahoo OAuth environment variable is missing."""


def _get_access_token() -> str:
    missing = [name for name in _REQUIRED_ENV_VARS if not os.environ.get(name)]
    if missing:
        raise YahooCredentialsError(
            "Missing environment variable(s) required to call the real "
            f"Yahoo API: {', '.join(missing)}"
        )
    client_id = os.environ["YAHOO_CLIENT_ID"]
    client_secret = os.environ["YAHOO_CLIENT_SECRET"]
    refresh_token = os.environ["YAHOO_REFRESH_TOKEN"]

    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh_token}
    ).encode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)["access_token"]


def fetch_json(resource_path: str) -> dict:
    """Call a Yahoo Fantasy Sports resource and return its parsed JSON body.

    `resource_path` is a Yahoo Fantasy resource path, e.g.
    "/team/<team_key>/matchups" or "/league/<league_key>/players;status=A".
    Raises `YahooCredentialsError` before making any network call if the
    required environment variables are not set.
    """
    token = _get_access_token()
    request = urllib.request.Request(
        f"{API_BASE}{resource_path}?format=json",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)
