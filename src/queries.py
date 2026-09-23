# queries.py
# All the actual SQL lives here. Using ? placeholders everywhere instead of
# f-strings so we don't open ourselves up to SQL injection.

import csv
from src.models import Team, Match, PerformanceRecord


def insert_team(db, team):
    # OR IGNORE so we don't blow up if the team is already in there
    db.execute(
        "INSERT OR IGNORE INTO teams (team_number, team_name, location) VALUES (?, ?, ?)",
        (team.team_number, team.team_name, team.location),
    )


def insert_match(db, match):
    db.execute(
        "INSERT OR IGNORE INTO matches (match_id, match_type, red_score, blue_score) VALUES (?, ?, ?, ?)",
        (match.match_id, match.match_type, match.red_score, match.blue_score),
    )


def insert_performance(db, performance):
    cursor = db.execute(
        """INSERT INTO match_performances
           (match_id, team_number, alliance, auto_points, teleop_points, endgame_points, fouls, disqualified)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            performance.match_id,
            performance.team_number,
            performance.alliance,
            performance.auto_points,
            performance.teleop_points,
            performance.endgame_points,
            performance.fouls,
            int(performance.disqualified),
        ),
    )
    return cursor.lastrowid


def fetch_team(db, team_number):
    row = db.execute(
        "SELECT team_number, team_name, location FROM teams WHERE team_number = ?",
        (team_number,),
    ).fetchone()
    if row is None:
        return None
    return Team(row["team_number"], row["team_name"], row["location"])


def fetch_all_teams(db):
    rows = db.execute("SELECT team_number, team_name, location FROM teams ORDER BY team_number").fetchall()
    teams = []
    for row in rows:
        teams.append(Team(row["team_number"], row["team_name"], row["location"]))
    return teams


def fetch_match(db, match_id):
    row = db.execute(
        "SELECT match_id, match_type, red_score, blue_score FROM matches WHERE match_id = ?",
        (match_id,),
    ).fetchone()
    if row is None:
        return None
    return Match(row["match_id"], row["match_type"], row["red_score"], row["blue_score"])


def fetch_all_matches(db):
    rows = db.execute("SELECT match_id, match_type, red_score, blue_score FROM matches ORDER BY match_id").fetchall()
    matches = []
    for row in rows:
        matches.append(Match(row["match_id"], row["match_type"], row["red_score"], row["blue_score"]))
    return matches


def fetch_team_performances(db, team_number):
    rows = db.execute(
        """SELECT performance_id, match_id, team_number, alliance, auto_points,
                  teleop_points, endgame_points, fouls, disqualified
           FROM match_performances WHERE team_number = ? ORDER BY match_id""",
        (team_number,),
    ).fetchall()

    results = []
    for row in rows:
        results.append(PerformanceRecord(
            match_id=row["match_id"],
            team_number=row["team_number"],
            alliance=row["alliance"],
            auto_points=row["auto_points"],
            teleop_points=row["teleop_points"],
            endgame_points=row["endgame_points"],
            fouls=row["fouls"],
            disqualified=bool(row["disqualified"]),
            performance_id=row["performance_id"],
        ))
    return results


def fetch_all_performances(db):
    rows = db.execute(
        """SELECT performance_id, match_id, team_number, alliance, auto_points,
                  teleop_points, endgame_points, fouls, disqualified
           FROM match_performances ORDER BY match_id, team_number"""
    ).fetchall()

    results = []
    for row in rows:
        results.append(PerformanceRecord(
            match_id=row["match_id"],
            team_number=row["team_number"],
            alliance=row["alliance"],
            auto_points=row["auto_points"],
            teleop_points=row["teleop_points"],
            endgame_points=row["endgame_points"],
            fouls=row["fouls"],
            disqualified=bool(row["disqualified"]),
            performance_id=row["performance_id"],
        ))
    return results


def seed_from_csv(db, csv_path):
    # reads the sample csv and loads everything into the 3 tables
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = Team(
                team_number=int(row["team_number"]),
                team_name=row["team_name"],
                location=row.get("location", ""),
            )
            insert_team(db, team)

            match = Match(
                match_id=row["match_id"],
                match_type=row.get("match_type", "qualification"),
                red_score=int(row["alliance_red_score"]),
                blue_score=int(row["alliance_blue_score"]),
            )
            insert_match(db, match)

            performance = PerformanceRecord(
                match_id=row["match_id"],
                team_number=int(row["team_number"]),
                alliance=row["alliance"].strip().lower(),
                auto_points=int(row["auto_points"]),
                teleop_points=int(row["teleop_points"]),
                endgame_points=int(row["endgame_points"]),
                fouls=int(row["fouls"]),
                disqualified=row["disqualified"].strip().lower() in ("1", "true", "yes"),
            )
            insert_performance(db, performance)

    db.commit()
