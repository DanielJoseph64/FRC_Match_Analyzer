# models.py
# Simple classes for the data we're working with.
# Using dataclasses here just so I don't have to write __init__ by hand.

from dataclasses import dataclass
from typing import Optional


@dataclass
class Team:
    team_number: int
    team_name: str
    location: str = ""


@dataclass
class Match:
    match_id: str
    match_type: str = "qualification"
    red_score: int = 0
    blue_score: int = 0


@dataclass
class PerformanceRecord:
    # one row = one team's scouted stats for one match
    match_id: str
    team_number: int
    alliance: str  # "red" or "blue"
    auto_points: int = 0
    teleop_points: int = 0
    endgame_points: int = 0
    fouls: int = 0
    disqualified: bool = False
    performance_id: Optional[int] = None

    @property
    def total_points(self):
        # just adds up the 3 scoring phases
        return self.auto_points + self.teleop_points + self.endgame_points

    def alliance_score(self, match):
        # score of the alliance this team was on
        if self.alliance == "red":
            return match.red_score
        else:
            return match.blue_score

    def opposing_alliance_score(self, match):
        if self.alliance == "red":
            return match.blue_score
        else:
            return match.red_score
