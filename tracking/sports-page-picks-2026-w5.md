# Week 5 picks — 2026

Built 2026-09-29, before kickoff. Lines and public splits read off the live CBS
card; yards-per-play margins computed from weeks 1&ndash;4 via CFBD.
**Re-read every line before entering.** These were pulled Tuesday for a card that
starts Thursday.

## The sheet

| pts | take | public on our side | game |
|---:|---|---:|---|
| 15 | MISSOURI +5.5 | 15% | FLORIDA at MISSOURI |
| 14 | NAVY +2.5 | 18% | NAVY at AIR FORCE |
| 13 | FRESNO ST. +2.5 | 37% | FRESNO ST. at WASHINGTON ST. |
| 12 | IOWA ST. -3.5 | 38% | WEST VIRGINIA at IOWA ST. |
| 11 | MINNESOTA +5.5 | 43% | MICHIGAN at MINNESOTA |
| 10 | PITTSBURGH +3.5 | 44% | PITTSBURGH at VIRGINIA TECH |
| 9 | UNLV -2.5 | 48% | CALIFORNIA at UNLV |
| 8 | ARIZONA ST. -3.5 | 58% | BAYLOR at ARIZONA ST. |
| 7 | PENN STATE -2.5 | 60% | PENN STATE at NORTHWESTERN |
| 6 | VIRGINIA -2.5 | 63% | VIRGINIA at FLORIDA STATE |
| 5 | TULSA -0.5 | 65% | NORTH TEXAS at TULSA |
| 4 | NEW MEXICO ST. -1.5 | 69% | W. KENTUCKY at NEW MEXICO ST. |
| 3 | KENTUCKY +3.5 | 78% | KENTUCKY at SOUTH CAROLINA |
| 2 | BYU -6.5 | 87% | BYU at TCU |
| 1 | UMASS -4.5 | 92% | E. MICHIGAN at UMASS |

Seven of fifteen are against the public. Average public support on our sides: 54%.

## Method, unchanged from week 4

Projected margin = `5.1 x (yards-per-play margin difference) - 2.5 home field`,
compared against the spread. The 5.1 is the walk-forward coefficient estimated
across 1,441 games of 2025&ndash;26 using only prior weeks &mdash; not the 8.4 you get
from same-game yards, which is measured after the fact and inflates every
disagreement by 1.7x.

**These are not edges.** `picks_overlay.py` backtested this information at 50.2%
against the spread, with the yards-per-play margin correlating with the spread
itself at r = +0.73. The market already knows. The sides are coin flips with a
lean; the ORDER is where the decision lives.

Weights go to differentiation: least popular side carries 15. Simulated at ten
entrants with every game a true coin flip, contrarian-heavy weighting wins the
week 22.4% against consensus-heavy's 14.5%, with mean score identical to a tenth
of a point. An independent Stan rebuild put those levels at 16.3% and 10.5% &mdash;
six points lower, but a best-to-worst ratio of 1.55 against our 1.54. **Trust the
ratio, not the percentage.**

## What happened to week 4

Nothing. The Sports Page scored **0**, because no entry was submitted. The sealed
rule under digest `b78c44f6` was revealed on schedule and the digest verified
clean &mdash; so the apparatus worked exactly as designed and the experiment never
ran.

That is worth stating plainly rather than quietly re-sealing. A pre-registration
that is never tested proves only that the seal works. Week 5 is the first real
test of the ordering rule, and it is being entered before kickoff for that reason.
