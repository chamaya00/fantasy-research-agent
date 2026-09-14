"""Generates an AI-written summary of a completed fantasy matchup."""

from collections.abc import Callable

from yahoo_data.models import Matchup, Roster

from . import llm


def _describe_roster(roster: Roster) -> str:
    performances = ", ".join(
        f"{player.name} ({player.position}): "
        + ", ".join(f"{stat} {value}" for stat, value in player.stats.items())
        for player in roster.players
    )
    return f"{roster.team_name} scored {roster.score}. Player performances: {performances}."


def _build_prompt(matchup: Matchup) -> str:
    return (
        f"Write a short recap of a fantasy football matchup for week {matchup.week}.\n"
        f"{_describe_roster(matchup.home)}\n"
        f"{_describe_roster(matchup.away)}\n"
        "Reference the final scores and at least one specific player's stat line."
    )


def summarize_matchup(matchup: Matchup, *, complete: Callable[[str], str] = llm.complete) -> str:
    """Return an AI-written prose summary of `matchup`.

    `complete` defaults to the real OpenRouter call (`backend.llm.complete`);
    tests inject a fake so no live LLM call is required to exercise this
    function's own logic - building a prompt grounded in the matchup's real
    scores and player stat lines, and returning the completion unmodified.
    """
    return complete(_build_prompt(matchup))
