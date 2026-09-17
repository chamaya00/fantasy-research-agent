#!/usr/bin/env python3
"""One-off lookup: print your Yahoo Fantasy Football league key(s) and team key(s).

Needs YAHOO_CLIENT_ID / YAHOO_CLIENT_SECRET / YAHOO_REFRESH_TOKEN in the
environment (see scripts/yahoo_oauth_setup.py) - reuses
`yahoo_data.client.fetch_json`, the one place in this repo that talks to
Yahoo, rather than hand-rolling a second HTTP call.

Calls Yahoo's own "current logged-in user" resource
(/users;use_login=1/games;game_keys=nfl/...), so you never have to guess a
season's numeric NFL game_key or scrape one out of a URL - Yahoo resolves
"nfl" to the current season for you and returns only leagues/teams you're
actually in.

Usage:
    python3 scripts/yahoo_find_keys.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from yahoo_data.client import YahooCredentialsError, fetch_json


def _records_with(obj, marker_key: str) -> list[dict]:
    """Recursively find every dict in Yahoo's nested JSON that has `marker_key`.

    Yahoo's JSON nests each resource under numeric-string index keys and
    wraps repeated fields in lists, but a league/team's own fields (key,
    id, name, ...) are always siblings in one dict - so finding the dict
    that has `marker_key` is enough to read its `name` alongside it.
    """
    records = []
    if isinstance(obj, dict):
        if marker_key in obj:
            records.append(obj)
        for value in obj.values():
            records.extend(_records_with(value, marker_key))
    elif isinstance(obj, list):
        for item in obj:
            records.extend(_records_with(item, marker_key))
    return records


def main() -> None:
    try:
        leagues = fetch_json("/users;use_login=1/games;game_keys=nfl/leagues")
        teams = fetch_json("/users;use_login=1/games;game_keys=nfl/teams")
    except YahooCredentialsError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    league_records = _records_with(leagues, "league_key")
    print("League(s):")
    if not league_records:
        print("  none found - are you in an NFL fantasy league this season?")
    for record in league_records:
        print(f"  {record['league_key']}  ({record.get('name', '?')})")

    team_records = _records_with(teams, "team_key")
    print("\nYour team(s):")
    if not team_records:
        print("  none found - do you manage a team in one of the leagues above?")
    for record in team_records:
        print(f"  {record['team_key']}  ({record.get('name', '?')})")


if __name__ == "__main__":
    main()
