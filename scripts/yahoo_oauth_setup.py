#!/usr/bin/env python3
"""One-time Yahoo OAuth2 setup.

Walks through Yahoo's authorization-code flow interactively, exchanges the
code for a refresh token, and (optionally) sets YAHOO_CLIENT_ID,
YAHOO_CLIENT_SECRET, and YAHOO_REFRESH_TOKEN as this repo's Actions secrets
via `gh`, which is already authenticated in a GitHub Codespace.

You need a Yahoo app first (https://developer.yahoo.com/apps/create/,
Fantasy Sports - Read permission), with a Redirect URI registered that
matches what you enter below exactly - trailing slash and all.

Nothing typed here is written to disk. If you'd rather set the secrets by
hand, decline the prompt at the end and copy the printed refresh token into
https://github.com/chamaya00/fantasy-research-agent/settings/secrets/actions/new
yourself.

Usage:
    python3 scripts/yahoo_oauth_setup.py
"""

import base64
import getpass
import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_REDIRECT_URI = "https://chamaya00.github.io/fantasy-research-agent/"
AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"


def require(label: str, value: str) -> str:
    if not value:
        print(f"{label} is required.", file=sys.stderr)
        sys.exit(1)
    return value


def exchange_code(client_id: str, client_secret: str, redirect_uri: str, code: str) -> dict:
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
            "code": code,
        }
    ).encode()
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = urllib.request.Request(
        TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {basic_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        print(f"\nToken exchange failed: HTTP {exc.code}", file=sys.stderr)
        print(exc.read().decode(errors="replace"), file=sys.stderr)
        sys.exit(1)


def set_secret(name: str, value: str) -> bool:
    result = subprocess.run(
        ["gh", "secret", "set", name, "--body", value],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Could not set {name}: {result.stderr.strip()}", file=sys.stderr)
    return result.returncode == 0


def main() -> None:
    print("Yahoo OAuth2 setup - one-time, run from a terminal you trust.\n")

    client_id = require("Yahoo Client ID", input("Yahoo Client ID: ").strip())
    client_secret = require(
        "Yahoo Client Secret", getpass.getpass("Yahoo Client Secret (hidden): ").strip()
    )
    redirect_uri = input(f"Redirect URI [{DEFAULT_REDIRECT_URI}]: ").strip() or DEFAULT_REDIRECT_URI

    auth_params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "language": "en-us",
        }
    )
    print("\n1. Open this URL, log in, and approve the app:\n")
    print(f"   {AUTH_URL}?{auth_params}\n")
    print(
        "2. Yahoo redirects you back to the redirect URI above with a\n"
        "   `?code=...` query parameter. The page itself may just show the\n"
        "   normal app - that's fine, nothing on it reads the parameter.\n"
        "   Copy the code value out of the address bar.\n"
    )

    code = require("code", input("Paste the code: ").strip())

    tokens = exchange_code(client_id, client_secret, redirect_uri, code)
    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print("\nNo refresh_token in the response:", file=sys.stderr)
        print(json.dumps(tokens, indent=2), file=sys.stderr)
        sys.exit(1)

    print("\nGot a refresh token.")

    answer = (
        input(
            "\nSet YAHOO_CLIENT_ID, YAHOO_CLIENT_SECRET, and YAHOO_REFRESH_TOKEN as this "
            "repo's secrets now, via `gh`? [y/N]: "
        )
        .strip()
        .lower()
    )
    if answer == "y":
        ok = True
        ok &= set_secret("YAHOO_CLIENT_ID", client_id)
        ok &= set_secret("YAHOO_CLIENT_SECRET", client_secret)
        ok &= set_secret("YAHOO_REFRESH_TOKEN", refresh_token)
        if ok:
            print("All three secrets set.")
        else:
            print(
                "\nAt least one secret could not be set automatically - gh may need "
                "`gh auth refresh --scopes admin:repo_hook` first, or you may lack admin "
                "access to the repo. Set the failed one(s) by hand at "
                "https://github.com/chamaya00/fantasy-research-agent/settings/secrets/actions",
                file=sys.stderr,
            )
            print(f"\nRefresh token, in case you need to paste it yourself:\n{refresh_token}")
    else:
        print(
            "\nSet these three repo secrets by hand at "
            "https://github.com/chamaya00/fantasy-research-agent/settings/secrets/actions/new :\n"
            f"  YAHOO_CLIENT_ID       = {client_id}\n"
            "  YAHOO_CLIENT_SECRET   = (the one you typed - not re-printed here)\n"
            f"  YAHOO_REFRESH_TOKEN   = {refresh_token}"
        )


if __name__ == "__main__":
    main()
