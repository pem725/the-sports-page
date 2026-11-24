# Thanksgiving NFL: background TV? (research, 2026-11-18)

nflverse games + play-by-play, 1999-2025 regular season (6,967 games; 73 Thanksgiving). Market chance: vig-free moneyline, else spread (sd 13.5). Details in `results.json`.

## 1. "The Lions almost always lose, usually to somebody like the Cowboys" — PARTLY TRUE
| | Thanksgiving | Other games, same seasons |
|---|---|---|
| Lions | 8-19 (30 per 100) | 167-241-2 (41 per 100) |
| Market expected | 12 wins | 181 (won 168) |
| Cowboys | 15-12 (56 per 100) | 217-192-1 |

The Lions lose 70 of 100. But the market expected them to lose: they were underdogs in 18 of 27 (went 1-17), favorites in 9 (went 7-2). Still 4 wins short of the market (8 or fewer: about 6 in 100). **The Cowboys part is false**: Detroit never played Dallas on Thanksgiving in this span. 16 of 27 opponents were Bears, Packers or Vikings; All-time record unconfirmed from a primary source; not used.

## 2. "Boring" — PARTLY TRUE, and not the Lions' fault
| per game | Thanksgiving | All other |
|---|---|---|
| Decided by 8 or fewer, per 100 | 42 | 51 |
| Favorite's market chance | 68% | 66% |
| Win-probability swing (sum of moves) | 3.5 | 3.9 (perm. p = .03) |
| 4th-quarter comebacks, per 100 | 16 | 24 |

Lions games are near average (3.7); the night game drags (3.0). Best: HOU 34-31 DET (OT) 2012, top of all 6,964 games. Worst: TEN 47-10 DET 2008.

## 3. "Inconsequential" — FALSE
Logistic model (playoffs ~ pre-game win% x result; 854 team-games, Thanksgiving weeks). Playoff-chance swing per game: **30 points** Thanksgiving, **30** other games that week. Both teams under .500: 15 per 100 vs 21.

## 4. 2026 slate — LESS consequential than usual
| Game (TV) | Records | Line | Playoff odds | Swing (sim) |
|---|---|---|---|---|
| CHI at DET (CBS) | 7-2 / 7-2 | CHI -1.5 | 83% / 90% | 27 pts |
| PHI at DAL (FOX) | 2-7 / 4-6 | DAL -8.5 | 2% / 27% | 22 |
| KC at BUF (NBC) | 7-2 / 8-1 | BUF -3 | 97% / >99% | 4 |

nflverse and ESPN agree. Swing: 200,000 runs of the Odds Board's game chances (no tiebreakers; within 4 points of the Board). Same-week Sunday games median ~25. Chiefs-Bills is about seeding, not playoffs.

## 5. The parade — sourced, and the claim fails on audience
2025: parade 25.4M on NBC's 8:30 airing, 34.3M with Peacock ([NBCU](https://www.nbcuniversal.com/article/nbcs-macys-thanksgiving-day-parade-set-all-time-viewership-record)). Games: GB-DET 47.7M, KC-DAL 57.2M, CIN-BAL 28.4M ([NFL.com](https://www.nfl.com/news/2025-thanksgiving-day-nfl-games-shatter-viewership-records)). Bases differ.
