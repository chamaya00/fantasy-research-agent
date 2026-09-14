import json
from pathlib import Path

from backend.waiver_recommendations import recommend_waivers
from yahoo_data.parsing import parse_available_players

FIXTURE = Path(__file__).parent / "fixtures" / "waiver_available_players.json"


def _echo(prompt: str) -> str:
    # Stands in for a live LLM call: echoing the (player-specific) prompt
    # verbatim proves each reason is grounded in that player's own data
    # without requiring a live OpenRouter call.
    return prompt


def test_recommend_waivers_ranks_and_grounds_each_reason_in_fixture_data():
    players = parse_available_players(json.loads(FIXTURE.read_text()))
    fixture_names = {player.name for player in players}

    recommendations = recommend_waivers(players, complete=_echo)

    assert [r.name for r in recommendations] == ["Zach Charbonnet", "Jaylen Warren"]
    for recommendation in recommendations:
        assert recommendation.name in fixture_names
        assert recommendation.reason.strip() != ""
        assert recommendation.name in recommendation.reason


def test_recommend_waivers_returns_empty_list_for_no_candidates():
    assert recommend_waivers([], complete=_echo) == []
