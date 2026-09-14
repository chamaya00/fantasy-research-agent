"""Turns Yahoo Fantasy Sports API JSON into `yahoo_data.models` objects.

Yahoo's `format=json` responses are XML converted to JSON rather than a
JSON API designed as one: a "collection" (a league's teams, a team's roster,
a list of players) is a dict keyed `"0"`, `"1"`, ... plus a `"count"`, and an
object's own fields (a team, a player) arrive as a list mixing one list of
single-key dicts with further single-key dicts, in no guaranteed order.
`_collection_items` and `_merge_yahoo_object` below undo those two quirks;
everything past them works with plain, flat dicts.
"""

from .models import AvailablePlayer, Matchup, PlayerStatLine, Roster


def _collection_items(collection: dict) -> list:
    count = int(collection["count"])
    return [collection[str(i)] for i in range(count)]


def _merge_yahoo_object(fields: list) -> dict:
    merged: dict = {}
    for item in fields:
        if isinstance(item, list):
            merged.update(_merge_yahoo_object(item))
        elif isinstance(item, dict):
            merged.update(item)
    return merged


def _parse_player(player_payload: list) -> PlayerStatLine:
    merged = _merge_yahoo_object(player_payload)
    stats = {
        entry["stat"]["name"]: entry["stat"]["value"]
        for entry in merged["player_stats"]["stats"]
    }
    return PlayerStatLine(
        player_id=merged["player_id"],
        name=merged["name"]["full"],
        position=merged["display_position"],
        stats=stats,
    )


def _parse_roster(team_payload: list) -> Roster:
    merged = _merge_yahoo_object(team_payload)
    player_entries = _collection_items(merged["roster"]["players"])
    players = [_parse_player(entry["player"]) for entry in player_entries]
    return Roster(
        team_key=merged["team_key"],
        team_name=merged["name"],
        score=float(merged["team_points"]["total"]),
        players=players,
    )


def parse_matchup(payload: dict) -> Matchup:
    """Parse a completed-week matchup response into a `Matchup`.

    `payload` is the parsed JSON body of Yahoo's matchup resource
    (`.../matchup;week=N?format=json`), decoded with `json.load`/`json.loads`.
    """
    matchup = payload["fantasy_content"]["matchup"]
    team_entries = _collection_items(matchup["teams"])
    home, away = (_parse_roster(entry["team"]) for entry in team_entries)
    return Matchup(week=matchup["week"], home=home, away=away)


def parse_available_players(payload: dict) -> list[AvailablePlayer]:
    """Parse a waiver-wire/available-players response into `AvailablePlayer`s.

    `payload` is the parsed JSON body of Yahoo's league players resource
    (`.../league/<league_key>/players;status=A?format=json`), decoded with
    `json.load`/`json.loads`.
    """
    player_entries = _collection_items(payload["fantasy_content"]["league"]["players"])
    players = []
    for entry in player_entries:
        merged = _merge_yahoo_object(entry["player"])
        players.append(
            AvailablePlayer(
                player_id=merged["player_id"],
                name=merged["name"]["full"],
                position=merged["display_position"],
                ownership={
                    "status": merged["ownership"]["ownership_type"],
                    "percent_owned": merged["percent_owned"]["value"],
                },
            )
        )
    return players
