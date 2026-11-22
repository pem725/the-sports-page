# Week 12 picks — 2026

Built 2026-11-19, before kickoff. Lines are the CBS pool card's (fixed when the card was set); SP+ from our frozen
snapshot `data/rating-snapshots/2026-w12.json` (taken 2026-11-19). First kickoff Saturday 12:00 PM ET.

## The sheet

| pts | take | game | SP+ edge vs line (pts) |
|---:|---|---|---:|
| 15 | UCLA -3.5 | UCLA at Michigan | 8.4 |
| 14 | Northwestern -3.5 | Northwestern at Minnesota | 6.5 |
| 13 | BYU -5.5 | BYU at Kansas | 5.5 |
| 12 | Nevada -3.5 | Hawaii at Nevada | 5.1 |
| 11 | Utah -6.5 | Utah at TCU | 5.1 |
| 10 | Oklahoma State -3.5 | Oklahoma State at Arizona State | 3.9 |
| 9 | Ohio State -3.5 | Ohio State at Nebraska | 1.6 |
| 8 | Cincinnati -3.5 | Colorado at Cincinnati | 3.1, halved to 1.6 |
| 7 | Texas Tech -3.5 | Texas Tech at Baylor | 3.0, halved to 1.5 |
| 6 | California +2.5 | Stanford at California | 1.1 |
| 5 | Marshall +1.5 | Georgia State at Marshall | 0.1 |
| 4 | Tennessee -1.5 | LSU at Tennessee | 0.1 |
| 3 | Kentucky +5.5 | Kentucky at Missouri | 0.0 |
| 2 | Boston College +3.5 | Syracuse at Boston College | 0.0 |
| 1 | North Carolina +1.5 | North Carolina at Virginia | 0.0 |

**Tiebreaker: 38** (UCLA/Michigan; market total 37.5, DraftKings and Bovada via CFBD).

## Method

Same as earlier weeks with one change. Projected home margin = SP+ home − SP+ away + 2.2 home field; edge = projected
margin minus the market's. **The cross-check is now our own schedule-adjusted yards-per-play net
(`data/ypp-ratings.json`) instead of Massey's consensus**: where it disagrees with SP+ about which team is better,
the edge is halved before ranking (fired on Cincinnati, Texas Tech, Boston College). Massey's data is now inference
only and kept out of this repo.

The bottom five are coin flips: edges of a tenth of a point or less. Their order means nothing.

Worth watching: the CBS card's lines are stale on two games. The market now has Marshall -2.5 (card: +1.5) and LSU
favored by 1.25 at Tennessee (card: Tennessee -1.5). The model did not use that; it reads SP+ against the card.
