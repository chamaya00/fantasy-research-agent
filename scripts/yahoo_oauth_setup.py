#!/usr/bin/env python3
"""One-time Yahoo OAuth2 setup.

Walks through Yahoo's authorization-code flow interactively, exchanges the
code for a refresh token, and (optionally) sets YAHOO_CLIENT_ID,
YAHOO_CLIENT_SECRET, and YAHOO_REFRESH_TOKEN as this repo's Actions secrets
via `gh`, which is already authenticated in a GitHub Codespace.

You need a Yahoo app first (https://developer.yahoo.com/apps/create/,
Fantasy Sports - Read permission), with a Redirect URI registered that
matches what you enter below exactly - trailing slash and all.

Picks up YAHOO_CLIENT_ID / YAHOO_CLIENT_SECRET from the environment if
they're already there, and only prompts for whichever is missing. Note:
a repo secret set under Settings -> Secrets and variables -> Actions is
NOT automatically available here - that's a separate store from Settings
-> Secrets and variables -> Codespaces, and only the latter (repo or your
account level) gets injected as an env var into a Codespace terminal, and
only into a Codespace created or rebuilt after the secret was added. If
neither is set that way, this just prompts for them instead - nothing
breaks either way.

The authorization URL, and the credentials/token if they can't be set via
`gh`, are written to text files under scripts/.oauth_output/ (gitignored)
instead of only being printed to the terminal, so you can open and copy
from the Codespaces editor. Offers to delete that directory once you're
done with it - it holds real secrets in plain text until then.

`.devcontainer/devcontainer.json`'s `postAttachCommand` runs this script
(then scripts/yahoo_find_keys.py) every time a Codespace on this repo is
opened, so it's safe to invoke repeatedly: once a run completes
successfully it writes a marker file (`scripts/.yahoo_oauth_done`,
gitignored), and every later run exits immediately instead of
re-prompting - so does one where `YAHOO_REFRESH_TOKEN` is already set
(e.g. as a Codespaces secret), even without that marker, since a fresh
Codespace container never carries it over from a previous one. Either way,
an automatic run never blocks on input. Pass `--force` to go through the
flow again anyway (e.g. the refresh token was revoked or you're switching
Yahoo apps).

Usage:
    python3 scripts/yahoo_oauth_setup.py [--force]
"""

import base64
import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_REDIRECT_URI = "https://chamaya00.github.io/fantasy-research-agent/"
AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
OUTPUT_DIR = Path(__file__).parent / ".oauth_output"
DONE_MARKER = Path(__file__).parent / ".yahoo_oauth_done"


def require(label: str, value: str) -> str:
    if not value:
        print(f"{label} is required.", file=sys.stderr)
        sys.exit(1)
    return value


def get_client_id() -> str:
    value = os.environ.get("YAHOO_CLIENT_ID", "").strip()
    if value:
        print("Using YAHOO_CLIENT_ID from the environment.")
        return value
    return require("Yahoo Client ID", input("Yahoo Client ID: ").strip())


def get_client_secret() -> str:
    value = os.environ.get("YAHOO_CLIENT_SECRET", "").strip()
    if value:
        print("Using YAHOO_CLIENT_SECRET from the environment.")
        return value
    return require(
        "Yahoo Client Secret", getpass.getpass("Yahoo Client Secret (hidden): ").strip()
    )


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
    already_have_token = bool(os.environ.get("YAHOO_REFRESH_TOKEN", "").strip())
    if (DONE_MARKER.exists() or already_have_token) and "--force" not in sys.argv:
        reason = (
            f"{DONE_MARKER} exists"
            if DONE_MARKER.exists()
            else "YAHOO_REFRESH_TOKEN is already set (e.g. as a Codespaces secret)"
        )
        print(
            f"Already completed - {reason}. Re-run with --force if you need a "
            "fresh refresh token (e.g. it was revoked, or you're switching Yahoo "
            "apps)."
        )
        return

    print("Yahoo OAuth2 setup - one-time, run from a terminal you trust.\n")
    print(
        "Note: YAHOO_CLIENT_ID/YAHOO_CLIENT_SECRET are only picked up automatically "
        "if they're set as Codespaces secrets (Settings -> Secrets and variables -> "
        "Codespaces) - Actions secrets are a different store and aren't injected "
        "here. Missing either just means you'll be prompted for it below.\n"
    )

    client_id = get_client_id()
    client_secret = get_client_secret()
    redirect_uri = input(f"Redirect URI [{DEFAULT_REDIRECT_URI}]: ").strip() or DEFAULT_REDIRECT_URI

    auth_params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "language": "en-us",
        }
    )
    auth_url = f"{AUTH_URL}?{auth_params}"

    OUTPUT_DIR.mkdir(exist_ok=True)
    auth_url_file = OUTPUT_DIR / "auth_url.txt"
    auth_url_file.write_text(auth_url + "\n")

    print(f"\n1. Open {auth_url_file} in the Codespaces editor (left file")
    print("   explorer), copy the URL, open it in a new browser tab, log in,")
    print("   and approve.\n")
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
    write_secrets_file = answer != "y"
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
                "access to the repo.",
                file=sys.stderr,
            )
            write_secrets_file = True

    if write_secrets_file:
        credentials_file = OUTPUT_DIR / "credentials.txt"
        credentials_file.write_text(
            "Paste these into "
            "https://github.com/chamaya00/fantasy-research-agent/settings/secrets/actions/new\n"
            "(one secret per submission - the page only takes one at a time)\n\n"
            f"YAHOO_CLIENT_ID={client_id}\n"
            f"YAHOO_CLIENT_SECRET={client_secret}\n"
            f"YAHOO_REFRESH_TOKEN={refresh_token}\n"
        )
        print(f"\nWrote the values to {credentials_file} - open it in the editor and copy each into the repo's secrets page.")

    DONE_MARKER.write_text("Ran successfully - see git history/PR for when. Delete this file to re-run the flow.\n")

    print(
        f"\n{OUTPUT_DIR}/ now holds your client secret and/or refresh token in "
        "plain text. Open whatever you still need to copy from it first."
    )
    cleanup = input("Delete it now? [Y/n]: ").strip().lower()
    if cleanup != "n":
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        print("Deleted.")
    else:
        print(f"Left in place - delete {OUTPUT_DIR}/ yourself once you're done.")


if __name__ == "__main__":
    main()
