import json
from pathlib import Path

from backend.matchup_summary import summarize_matchup
from yahoo_data.parsing import parse_matchup

FIXTURE = Path(__file__).parent / "fixtures" / "matchup_completed.json"


def _echo(prompt: str) -> str:
    # Stands in for a live LLM call: an LLM given a prompt grounded in real
    # data would echo that data back in its prose, so echoing the prompt
    # verbatim proves the pipeline (real data in, completion out) without
    # requiring a live OpenRouter call.
    return prompt


def test_summarize_matchup_references_real_scores_and_a_named_player():
    matchup = parse_matchup(json.loads(FIXTURE.read_text()))

    summary = summarize_matchup(matchup, complete=_echo)

    assert "112.4" in summary
    assert "97.8" in summary
    assert "Patrick Mahomes" in summary
