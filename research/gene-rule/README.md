# Gene's Rule, tested (2026-11-13)

**The rule (Gene's, all of it):** you can tell a good team by how swiftly and surely it
answers after the other side scores. A team that follows the opponent's score with a score
of its own is a **Gene team**.

**The editor's generalization:** the same thing should show up in other sports: hockey
(the Rangers in their good years jumped right back), baseball (the '86 Mets, the 2024 Mets).

## The question, made testable

1. Do teams score more often right after being scored on than they do otherwise? (Is there
   an *answer effect* at all?)
2. Do teams that answer more often win more often? (Is a Gene team a good team?)
3. Is answering its own skill, separate from just being able to score? If so, a team's
   **answer premium** (answer rate minus its scoring rate the rest of the time) should
   predict winning and should repeat from one year to the next.
4. Does the answer rate forecast the rest of a season any better than point differential?

## Definitions

| sport | a chance | answered | fair comparison |
|---|---|---|---|
| NFL | the drive right after the other team's touchdown (offense, defense or return), same half, 2+ minutes left | drive ends in TD or FG | the same team's other drives that began with a kickoff (same field position) |
| MLB | the half-inning right after the other team scores | 1+ runs | the same team's other half-innings |
| NHL | every goal against | the next goal is ours (and within 5 minutes) | the next goal after our own goal; goals-for share |

## What we found

| | NFL (1999 to Nov 12, 2026) | MLB (1977–2025) | NHL (2015–16 to date) |
|---|---|---|---|
| right after they score | 33 per 100 drives score | 28 per 100 half-innings | next goal ours 41 per 100 |
| fair comparison | 34 (other kickoff drives) | 28 | 42 (after our own goal) |
| answer rate vs winning, team-season | r = .45 | .40 | .83 |
| ordinary scoring vs winning | .61 | .53 | GF% .96 |
| answer premium vs winning | −.01 | −.02 | −.21 |
| answer premium, year to year | .01 | .01 | .04 |

- **There is no answer effect.** In all three sports, a team scores right after being scored
  on at the same rate it scores the rest of the time. In the NFL, same game and same
  opponent: 34 versus 35 per 100.
- **Gene teams are good teams**, because answering is scoring and good teams score.
- **Answering is not a separate skill.** The premium is unrelated to winning and does not
  repeat (year-to-year r ≈ 0 in every sport).
- **Forecasting (NFL):** from weeks 1–9, point differential explains 22% of the spread in
  weeks 10+ win%; answer rate 5%; adding answer rate to point differential adds 0.3 points.
- **The fan's version (NFL):** when the opponent scores the game's first TD, the team that
  answers on its next drive wins 42 of 100; the team that does not, 27. Answer with a TD and
  it is 48 of 100: a tied game.
- **2026 (through Nov 12):** six Gene teams (answered half or more of 15+ chances): BUF
  12/17 (7–1), CIN 9/15 (6–2), DET 12/22 (6–2), DAL 15/23 (4–5), HOU 10/16 (3–5), LV 16/28
  (4–5). Not Gene teams: CHI 6/18 (7–2), SF 4/15 (7–1), JAX 3/11 (6–2). ESPN drive charts
  agree with nflverse within one drive for every team; records checked against ESPN
  standings and `check_scores.py`.
- **'86 Mets:** answered in 29 of 100 half-innings; scored in 29 of 100 others. The 2024
  Mets answered 23 of 100, *below* their usual 28. What fans remember from 2024 is
  comebacks, which is a different stat (late innings, from behind) and a good next test.
- **Rangers 2022–23:** got the next goal after 113 of 216 goals against (52 per 100), among
  the decade's best, with a 56% goals-for share. Goals checked against the NHL and ESPN
  standings (277–219 official; 273–216 here, because shootout goals are left out).

## Limits

- An answer drive is usually played from behind; trailing teams play differently. Not
  adjusted. In hockey that should *help* answering (trailing teams outshoot), and still no
  answer effect shows up.
- Nine weeks is a small sample: 15–28 chances per team. Treat the 2026 list as a snapshot.

## The Rangers point: power play and penalty kill (2026-11-13, `2_nhl_special.py`)

The editor's memory: Rangers teams that answered "took opportunities when they came", so
they were good on the power play, and "surprisingly" stingy on the penalty kill too.
344 team-seasons, 2015-16 to 2025-26. Special teams come from the NHL stats API.
Power-play goals counted from the play-by-play agree with the API (r = .99, average gap
1.3 goals a season).

- **Good at both is barely more common than chance.** PP% and PK% correlate .17. Thirteen
  of every 100 team-seasons are in the top third on both, against 11 by chance.
- **Answering teams do have better special teams** (answer rate vs PP% .52, vs PK% .35),
  but so does any team that outscores people (GF% vs PP% .55, vs PK% .50). Hold GF% fixed
  and answering vs PP% drops to .11, and answering vs PK% turns slightly negative (−.15).
- **One small real lean:** answer goals come on the power play a little more often than
  goals in general (21 vs 20 per 100; 33,884 answer goals, about 5 standard errors). That
  is a nudge, not a trait.
- **Year to year:** PP% .37, PK% .26, answer rate .38, GF% .55.
- **The Rangers he remembers were real.** 2023-24 (Presidents' Trophy): PP #3, PK #3,
  answer rate #6 of 32. 2021-22: PP #4, PK #7. 2022-23: answer #3, PP #7, PK #13. But
  2024-25 had the 28th-ranked power play, and 2025-26 ranked 25th in answering with the 5th-best power play.
  The good years had all three because they were good years.

## Next tests (not done)
- **Comebacks, not answers:** win probability from behind late (the 2024 Mets).
- **College football** via CFBD drives (watch the quota).

## Files

`0_nfl_drives.py` (nflverse pbp → one row per drive), `0_mlb_lines.py` (Retrosheet line
scores), `0_nhl_goals.py` (NHL API, needs a User-Agent header or it returns 403),
`1_nfl.py`, `2_nfl_game_and_2026.py`, `3_verify_espn.py`, `1_mlb.py`, `1_nhl.py`,
`4_build_piece.py` (writes `queue/203-genes-rule.html` from the result files).

Retrosheet notice: The information used here was obtained free of charge from and is
copyrighted by Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.
