# Patrick's Pool — Week 4 independent audit

Checked 2026-09-23 against the live CBS Week 4 card and
`python3 scripts/picks_overlay.py --week 4 --year 2026`.

This is a second set of eyes for the person building the slate. It is not a
pick sheet and nothing was entered on CBS. At audit time the page showed
**0/15 picks** and a blank tiebreaker.

## The live card

The percentage is CBS's national selection split. The point value shown is the
card's current default order, not a recommendation.

| default pts | matchup | CBS line | public side |
|---:|---|---:|---|
| 15 | Army at Temple | Army -3.5 | Army 77% |
| 14 | Clemson at California | California -0.5 | California 52% |
| 13 | Texas at Tennessee | Texas -5.5 | Texas 63% |
| 12 | UCLA at Maryland | UCLA -2.5 | UCLA 68% |
| 11 | Ole Miss at Florida | Florida -3.5 | Ole Miss 75% |
| 10 | UConn at Miami (OH) | Miami (OH) -4.5 | UConn 55% |
| 9 | Iowa at Michigan | Michigan -5.5 | Iowa 60% |
| 8 | TCU at UCF | TCU -3.5 | TCU 55% |
| 7 | Nebraska at Michigan State | Nebraska -5.5 | Nebraska 57% |
| 6 | James Madison at Old Dominion | James Madison -6.5 | James Madison 89% |
| 5 | Kansas State at Cincinnati | Kansas State -6.5 | Cincinnati 56% |
| 4 | Oklahoma State at West Virginia | West Virginia -1.5 | West Virginia 67% |
| 3 | Oregon at USC | Oregon -3.5 | USC 57% |
| 2 | Missouri at Mississippi State | Mississippi State -5.5 | Mississippi State 69% |
| 1 | Georgia Tech at Stanford | Georgia Tech -3.5 | Georgia Tech 72% |

Lines can move. Read these back from CBS before sealing or entering anything.

## Where the explanatory stats actually disagree

The overlay is season-to-date through Week 3. Its main measure is yards-per-play
margin: yards gained per play minus yards allowed per play. The script's own
back-test is the guardrail: this information is already strongly represented in
the spread (`r = +0.73`) and went **50.2% ATS** in 2024–25. Use it to locate the
argument, not to pretend the argument has been settled.

### Strongest disagreements with both line and crowd

1. **Tennessee +5.5 vs Texas.** Tennessee's YPP margin is +2.9; Texas is +0.6.
   Tennessee also leads in completion percentage, 66.2% to 63.2%, and yards per
   game, 510 to 417. CBS has Texas laying 5.5 and 63% of the public on Texas.
   This is the cleanest three-way disagreement on the card.

2. **Maryland +2.5 vs UCLA.** Maryland leads YPP margin +2.8 to +2.0 and
   completion percentage 73.2% to 61.0%. CBS has UCLA laying 2.5 with 68% of
   the public. The total-yards difference is small (515 to 490), which makes
   this less lopsided than the completion gap alone looks.

3. **Florida -3.5 vs Ole Miss.** Florida leads YPP margin +3.5 to +0.7,
   completion percentage 74.1% to 68.1%, and yards per game 544 to 445. Yet
   75% of CBS users are taking Ole Miss plus the points. This is the largest
   crowd-versus-profile split on the slate.

4. **Kansas State -6.5 at Cincinnati.** Kansas State leads YPP margin +3.7 to
   +1.2 while 56% of the public takes Cincinnati. Total yards are effectively
   tied, and Cincinnati's completion percentage is higher, so the disagreement
   lives specifically in efficiency per play rather than volume.

### Useful checks, but not contrarian

- **UConn +4.5 at Miami (OH):** YPP margin +2.0 versus +0.2 and a 443–379
  yards-per-game advantage. The public already leans UConn, 55%.
- **Iowa +5.5 at Michigan:** YPP margin +3.9 versus +1.8 and a large volume
  advantage. The public already leans Iowa, 60%.
- **Nebraska -5.5 at Michigan State:** +3.4 YPP margin versus -0.3. The public
  leans Nebraska, but only 57%, so it is less crowded than the profile suggests.
- **Georgia Tech -3.5 at Stanford:** +0.4 versus -1.1. CBS users are already
  there at 72%.

### Weak or internally mixed signals

- **TCU -3.5 at UCF:** nearly equal YPP margins (+2.0, +2.3). TCU has the
  completion and yardage advantages; the efficiency measure does not confirm
  the favorite.
- **Oklahoma State +1.5 at West Virginia:** YPP margins are nearly equal
  (+1.6, +1.3). The 67% public lean to West Virginia creates differentiation,
  but the overlay does not supply a strong football reason.
- **Oregon -3.5 at USC:** YPP margins are close (+1.9, +1.5), while USC leads
  completion percentage. This is a judgment game, not an overlay game.
- **Mississippi State -5.5 vs Missouri:** Mississippi State has a modest YPP
  edge (+3.1 to +2.4) and a large yardage edge, but 69% of the public is already
  on that side.

## One correction to keep in mind for the guide

`pool/how-to-play.html` models **eight entrants**, matching the eight active
Week 3 entries in the ledger. The live CBS pool now lists ten names; participation
has varied by week (for example, one entry has zero season points). The guide is
not necessarily wrong, but “fair share, 8 entrants” should be read as the Week 3
simulation assumption, not a permanent property of the pool. If the active field
changes, the displayed fair share and win curve need to change too.

The stronger mathematical caveat is that “ordering cannot help you” is exact
only when every ATS result is an independent 50/50 event. It is a useful null
model, not a literal fact about fifteen unequal games. If the picker has a real,
calibrated probability difference across games, assigning larger weights to
larger probabilities raises expected score. The published evidence so far says
we have not demonstrated that ability, which is the honest reason to use the
coin-flip model.

