"""Modal deployment of the matchup-summary and waiver-recommendation functions.

Requires a Modal account and a Modal secret named `openrouter` providing
`OPENROUTER_API_KEY` (see docs/decisions/0002-modal-for-batch-functions.md and
0003-openrouter-free-tier-for-llm-inference.md). Not imported by any test -
the summarization/recommendation logic these functions wrap lives in
`backend/matchup_summary.py` and `backend/waiver_recommendations.py`, and is
tested there without needing Modal or a live LLM call.

`matchup_summary_function` and `waiver_recommendation_function` are callable
only via the Modal SDK/CLI. `web` (see docs/decisions/0004-fastapi-for-http-endpoints.md)
exposes the same two operations as HTTP routes a browser `fetch()` can reach,
for the static frontend built in #6.
"""

import dataclasses

import modal

from yahoo_data.parsing import parse_available_players, parse_matchup

from .matchup_summary import summarize_matchup
from .waiver_recommendations import recommend_waivers

app = modal.App("fantasy-research-agent")

# Both functions call OpenRouter over stdlib `urllib`, and parse Yahoo's JSON
# with stdlib `json` - no third-party package needs installing into the
# container beyond the base image. `web` (below) additionally needs FastAPI,
# so it uses `http_image` rather than this one.
image = modal.Image.debian_slim()

# FastAPI is only for the `web` function's HTTP routes - nothing outside the
# Modal container needs it, so it is not in requirements.txt. See ADR 0004.
http_image = image.pip_install("fastapi[standard]")

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


@app.function(image=http_image, secrets=secrets)
@modal.asgi_app()
def web():
    """HTTP-callable counterparts to the two functions above, for the static frontend (#6).

    Mounts a small FastAPI app with two POST routes rather than decorating
    each function as its own web endpoint, so both routes share one CORS
    setup for the browser's preflight `OPTIONS` request - see ADR 0004.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    web_app = FastAPI()
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )

    @web_app.post("/matchup-summary")
    def matchup_summary_endpoint(matchup_payload: dict) -> dict:
        """POST a Yahoo matchup JSON payload; see `matchup_summary_function` for the shape.

        Returns `{"status": "no_matchup"}` for an empty payload, otherwise
        `{"status": "ok", "home_team", "away_team", "home_score",
        "away_score", "summary"}` - the shape
        docs/design/5-matchup-and-waiver-page.md's Matchup Summary section
        renders.
        """
        if not matchup_payload:
            return {"status": "no_matchup"}
        matchup = parse_matchup(matchup_payload)
        return {
            "status": "ok",
            "home_team": matchup.home.team_name,
            "away_team": matchup.away.team_name,
            "home_score": matchup.home.score,
            "away_score": matchup.away.score,
            "summary": summarize_matchup(matchup),
        }

    @web_app.post("/waiver-recommendations")
    def waiver_recommendation_endpoint(available_players_payload: dict) -> dict:
        """POST a Yahoo available-players JSON payload; see `waiver_recommendation_function` for the shape.

        Returns `{"recommendations": [...]}`, each entry shaped like
        `WaiverRecommendation` (player_id, name, position, reason) - an
        empty list is the Waiver Wire section's Empty state.
        """
        players = parse_available_players(available_players_payload)
        recommendations = recommend_waivers(players)
        return {"recommendations": [dataclasses.asdict(r) for r in recommendations]}

    return web_app
