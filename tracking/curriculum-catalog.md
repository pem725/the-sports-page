# The Curriculum Catalog: procedures and designs, each with a real sports case

Set by the editor, 2026-11-18: *"The Sports Page isn't just about sports. It's about stats."* We want a catalog
of the procedures we can now teach, each shown in use, on data we hold, answering a question a fan would
actually ask. One row = one future issue (or a series), with a concept primer behind it where none exists yet.

Rules that carry over from the rest of the paper: real cases only, never a schematic. Every number traced to a
primary feed. The procedure is never the headline (headline rule 4); the question is. *Data* says where the
numbers come from; *Status* says what is already done.

## Models: what's in a predictor

| Procedure | The fan's question | Data we hold | Status |
|---|---|---|---|
| **Ordinary regression** (what a coefficient means; a predictor's worth *given* the others) | Is yards per play worth anything once you know the score margin? | `data/ypp-ratings.json`, CFBD box scores, nflverse | Ratings live on every game card; no teaching piece. Primer needed: *what's in a predictor* |
| **Logistic regression** (a probability from a line; log-odds) | How safe is a 10-point halftime lead, in the NFL vs. college? | `data/halftime-baselines.json`, nflverse play-by-play | Checkpoint rates are on game cards; the curve itself never shown |
| **Poisson distribution** (counts of rare events) | Is a hat trick or a 1-0 game rarer than it "should" be? | NHL API, every game since 2015 (research/gene-rule) | **Drafted 2026-11-18:** `queue/210-poisson-hockey.html`, code in `research/poisson-hockey/`. Fit within ~1 game in 100; the fit is two departures canceling (trailing teams score 110 per 100; empty-net goals spread it back). Open: 203 eight-goal games vs ~300 owed |
| **Poisson regression** (counts with predictors; exposure as an offset) | Do power plays explain goals, or does ice time? | NHL API boxscores | Not started |
| **Classification and regression trees** | What single question best sorts playoff teams from the rest? | NFL team-seasons 1999-2025 (research/momentum/nfl) | Not started. Pair it with logistic regression: same data, a tree vs. a curve, and the overfitting primer |
| **Data reduction** (factor analysis) | Is "a good hitter" one thing or three? | research/constructs/baseball-hitting | Under way (constructs glossary; primer `constructs-and-indicators`) |
| **Paired comparisons** (Bradley-Terry; Massey's least-squares ratings) | How can a computer rank 136 teams that mostly never meet? | CFBD games 2014-2026 (research/cfp-committee) | Our margin rating already does this (Issue #233); not yet explained as a method |

## Missing data, censoring and time

| Procedure | The fan's question | Data we hold | Status |
|---|---|---|---|
| **Missing data mechanisms** (MCAR, MAR, MNAR) | SMU had no 1987 or 1988 season. How do you rank a program with a hole in it? | Howell scores (every-program.html), CFBD | Not started. **Verify the SMU years in both feeds before writing** |
| **Data deleted, then restored** | Penn State's wins were vacated in 2012 and restored in 2015. Which record do you analyze? | Howell keeps results as played; the NCAA record does not | Not started. Howell's as-played rule is already noted on every-program.html. **Verify the dates** |
| **Censoring and survival** (time to event; still-active cases) | How long does a program take to come back from sanctions? How long does a coach last? | Howell, CFBD coaches | The Half-Life series used survival curves (Gompertz). Right-censoring never named. Primer needed |

## Designs, not just analyses

| Design | The fan's question | Data we hold | Status |
|---|---|---|---|
| **Tournament and schedule design** (round robin vs. single elimination vs. a committee) | Why is the best NFL team obvious by January and the best college team never is? | NFL and CFB schedules; research/cfp-committee/coinflip | Coin-flip piece queued (Fri 11/20). The schedule-graph half (17 games in a 32-team league vs. 12 in a 136-team league) is unwritten |
| **Regression discontinuity** | Does finishing 12th rather than 13th, or 25th rather than 26th, change a program's next year? | CFP rankings 2014-2026 (CFBD); AP votes | Not started. **Check sample size first:** few teams sit right at the line each year |
| **Natural experiments** | Did the 12-team playoff change how teams schedule? | CFBD schedules | Not started |

## Ranked data (the Massey thread)

| Procedure | The fan's question | Data we hold | Status |
|---|---|---|---|
| **Rank agreement** (Spearman, Kendall's tau, Kendall's W) | How much do the computers agree, and when does the agreement break down? | Massey composite (permission requested, see below) | Issue #173 (Oregon) showed the spread informally |
| **Rank aggregation** (Borda, medians, a cumulative index) | Who has been best *all season*, not just this week? | Weekly composite, week 1 onward | Editor's idea: a cumulative index plus each team's high and low |
| **Rater bias** (multilevel model, raters nested in outlets) | Do poll voters rank the teams they cover higher? | AP individual ballots, **availability to verify** | Not started. The committee half is done (Issue #233, "mostly right") |

## Massey: status

2026-11-18: a draft to Kenneth Massey sits in the editor's GMU Outlook for review. It asks (1) for permission
to use the weekly college football composite in non-commercial teaching pieces, with credit, and (2) whether
he would work with us on ranked data. **His terms require written consent to reproduce or redistribute
his content.** The draft discloses that `data/massey-*.json` and `data/rating-snapshots/massey-*.json` are
already in this public repo, and offers to take them down. Until he answers:
- Cite and link his pages as before.
- Add no new Massey files to the repo.
- If he says no, remove the files from the tip of the repo. Note they stay in git history.

## Series: too many variables (for Jeff's methods students)

Editor, 2026-11-18: load a boatload of collinear predictors of win/lose, use the huge sample so every
coefficient is "significant", then show confounders, colliders and reversed arrows with DAGs; retrospective
designs mislead, prospective models are weak because what matters is unobserved; in the end it usually
comes down to one critical variable. First pass: `research/kitchen-sink/1_demo.py` (NFL team-games 1999-2025).

**What the data already shows (13,898 team-games):**
- Plays alone: + (z 15). Add time of possession: plays turns **negative, z −30**. Yards flips sign once
  yards per play enters. Every flip is "significant"; sample size does not rescue a confused model.
- The retrospective box score "explains" 71% of winners with plays + TOP, but the arrow runs backward:
  teams that lead run the ball and the clock. Winning causes possession time.
- Prospective (only what was known before kickoff, week 4 on, fit 1999-2017, tested 2018-2025): season-to-date
  point margin + home = **63%**; all six season-to-date stats = **63%**, with yards and TOP carrying the wrong
  sign. One variable does as well as the kitchen sink.

| Piece | Lesson | Data | Status |
|---|---|---|---|
| The sign that flipped | collinearity; power is not validity | team-games (done above) | Demo done; DAG needed |
| Winning causes time of possession | reversed arrow; retrospective design; the sign flip folded in | team-games, nflverse pbp 2016-25 | **Drafted 2026-11-18:** `queue/211-time-of-possession.html`, DAG from the editor's arrows; Q4 run share 22 (behind 9+) vs 67 (ahead 9+); 36 vs 25 s to next snap; run 4.5 vs pass 6.2 yd |
| The playoff-team collider | conditioning on a common effect (selection) | NFL team-seasons | Not started |
| What the market sees that we don't | unobserved variables; the spread as a benchmark | `research/momentum/nfl/data/games.csv` has spread_line | Not started |
| Last year x decay x P(healthy) | one critical variable for fantasy; QB vs RB year-to-year | nflverse player stats (cached by build_stands_nfl.py) | Not started |
| Hidden form | a true hidden Markov model: team "form" as a latent state week to week | team-games | Idea; check it beats a plain rating before writing |

Traps: the J.J. Watt / Falcons right tackle stance anecdote needs a primary source (the clip or broadcast)
before it is used, and the player is not named until then. Jeff's beat is basketball: a basketball replication
would suit his students; check what box-score data we can get first.
