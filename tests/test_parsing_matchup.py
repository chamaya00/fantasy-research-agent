import json
from pathlib import Path

from yahoo_data.parsing import parse_matchup

FIXTURE = json.loads(
    (Path(__file__).parent / "fixtures" / "matchup_completed.json").read_text()
)


def test_matchup_exposes_both_teams_scores():
    matchup = parse_matchup(FIXTURE)

    assert matchup.week == "5"
    assert matchup.home.team_name == "Gridiron Gurus"
    assert matchup.home.score == 112.4
    assert matchup.away.team_name == "Couch Commanders"
    assert matchup.away.score == 97.8


def test_matchup_exposes_player_level_stat_lines():
    matchup = parse_matchup(FIXTURE)

    home_players = {p.name: p for p in matchup.home.players}
    assert set(home_players) == {"Patrick Mahomes", "Travis Kelce"}

    mahomes = home_players["Patrick Mahomes"]
    assert mahomes.position == "QB"
    assert mahomes.stats == {"Passing Yards": "315", "Passing Touchdowns": "3"}

    away_players = {p.name: p for p in matchup.away.players}
    allen = away_players["Josh Allen"]
    assert allen.position == "QB"
    assert allen.stats == {"Passing Yards": "245", "Passing Touchdowns": "1"}
