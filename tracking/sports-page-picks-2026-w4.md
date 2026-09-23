# Week 4 picks — 2026

Built 2026-09-23, before kickoff. Lines from CFBD, public splits from CBS.
**Re-read every line off CBS before entering.** These were pulled Wednesday for
Saturday games and they will move.

## The sheet

| pts | take | public on our side | game |
|---:|---|---:|---|
| 15 | Old Dominion +6.0 | 11% | James Madison at Old Dominion |
| 14 | Florida -3.0 | 25% | Ole Miss at Florida |
| 13 | Missouri +6.5 | 31% | Missouri at Mississippi State |
| 12 | Maryland +1.5 | 32% | UCLA at Maryland |
| 11 | Oklahoma State +1.8 | 33% | Oklahoma State at West Virginia |
| 10 | Tennessee +4.5 | 37% | Texas at Tennessee |
| 9 | Kansas State -6.2 | 44% | Kansas State at Cincinnati |
| 8 | UCF +3.0 | 45% | TCU at UCF |
| 7 | California +1.2 | 52% | Clemson at California |
| 6 | UConn +3.5 | 55% | UConn at Miami (OH) |
| 5 | Nebraska -5.5 | 57% | Nebraska at Michigan State |
| 4 | USC +3.0 | 57% | Oregon at USC |
| 3 | Iowa +5.5 | 60% | Iowa at Michigan |
| 2 | Georgia Tech -3.5 | 72% | Georgia Tech at Stanford |
| 1 | Army -3.0 | 77% | Army at Temple |

Eight of fifteen are against the public. Average public support on our sides: 46%.

## How the sides were chosen, and what that is worth

Projected margin = `5.1 x (yards-per-play margin difference) - 2.5 home field`,
compared against the spread.

**The 5.1 is the honest coefficient and getting it right mattered.** The first
pass used 8.4, which is what you get regressing a game's final margin on that same
game's yards per play — r = 0.86, and completely useless for forecasting, because
it is measured after the fact. Re-estimated walk-forward across 1,441 games of
2025 and 2026, using only weeks strictly before each game: **1.0 yard per play of
prior margin buys 5.1 points of future margin, r = 0.47, residual SD 18.9 points.**
The descriptive number inflated every disagreement by 1.7x, which is where a
26-point "edge" over the market came from.

**Do not read the model's confidence as confidence.** It has no opponent
adjustment, so three games against soft schedules read as elite — that is open
task C6 in `TASKS.md` and it is not built. `picks_overlay.py` backtested this
information at **50.2% against the spread** over 2,278 games, with the yards-per-
play edge correlating with the spread itself at r = +0.73. The market already
knows. Treat all fifteen as coin flips with a lean.

## Why the ordering is what it is

Given no edge on the sides, the weights are set for differentiation: the least
popular side carries 15. This is the rule sealed on 2026-09-23 under digest
`b78c44f6`, and week 4 grades it.

Simulated at 10 entrants, all picks true coin flips, differing from the room on 8
of 15:

| weighting | mean score | P(win the week) |
|---|---:|---:|
| contrarian-heavy | 59.9 | 22.2% |
| random | 60.1 | 19.4% |
| consensus-heavy | 59.9 | 14.7% |

Mean score is identical by construction — ordering cannot change what you score.
P(win) is not identical, and the gap is large. **This refines what
`pool/how-to-play.html` says.** The guide is right that ordering cannot raise your
expected score; it does not say that ordering still decides who beats you. Put the
big numbers where you differ from the room.

## Leading does not change this

Checked, because it is the obvious objection. Holding a 12-point lead with ten
weeks left, 10 entrants:

| how tightly you track the room | P(finish first) |
|---|---:|
| independent | 28.2% |
| loose | 21.3% |
| tight | 9.8% |
| copy exactly | 3.8% |

A week's score has SD about 18, so over ten weeks the gap between two players
swings by roughly 78 points. A 12-point lead is 0.15 of that — far too small to be
worth protecting. Play for the win, not for the lead.

## The one that is uncomfortable, and why it stays

Old Dominion +6.0 carries 15 points on an edge of -0.3, which is nothing. We have
no read on that game at all; it is there because 89% of the public is on James
Madison and that is the single largest disagreement available. That is the sealed
rule working as designed, and it is exactly the pick that will look stupid if it
loses. It is supposed to be uncomfortable — the whole point of sealing the rule
was to stop us quietly dropping it when it looked bad.
