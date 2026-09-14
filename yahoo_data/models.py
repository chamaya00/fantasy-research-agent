"""Shapes the rest of the app consumes, independent of Yahoo's wire format."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PlayerStatLine:
    player_id: str
    name: str
    position: str
    stats: dict[str, str]


@dataclass(frozen=True)
class Roster:
    team_key: str
    team_name: str
    score: float
    players: list[PlayerStatLine] = field(default_factory=list)


@dataclass(frozen=True)
class Matchup:
    week: str
    home: Roster
    away: Roster


@dataclass(frozen=True)
class AvailablePlayer:
    player_id: str
    name: str
    position: str
    ownership: dict[str, str]
