# How many points do you need? College vs NFL, 2006-2025

Data: CFBD games, FBS vs FBS only, 14,844 games (29,688 team-games), regular + postseason, no ties (OT).
NFL: nflverse team-games, 5,199 games (10,398 team-games), 14 ties counted as half wins.
Mirror identity respected: P(win | allowed x) = 1 - P(win | scored x) (checked: sums to 1.000 at 10/17/21/24/28/35 in both leagues). So the "allow" column below is the same curve read from the other side, not a second finding.

## 1. Thresholds (smoothed +-2 pts window, interpolated)

| Win this often | CFB: score at least | CFB: allow at most | NFL: score at least | NFL: allow at most |
|---|---|---|---|---|
| 50% | 26 | 26 | 22 | 22 |
| 75% | 35 | 17 | 30 | 16 |
| 90% | 46 | 13 | 38 | 10 |
| 95% | 53 | 9 | 42 | 7 |

Mean points per team-game: CFB 27, NFL 23. The 25-to-75% band of doubt: CFB ~18 pts wide (17 to 35), NFL ~14 (16 to 30).
Era drift: CFB 50% point 24 (2006-10) vs 25 (2021-25); NFL 21 vs 21. Small.

## 2. Compensation (team-seasons, regular season, PPG/PAPG centered on season mean)

- One PPG of offense and one PPG of defense are worth the same in both leagues.
  CFB: +1.9 win-pct points per PPG either way (0.0190 vs 0.0187, diff -0.0003, SE 0.0005; n=2,483).
  NFL: +2.8 either way (0.0277 vs 0.0282, diff +0.0004, SE 0.0014; n=640).
- Matched margin: defense-led (low-total) vs offense-led (high-total) teams at the same PPG margin.
  CFB: lowest vs highest quintile of total, -0.6 win-pct points (95% CI -1.8 to +0.5; n=497 each).
  NFL: -0.5 (CI -2.3 to +1.4; n=128 each). Both null. 2-PPG (CFB) / 1-PPG (NFL) bin tables in results.json.
- Bottom-half offense + top-quartile defense: CFB 73% had a winning record (166/229); NFL 56% (29/52).
  Mirror profile (bottom-half D + top-quartile O): CFB 71% (153/217); NFL 68% (34/50).
- Bottom-quartile offense, winning record: CFB 7.2% (45/621), NFL 4.3% (7/161). Bottom-quartile defense: CFB 8.0% (50/622), NFL 8.7% (14/160). NFL gap not significant (CIs 2-9% vs 5-14%).
- Where the leagues differ is spread, not value: NFL offenses vary more than defenses (SD 4.3 vs 3.4 PPG); CFB they are equal (7.2 vs 7.0). A great NFL defense simply buys fewer points than a great NFL offense.
- Pythagorean exponent: CFB 2.5, NFL 2.7 (RMSE 0.092 / 0.081 win pct). A point of margin is worth ~1.5x more in the NFL (2.8 vs 1.9 win-pct points per PPG).
- Verdict on the editor's hunch: not supported. In college you CAN compensate, point for point, exactly as in the NFL; if anything the NFL is where the defense-first path is (non-significantly) narrower.

## 3. Hold them under 15

| | CFB | NFL |
|---|---|---|
| P(win, allowed <=14) | 94% (n=6,133) | 91% (n=2,423) |
| Share of team-games allowing <=14 | 21% | 23% |
| 2006-10 -> 2021-25 share | 23% -> 21% | 28% -> 22% |
| P(win, allowed exactly 14) | 90% (n=1,330) | 88% (n=357) |
| Team-seasons holding every opponent <=14 | 1 of 2,483 (2011 Alabama, FBS foes) | 0 of 640 |
| Median team: share of games <=14 | 18% | 24% |

## 4. Yards per play allowed vs points allowed (per team-game, opp plays >= 30)

| | n | r (YPP) | r (total yards) | median YPP when <=14 | P(<=14 given YPP<4) | pts per +1 YPP |
|---|---|---|---|---|---|---|
| CFB 2006-11 | 8,550 | 0.71 | 0.74 | 4.1 | 71% | 6.8 |
| CFB 2024-25 | 3,210 | 0.75 | 0.78 | 4.2 | 76% | 6.9 |
| NFL 2006-25 | 10,398 | 0.62 | 0.64 | 4.4 | 68% | 5.5 |

YPP explains ~half the variance in points allowed in college (r^2 0.52), ~40% in the NFL (0.39). At 6+ YPP allowed, a <=14 game is 1-2% in college and 3% in the NFL. Plays alone correlate only 0.2-0.3. Total yards edges YPP slightly because it carries volume (plays) too.

## Most striking
Twenty years, 2,483 FBS team-seasons, and exactly one held every FBS opponent under 15: 2011 Alabama. "Hold everybody under 15" is a 94%-win rule per game and a near-impossible season.

## Validation
- 1,775 games cross-checked against ESPN summary API: 0 score errors; 2 neutral-site bowls (2024 Myrtle Beach, 2024 Las Vegas) have home/away labels swapped between sources (scores identical; their YPP pairing may be swapped, negligible).
- Spot checks vs ESPN: 2006 Fiesta Bowl Boise St 43-42 Oklahoma; 2013 Iron Bowl Auburn 34-28 Alabama; 2019 CFP final LSU 42-25 Clemson. All match.

## Caveats
- CFBD monthly quota hit 0 mid-pull (2011 wk 12). CFB box scores cover 2006-11 (CFBD) and 2024-25 (ESPN) only; 2012-23 YPP not measured. The two windows agree (r 0.71 vs 0.75).
- WARNING: this key is the pipeline's key; quota is now exhausted for the month, which may affect the daily CFB refreshers (build_cfb_odds, sunday_football) until it resets.
- FBS-vs-FBS only: FCS games excluded, so team-season PPG covers ~11 games. Schedule strength is not adjusted; CFB PPG mixes talent gaps with schedule.
- Season-level relationships are correlational; "defense-led" = below-average combined scoring at a given margin, not a coaching philosophy.
- CFB plays = rushes + pass attempts (sacks inside rushes); NFL plays = scrimmage plays incl. sacks. Comparable, not identical.
