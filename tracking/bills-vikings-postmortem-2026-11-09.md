# Bills at Vikings, Mon 2026-11-09: graded (for the Nov 15 Sunday Edition)

Final **BUF 23, MIN 6**, confirmed on ESPN (event 401873051) and nflverse games.csv.
Seal verified: vault sha256 matches b065f9c0... in tracking/sealed/.

| sealed call | grade |
|---|---|
| Editor: the offense (Buffalo) wins | HIT |
| Our model: MIN 23, BUF 22 | MISS (wrong winner, 17 points of margin) |
| Meet in the middle: BUF < 33 and MIN allows > 13 | HIT (BUF scored 23, the history's exact average) |
| Two-looks test (fixed before kickoff) | UNCLEAR: elite-offense rematch change -2.3 (se 1.6, n=90) vs control -0.2 (se 0.2, 2,960 pairs); diff -2.2, z -1.4 |

History of No. 1 offense vs No. 1 defense now: offense 19, defense 20; since 2010, 9-7.

**The miss to own:** the program framed BUF O vs MIN D, and Minnesota won that matchup
(BUF 4.3 yards/play vs a 5.8 bar; Allen 0.0 EPA/dropback, INT to Murphy). The game was
decided by BUF D vs Wentz: 8/25, 81 yds, 2 INT, rating 8.9, about -1.0 EPA/dropback. The
booth's default (2-in-3 Wentz better than Murray, on 48 dropbacks) was too generous.
MIN 0-8 on third down, 178 yards, 3 turnovers.

Keys: 1-2 (blitz, play action) await FTN charting (not posted 11-10). 3 red zone: BUF
1-3 (ESPN), Minnesota held, but "field goals mean Minnesota is winning" was wrong.
4 slow start: BUF -0.53 EPA/play first 15 snaps, but led 3-0 after Q1. 5 fourth quarter:
MISS, 13-6 entering Q4 and BUF won it 10-0. 6 turnovers: Murphy INT, then a Wentz fumble
(reversed on BUF challenge) 16 seconds later; BUF +2. 7 third down: BUF 7-18, MIN 0-8.
8 yards per play: higher-YPP team won (4.3 vs 3.9); the 5.8 projection was well off.

Code: scratchpad twolooks.py (control = every other same-season pair; pair = unit).
