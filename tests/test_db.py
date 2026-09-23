# test_db.py
# testing the db setup + basic insert/fetch stuff using an in-memory db
# so nothing touches an actual file

import sqlite3
from pathlib import Path
import pytest

from src.db import DatabaseManager
from src.models import Team, Match, PerformanceRecord
from src.queries import (
    insert_team, insert_match, insert_performance,
    fetch_team, fetch_all_teams, fetch_all_matches,
    fetch_team_performances, seed_from_csv,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
SAMPLE_CSV_PATH = PROJECT_ROOT / "data" / "sample_matches.csv"


@pytest.fixture
def db():
    # fresh db for every test
    with DatabaseManager(":memory:") as database:
        database.init_db(SCHEMA_PATH)
        yield database


def test_tables_exist(db):
    rows = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = set(r["name"] for r in rows)
    assert "teams" in names
    assert "matches" in names
    assert "match_performances" in names


def test_foreign_key_blocks_bad_insert(db):
    # team_number 9999 doesn't exist, this should fail
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO match_performances (match_id, team_number, alliance, auto_points, teleop_points, endgame_points, fouls, disqualified) VALUES (?,?,?,?,?,?,?,?)",
            ("Q1", 9999, "red", 10, 10, 10, 0, 0),
        )


def test_indexes_exist(db):
    rows = db.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall()
    names = set(r["name"] for r in rows)
    assert "idx_performances_team" in names
    assert "idx_performances_match" in names


def test_insert_and_fetch_team(db):
    insert_team(db, Team(254, "The Cheesy Poofs", "San Jose, CA"))
    db.commit()
    team = fetch_team(db, 254)
    assert team is not None
    assert team.team_name == "The Cheesy Poofs"
    assert team.location == "San Jose, CA"


def test_fetch_missing_team_returns_none(db):
    assert fetch_team(db, 404) is None


def test_inserting_same_team_twice_doesnt_duplicate(db):
    insert_team(db, Team(1114, "Simbotics"))
    insert_team(db, Team(1114, "Simbotics"))
    db.commit()
    teams = fetch_all_teams(db)
    matching = [t for t in teams if t.team_number == 1114]
    assert len(matching) == 1


def test_insert_and_fetch_match(db):
    insert_match(db, Match("Q1", "qualification", 100, 90))
    db.commit()
    matches = fetch_all_matches(db)
    assert len(matches) == 1
    assert matches[0].red_score == 100
    assert matches[0].blue_score == 90


def test_insert_performance(db):
    insert_team(db, Team(5596, "Iron Claw"))
    insert_match(db, Match("Q1", red_score=120, blue_score=100))
    pid = insert_performance(db, PerformanceRecord("Q1", 5596, "red", 10, 40, 15, 1, False))
    db.commit()

    assert pid is not None
    perfs = fetch_team_performances(db, 5596)
    assert len(perfs) == 1
    assert perfs[0].total_points == 65  # 10 + 40 + 15


def test_teams_come_back_sorted(db):
    insert_team(db, Team(2056, "OP Robotics"))
    insert_team(db, Team(254, "The Cheesy Poofs"))
    insert_team(db, Team(1114, "Simbotics"))
    db.commit()
    numbers = [t.team_number for t in fetch_all_teams(db)]
    assert numbers == sorted(numbers)


def test_seed_from_csv(db):
    seed_from_csv(db, SAMPLE_CSV_PATH)

    teams = fetch_all_teams(db)
    matches = fetch_all_matches(db)
    assert len(teams) == 6
    assert len(matches) == 5

    team_254 = fetch_team(db, 254)
    assert team_254.team_name == "The Cheesy Poofs"

    perfs = fetch_team_performances(db, 254)
    assert len(perfs) == 5
