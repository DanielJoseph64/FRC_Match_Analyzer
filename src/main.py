# main.py
# The menu you actually interact with. Run with: python -m src.main

from pathlib import Path
from tabulate import tabulate

from src.db import DatabaseManager
from src.models import Team, Match, PerformanceRecord
from src.queries import (
    fetch_all_teams,
    fetch_team,
    insert_team,
    insert_match,
    insert_performance,
    seed_from_csv,
)
from src.analytics import calculate_team_stats, generate_leaderboard, VALID_LEADERBOARD_METRICS

# figure out where the project folder actually is so this works no matter
# what directory you run it from
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "frc_scouting.db"
SCHEMA_PATH = PROJECT_ROOT / "schema.sql"
SAMPLE_CSV_PATH = PROJECT_ROOT / "data" / "sample_matches.csv"

MENU_TEXT = """
==================================================
   FRC MATCH ANALYSIS TOOL
==================================================
1. Initialize Database & Seed Sample Data
2. View All Registered Teams
3. Search Team & Display Complete Analytics Report
4. Display Tournament Leaderboard
5. Add New Scouting Match Entry
6. Exit
==================================================
"""


def prompt_int(text):
    # keeps asking / returns None on bad input instead of crashing
    raw = input(text).strip()
    try:
        return int(raw)
    except ValueError:
        print(f"  '{raw}' isn't a number.")
        return None


def initialize_database():
    print("\nSetting up database and loading sample data...")
    with DatabaseManager(str(DB_PATH)) as db:
        db.init_db(SCHEMA_PATH)
        seed_from_csv(db, SAMPLE_CSV_PATH)
    print(f"  Done. Database saved to {DB_PATH}\n")


def view_all_teams():
    with DatabaseManager(str(DB_PATH)) as db:
        teams = fetch_all_teams(db)

    if len(teams) == 0:
        print("\nNo teams yet - run option 1 first.\n")
        return

    rows = []
    for t in teams:
        rows.append([t.team_number, t.team_name, t.location])

    print()
    print(tabulate(rows, headers=["Team #", "Name", "Location"], tablefmt="grid"))
    print()


def team_report():
    team_number = prompt_int("\nTeam number to look up: ")
    if team_number is None:
        return

    with DatabaseManager(str(DB_PATH)) as db:
        team = fetch_team(db, team_number)
        if team is None:
            print(f"  No team {team_number} found.\n")
            return
        stats = calculate_team_stats(db, team_number)

    print(f"\n--- Team {team.team_number}: {team.team_name} ---")
    rows = [
        ["Matches Played", stats["matches_played"]],
        ["Avg Auto Pts", stats["avg_auto_points"]],
        ["Avg Teleop Pts", stats["avg_teleop_points"]],
        ["Avg Endgame Pts", stats["avg_endgame_points"]],
        ["Avg Total Pts", stats["avg_total_points"]],
        ["Wins", stats["wins"]],
        ["Losses", stats["losses"]],
        ["Ties", stats["ties"]],
        ["Win Rate %", stats["win_rate"]],
    ]
    print(tabulate(rows, headers=["Stat", "Value"], tablefmt="grid"))
    print()


def leaderboard():
    print(f"\nMetrics you can sort by: {', '.join(sorted(VALID_LEADERBOARD_METRICS))}")
    metric = input("Which one? (enter for avg_total_points): ").strip()
    if metric == "":
        metric = "avg_total_points"

    with DatabaseManager(str(DB_PATH)) as db:
        try:
            board = generate_leaderboard(db, metric)
        except ValueError as e:
            print(f"  {e}\n")
            return

    if len(board) == 0:
        print("\nNothing to rank yet - run option 1 first.\n")
        return

    rows = []
    for row in board:
        rows.append([
            row["rank"], row["team_number"], row["team_name"],
            row["avg_total_points"], row["avg_auto_points"],
            row["avg_teleop_points"], row["win_rate"],
        ])

    print(f"\n--- Leaderboard by {metric} ---")
    print(tabulate(rows, headers=["Rank", "Team #", "Name", "Avg Total", "Avg Auto", "Avg Teleop", "Win %"], tablefmt="grid"))
    print()


def add_scouting_entry():
    print("\n--- New Scouting Entry ---")
    match_id = input("Match ID (e.g. Q6): ").strip()
    if match_id == "":
        print("  Match ID can't be blank.\n")
        return

    team_number = prompt_int("Team number: ")
    if team_number is None:
        return
    team_name = input("Team name: ").strip()

    alliance = input("Alliance (red/blue): ").strip().lower()
    if alliance not in ("red", "blue"):
        print("  Has to be 'red' or 'blue'.\n")
        return

    auto_points = prompt_int("Auto points: ")
    teleop_points = prompt_int("Teleop points: ")
    endgame_points = prompt_int("Endgame points: ")
    fouls = prompt_int("Fouls: ")
    if auto_points is None or teleop_points is None or endgame_points is None or fouls is None:
        print("  Bad input somewhere, not saving this entry.\n")
        return

    dq_input = input("Disqualified? (y/n): ").strip().lower()
    disqualified = dq_input in ("y", "yes")

    red_score = prompt_int("Final red alliance score: ")
    blue_score = prompt_int("Final blue alliance score: ")
    if red_score is None or blue_score is None:
        print("  Bad input somewhere, not saving this entry.\n")
        return

    with DatabaseManager(str(DB_PATH)) as db:
        insert_team(db, Team(team_number, team_name if team_name else f"Team {team_number}"))
        insert_match(db, Match(match_id, red_score=red_score, blue_score=blue_score))
        insert_performance(db, PerformanceRecord(
            match_id=match_id,
            team_number=team_number,
            alliance=alliance,
            auto_points=auto_points,
            teleop_points=teleop_points,
            endgame_points=endgame_points,
            fouls=fouls,
            disqualified=disqualified,
        ))

    print(f"  Saved entry for team {team_number} in {match_id}.\n")


def main():
    if not SCHEMA_PATH.exists():
        print("Can't find schema.sql, something's wrong with the project folder.")
        return

    while True:
        print(MENU_TEXT)
        choice = input("Pick an option (1-6): ").strip()

        if choice == "6":
            print("bye!")
            break
        elif choice == "1":
            initialize_database()
        elif choice == "2":
            view_all_teams()
        elif choice == "3":
            team_report()
        elif choice == "4":
            leaderboard()
        elif choice == "5":
            add_scouting_entry()
        else:
            print("  Not a valid option, try again.\n")


if __name__ == "__main__":
    main()
