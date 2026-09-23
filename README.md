**FRC Match Analysis Tool**
By Daniel Joseph
Eamil: djoseph.6499@gmail.com

This is a little project I built to mess around with Python + SQLite. I'm was on the FRC team in high school and I got interested in scouting data anytime I wasn't working in the pits as the lead mechanic. Scouting happens every match where teams write down how many points each robot scored, and then at the end of the tournament that data gets used to figure out who to pick for your alliance. So I thought it would be a good project to try and build something that does that analysis automatically instead of doing it in a spreadsheet.

It's not a real tool that any team uses, just something I built to practice Python and SQL, and to have something for my portfolio.

**What it does:**

You load in scouting data (either the sample CSV I made up, or add your own matches through the menu), and itwill:
- store everything in a SQLite database
- calculate average points per team (auto, teleop, endgame, total)
- calculate win/loss/tie record and win rate
- let you rank all the teams by whatever stat you want (basically a leaderboard)

Everything runs through a terminal menu, nothing fancy.

**How it's organized:**

```
frc_match_analyzer/
    data/
        sample_matches.csv     <- made up scouting data, 6 teams, 5 matches
    src/
        db.py         <- opens/closes the datbase connection
        models.py      <- Team / Match / PerformanceRecord classes
        queries.py      <- all the actual SQL (insert/fetch stuff)
        analytics.py    <- the averages + win rate + leaderboard math
        main.py         <- the menu you actually run
    tests/
        test_db.py
        test_analytics.py
    schema.sql          <- table definitions
    requirements.txt
    README.md
```

I split it up this way mostly because it got confusing having everything in one file - db stuff in `db.py`, the actual queries in `queries.py`, and then the math/analytics stuff separate so I could test it without needing a real database file every time.

## Setup

```bash
cd frc_match_analyzer
python3 -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
python -m src.main
```

For the first time you run it, pick option 1 from the menu since that sets up the database file and loads in the sample CSV data. After that you can ssearch up teams, see the leaderboard, or add new match entries.

**Running the tests:**

```bash
pytest -v
```

Tests use an in-memory database (`:memory:`) so it doesn't touch the real `frc_scouting.db` file and runs fast. I tried to cover the important edge cases I could think of - like what happens if a team hasn't played any matches yet, what happens on a tie, and what happens if a team gets disqualified (still counts as a loss even if their alliance won on paper, which is how it actually works in FRC).


**Things I learned / notes to self:**

- had to remember that SQLite doesn't enforce foreign keys unless you turn it on with `PRAGMA foreign_keys = ON` every single connection - it doesn't stick automatically, which tripped me up at first
- used `?` placeholders in every query instead of just plugging in the values with an f-string, since apparently that's how you avoid SQL injection
- the win/loss calculation compares your alliance's score to the other alliance's score for that match, not your individual robot's score, since that's actually how you win/lose a match in FRC
- if I keep working on this, next things I'd want to add: actual match schedule import instead of typing entries by hand, maybe a simple win-probability calculator based on alliance combos
