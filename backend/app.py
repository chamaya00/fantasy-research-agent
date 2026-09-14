"""Modal deployment of the matchup-summary and waiver-recommendation functions.

Requires a Modal account and a Modal secret named `openrouter` providing
`OPENROUTER_API_KEY` (see docs/decisions/0002-modal-for-batch-functions.md and
0003-openrouter-free-tier-for-llm-inference.md). Not imported by any test -
the summarization/recommendation logic these functions wrap lives in
`backend/matchup_summary.py` and `backend/waiver_recommendations.py`, and is
tested there without needing Modal or a live LLM call.
"""

import dataclasses

import modal

from yahoo_data.parsing import parse_available_players, parse_matchup

from .matchup_summary import summarize_matchup
from .waiver_recommendations import recommend_waivers

app = modal.App("fantasy-research-agent")

# Both functions call OpenRouter over stdlib `urllib`, and parse Yahoo's JSON
# with stdlib `json` - no third-party package needs installing into the
# container beyond the base image.
image = modal.Image.debian_slim()

secrets = [modal.Secret.from_name("openrouter")]


@app.function(image=image, secrets=secrets)
def matchup_summary_function(matchup_payload: dict) -> str:
    """Parse a Yahoo matchup response and return an AI-written summary."""
    matchup = parse_matchup(matchup_payload)
    return summarize_matchup(matchup)


@app.function(image=image, secrets=secrets)
def waiver_recommendation_function(available_players_payload: dict) -> list[dict]:
    """Parse a Yahoo available-players response and return ranked recommendations."""
    players = parse_available_players(available_players_payload)
    recommendations = recommend_waivers(players)
    return [dataclasses.asdict(recommendation) for recommendation in recommendations]
