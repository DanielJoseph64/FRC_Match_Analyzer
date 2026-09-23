# test_analytics.py
# testing the averages/win-rate/leaderboard math with small made-up
# scenarios I can check by hand

from pathlib import Path
import pytest

from src.db import DatabaseManager
from src.models import Team, Match, PerformanceRecord
from src.queries import insert_team, insert_match, insert_performance
from src.analytics import calculate_team_stats, generate_leaderboard

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"


@pytest.fixture
def db():
    with DatabaseManager(":memory:") as database:
        database.init_db(SCHEMA_PATH)
        yield database


def seed_two_teams(db):
    # team 100 (red) vs team 200 (blue), 2 matches
    # match A: red wins 120-100, match B: blue wins 110-90
    # so both teams end up 1-1
    insert_team(db, Team(100, "Red Robotics"))
    insert_team(db, Team(200, "Blue Bots"))
    insert_match(db, Match("A", red_score=120, blue_score=100))
    insert_match(db, Match("B", red_score=90, blue_score=110))

    insert_performance(db, PerformanceRecord("A", 100, "red", 10, 40, 10))
    insert_performance(db, PerformanceRecord("A", 200, "blue", 12, 35, 8))
    insert_performance(db, PerformanceRecord("B", 100, "red", 8, 30, 5))
    insert_performance(db, PerformanceRecord("B", 200, "blue", 15, 45, 10))
    db.commit()

    # team 100 totals: (10+40+10)=60, (8+30+5)=43 -> avg 51.5
    # team 200 totals: (12+35+8)=55, (15+45+10)=70 -> avg 62.5


def test_no_matches_gives_zeroed_stats(db):
    insert_team(db, Team(999, "Ghost Team"))
    db.commit()
    stats = calculate_team_stats(db, 999)
    assert stats["matches_played"] == 0
    assert stats["avg_total_points"] == 0.0
    assert stats["win_rate"] == 0.0


def test_averages_are_correct(db):
    seed_two_teams(db)
    stats = calculate_team_stats(db, 100)
    assert stats["matches_played"] == 2
    assert stats["avg_auto_points"] == 9.0
    assert stats["avg_teleop_points"] == 35.0
    assert stats["avg_endgame_points"] == 7.5
    assert stats["avg_total_points"] == 51.5


def test_win_loss_and_win_rate(db):
    seed_two_teams(db)
    s100 = calculate_team_stats(db, 100)
    s200 = calculate_team_stats(db, 200)

    assert s100["wins"] == 1
    assert s100["losses"] == 1
    assert s100["win_rate"] == 50.0

    assert s200["wins"] == 1
    assert s200["losses"] == 1
    assert s200["win_rate"] == 50.0


def test_tie_counts_for_both_teams(db):
    insert_team(db, Team(1, "Team One"))
    insert_team(db, Team(2, "Team Two"))
    insert_match(db, Match("T1", red_score=100, blue_score=100))
    insert_performance(db, PerformanceRecord("T1", 1, "red", 10, 10, 10))
    insert_performance(db, PerformanceRecord("T1", 2, "blue", 10, 10, 10))
    db.commit()

    assert calculate_team_stats(db, 1)["ties"] == 1
    assert calculate_team_stats(db, 2)["ties"] == 1


def test_disqualified_counts_as_loss(db):
    # even though the alliance technically won on paper, a DQ'd team should
    # still show up as a loss for that match
    insert_team(db, Team(1, "Team One"))
    insert_match(db, Match("T1", red_score=150, blue_score=100))
    insert_performance(db, PerformanceRecord("T1", 1, "red", 10, 10, 10, disqualified=True))
    db.commit()

    stats = calculate_team_stats(db, 1)
    assert stats["losses"] == 1
    assert stats["wins"] == 0


def test_leaderboard_sorts_by_avg_total_points(db):
    seed_two_teams(db)
    board = generate_leaderboard(db, "avg_total_points")
    team_numbers_in_order = [row["team_number"] for row in board]
    assert team_numbers_in_order == [200, 100]  # 200 has the higher average


def test_leaderboard_sorts_by_win_rate(db):
    insert_team(db, Team(1, "Always Wins"))
    insert_team(db, Team(2, "Always Loses"))
    insert_match(db, Match("M1", red_score=200, blue_score=50))
    insert_performance(db, PerformanceRecord("M1", 1, "red", 20, 20, 20))
    insert_performance(db, PerformanceRecord("M1", 2, "blue", 5, 5, 5))
    db.commit()

    board = generate_leaderboard(db, "win_rate")
    assert board[0]["team_number"] == 1
    assert board[0]["win_rate"] == 100.0


def test_bad_metric_raises_error(db):
    seed_two_teams(db)
    with pytest.raises(ValueError):
        generate_leaderboard(db, "not_a_real_metric")


def test_empty_leaderboard(db):
    assert generate_leaderboard(db) == []
