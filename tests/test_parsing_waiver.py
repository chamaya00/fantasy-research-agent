import json
from pathlib import Path

from yahoo_data.parsing import parse_available_players

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "waiver_available_players.json").read_text()
)


def test_available_players_expose_name_position_and_ownership():
    players = parse_available_players(FIXTURE)

    assert len(players) == 2
    by_name = {p.name: p for p in players}

    charbonnet = by_name["Zach Charbonnet"]
    assert charbonnet.position == "RB"
    assert charbonnet.ownership == {"status": "waivers", "percent_owned": "42"}

    warren = by_name["Jaylen Warren"]
    assert warren.position == "RB"
    assert warren.ownership == {"status": "freeagents", "percent_owned": "18"}
