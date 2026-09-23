# analytics.py
# This is where the actual stats/ranking stuff happens.
# I just pull the raw rows out of the db and do the math in plain python,
# felt easier than trying to do averages/win-rate in SQL directly.

from src.queries import fetch_all_matches, fetch_all_teams, fetch_team_performances

VALID_LEADERBOARD_METRICS = {
    "avg_total_points",
    "avg_auto_points",
    "avg_teleop_points",
    "avg_endgame_points",
    "win_rate",
    "matches_played",
}


def _get_match_result(performance, match):
    # figures out win/loss/tie for one performance record
    # note: getting DQ'd counts as a loss even if your alliance won the match
    if performance.disqualified:
        return "loss"

    my_score = performance.alliance_score(match)
    other_score = performance.opposing_alliance_score(match)

    if my_score > other_score:
        return "win"
    elif my_score < other_score:
        return "loss"
    else:
        return "tie"


def calculate_team_stats(db, team_number):
    performances = fetch_team_performances(db, team_number)
    matches = fetch_all_matches(db)

    # turn matches into a dict so we can look them up by id instead of looping every time
    match_by_id = {}
    for m in matches:
        match_by_id[m.match_id] = m

    matches_played = len(performances)

    if matches_played == 0:
        return {
            "team_number": team_number,
            "matches_played": 0,
            "avg_auto_points": 0.0,
            "avg_teleop_points": 0.0,
            "avg_endgame_points": 0.0,
            "avg_total_points": 0.0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "win_rate": 0.0,
        }

    auto_total = 0
    teleop_total = 0
    endgame_total = 0
    points_total = 0
    wins = 0
    losses = 0
    ties = 0

    for p in performances:
        auto_total += p.auto_points
        teleop_total += p.teleop_points
        endgame_total += p.endgame_points
        points_total += p.total_points

        match = match_by_id.get(p.match_id)
        if match is None:
            continue  # shouldn't really happen but just in case

        result = _get_match_result(p, match)
        if result == "win":
            wins += 1
        elif result == "loss":
            losses += 1
        else:
            ties += 1

    win_rate = round((wins / matches_played) * 100, 2)

    return {
        "team_number": team_number,
        "matches_played": matches_played,
        "avg_auto_points": round(auto_total / matches_played, 2),
        "avg_teleop_points": round(teleop_total / matches_played, 2),
        "avg_endgame_points": round(endgame_total / matches_played, 2),
        "avg_total_points": round(points_total / matches_played, 2),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "win_rate": win_rate,
    }


def generate_leaderboard(db, metric="avg_total_points"):
    if metric not in VALID_LEADERBOARD_METRICS:
        raise ValueError(f"'{metric}' isn't a valid metric. Pick from: {sorted(VALID_LEADERBOARD_METRICS)}")

    teams = fetch_all_teams(db)

    leaderboard = []
    for team in teams:
        stats = calculate_team_stats(db, team.team_number)
        stats["team_name"] = team.team_name
        leaderboard.append(stats)

    # sort highest first
    leaderboard.sort(key=lambda row: row[metric], reverse=True)

    rank = 1
    for row in leaderboard:
        row["rank"] = rank
        rank += 1

    return leaderboard
