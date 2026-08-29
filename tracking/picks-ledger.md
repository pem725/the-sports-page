# The Family Pool — a running calibration test

Four players: Patrick, his son, his brother, his cousin. Fifteen college football
games a week, ranked 1 to 15 by confidence, 15 being most certain.

**This exists to answer one question, and it is not "did we win".** It is whether
the numbers mean anything. When the model says 71%, does that group of picks win
about 71% of the time over a season? A single 71% pick losing is not evidence of
anything — 71% picks are *supposed* to lose 29% of the time. Only the aggregate
can speak, and only after twenty-five or thirty games.

## Method

Point spreads are converted to win probabilities through a normal CDF with a
13.5-point standard deviation, the usual figure for college football. Confidence
is then ranked by that probability, with ties broken toward the side the public
is *not* on — same expected value, better separation from three relatives.

Two known limits, stated up front so they are not discovered later as excuses:

- 13.5 points runs a little wide for lopsided games, so the 24-point spreads are
  probably nearer 95% than the 97% quoted.
- The public percentages are CBS's national split, not what three specific
  relatives will actually do.

## Week 1, submitted 2026-08-29

| Pts | Pick | Over | Model | Public |
|---:|---|---|---:|---:|
| 15 | Miami | Stanford | 97% | 74% |
| 14 | Penn State | Marshall | 97% | 83% |
| 13 | Washington | Washington State | 95% | 69% |
| 12 | Notre Dame | Wisconsin | 94% | 70% |
| 11 | Northwestern | South Dakota State | 84% | 61% |
| 10 | LSU | Clemson | 76% | 71% |
| 9 | Duke | Tulane | 74% | 65% |
| 8 | Auburn | Baylor | 71% | 74% |
| 7 | TCU | North Carolina | 71% | 77% |
| 6 | Cincinnati | Boston College | 71% | 79% |
| 5 | UNLV | Memphis | 68% | 53% |
| 4 | North Dakota State | Jacksonville State | 68% | 72% |
| 3 | James Madison | Liberty | 68% | 80% |
| 2 | Georgia Tech | Colorado | 68% | 86% |
| 1 | Virginia | NC State | 66% | 52% |

Expected: 11.7 correct, about 100 of 120 points.

## Running it

```
python3 scripts/picks_ledger.py --update    # pull results for finished games
python3 scripts/picks_ledger.py --report    # standings and the calibration table
```

Results come from ESPN, which updates live; the CollegeFootballData API lags
hours behind a finished game.

## The issue this becomes

By November there should be 150+ resolved picks across ten confidence bands.
That is a real calibration curve, and it is the piece: *we told you 71% thirty
times — here is how often it happened.* Publishing a calibration curve of our own
forecasts is the most honest thing this newsletter can do, and almost nobody does
it.
