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

## The quote (sourced 2026-11-10)

Joe Brady, postgame press conference, Buffalo Bills official YouTube channel,
"Joe Brady Talks Strong Defensive Performance In 23-6 Victory Over The Vikings",
posted 2026-11-09 (https://www.youtube.com/watch?v=_iJkNY7nBwg). Heard by the editor and
matched in the video's auto-captions.

- ~2:58, answering what feels different about the **defense** since the bye: "if you're
  worried about your own stats this game ... we're not going to get the result that we
  want ... you got to be the teammate. Make the play without making the play."
- ~5:53, again about linebacker **Terrel Bernard** (who intercepted Wentz at 4:10 of the
  3rd): "he's making a lot of plays without making the plays."

He said it about the defense, not the offense. Use it for the Buffalo-D-vs-Wentz half of
the post-mortem (0-8 on third down, 3 takeaways, ~-1.0 EPA per Wentz dropback), where the
credit spreads across a unit instead of one stat line. Captions are machine-made: quote
only the two short lines above, checked against the audio.

## Did the program guide the viewer? (the editor's question, 2026-11-10)

**Aim.** Six of eight keys (blitz, play action, red zone, slow start, third down, yards
per play) pointed at Buffalo's offense against Minnesota's defense. That matchup was close
to a draw. The game was decided on the other side: Buffalo's defense against Wentz, a backup
with 48 dropbacks of evidence. It sat in the Bayesian booth but got **no key**. The editor's
own example, "watch his first 5 plays," would have caught it: Wentz was 1 for 5 on his first
five dropbacks (-1.1 EPA each) by early in the 2nd quarter.

**Live reads that misled:** the red-zone rule ("field goals mean Minnesota is winning"),
the fourth-quarter lean (13-6 entering Q4, Buffalo won it 10-0), and the halftime
yards-per-play bar (Buffalo 3.6 against 5.8 said "Minnesota's defense is winning"; it was,
and Minnesota trailed). **Worked:** turnovers (key 6), Minnesota's third downs (0 for 5 at
half), and yards per play as the after-the-game winner check.

**Hindsight trap, caught.** The first story here was "the play count was the tell" (BUF 24,
MIN 8 after one quarter). Over the 2026 season, the halftime play-count leader won only 54%
of one-score games. That is the cherry-pick we warn readers about.

**Halftime gauges, 2026 regular season through week 9 (135 games; 79 within 8 at half):**

| leader at halftime in... | wins, all games | wins, one-score games |
|---|---|---|
| the score | 77% | 75% |
| expected points per play | 72% | 66% |
| yards per play | 70% | 65% |
| plays run | 62% | 54% |
| third-down rate | 61% | 50% |
| turnovers | 55% | 51% |

Nothing beats the score. In one-score games, when yards per play disagrees with the score the
leader still wins 70% (23 games); when it agrees, 78% (45). Expected points: 67% (15) vs 77% (53).
The gauges are tie-breakers, not oracles, and the program should say so.

**Rules for the next program:**
1. Spend keys on uncertainty, not fame. The thinnest evidence (a backup QB, a reshuffled
   line) gets a key with a checkpoint.
2. Every key gets a checkpoint a viewer can count at the bar, and a time to check it.
3. Every checkpoint is backtested on this season before it prints, with its hit rate shown.
   No untested rules.
4. Print the baseline: the halftime score is right about 3 times in 4 in one-score games.
5. At most three keys per matchup; both sides of the ball get keys.
