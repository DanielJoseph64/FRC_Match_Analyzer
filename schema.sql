-- schema.sql
-- sets up the 3 tables this project uses:
--   teams              - basic team info
--   matches             - one row per match, final scores
--   match_performances  - one row per team per match (the scouting data)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    team_number INTEGER PRIMARY KEY,
    team_name   TEXT NOT NULL,
    location    TEXT
);

CREATE TABLE IF NOT EXISTS matches (
    match_id    TEXT PRIMARY KEY,
    match_type  TEXT NOT NULL DEFAULT 'qualification',
    red_score   INTEGER NOT NULL DEFAULT 0,
    blue_score  INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS match_performances (
    performance_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id        TEXT NOT NULL,
    team_number     INTEGER NOT NULL,
    alliance        TEXT NOT NULL CHECK (alliance IN ('red', 'blue')),
    auto_points     INTEGER NOT NULL DEFAULT 0,
    teleop_points   INTEGER NOT NULL DEFAULT 0,
    endgame_points  INTEGER NOT NULL DEFAULT 0,
    fouls           INTEGER NOT NULL DEFAULT 0,
    disqualified    BOOLEAN NOT NULL DEFAULT 0,
    FOREIGN KEY (match_id) REFERENCES matches (match_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (team_number) REFERENCES teams (team_number)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- indexes so looking up a team's matches (or a match's teams) isn't a full scan
CREATE INDEX IF NOT EXISTS idx_performances_team ON match_performances (team_number);
CREATE INDEX IF NOT EXISTS idx_performances_match ON match_performances (match_id);
