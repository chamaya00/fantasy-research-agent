"""Generates a ranked, reasoned waiver-wire pickup list."""

from collections.abc import Callable
from dataclasses import dataclass

from yahoo_data.models import AvailablePlayer

from . import llm


@dataclass(frozen=True)
class WaiverRecommendation:
    player_id: str
    name: str
    position: str
    reason: str


def _percent_owned(player: AvailablePlayer) -> float:
    return float(player.ownership.get("percent_owned", "0"))


def _build_reason_prompt(player: AvailablePlayer) -> str:
    return (
        f"In one sentence, explain why a fantasy football manager should "
        f"consider picking up {player.name} ({player.position}) from waivers, "
        f"given ownership data {player.ownership}."
    )


def recommend_waivers(
    players: list[AvailablePlayer], *, complete: Callable[[str], str] = llm.complete
) -> list[WaiverRecommendation]:
    """Return `players` ranked by ownership percentage, each with a stated reason.

    `complete` defaults to the real OpenRouter call (`backend.llm.complete`);
    tests inject a fake so no live LLM call is required to exercise this
    function's own logic - ranking the real fixture players and building a
    reason prompt grounded in each one's own data.
    """
    ranked = sorted(players, key=_percent_owned, reverse=True)
    return [
        WaiverRecommendation(
            player_id=player.player_id,
            name=player.name,
            position=player.position,
            reason=complete(_build_reason_prompt(player)),
        )
        for player in ranked
    ]
