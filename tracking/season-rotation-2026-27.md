# Season rotation, November 2026 to April 2027

Set 2026-10-31 by the editor, the day Jeff joined the board: *"now that baseball
is starting to fade, we're going to need another sport so we have a round
robin."* One slot a day and no back-to-back topics means the queue needs at least
three live sports at all times. From mid-February to late March there are only
two with games (basketball and hockey), so basketball is the piece that keeps the
rotation honest.

Dates marked ~ are approximate; confirm each one against the league's own
calendar before a piece leans on it.

## What is live, fortnight by fortnight

| window | football | baseball | basketball | hockey | other |
|---|---|---|---|---|---|
| Nov 1-15 | NFL midseason, CFB November, NFL trade deadline **Nov 10** | awards, hot stove | CBB tips off ~early Nov; NBA early season | NHL | |
| Nov 16-30 | CFB rivalry week (Thanksgiving), CFP rankings | **labor deal expires Dec 1**; lockout piece (193) the week of Nov 23 | CBB early tournaments | NHL | |
| Dec 1-15 | conference title games, CFP field | lockout begins (expected) | CBB nonconference | NHL | CFB early signing day ~early Dec |
| Dec 16-31 | bowls, CFP first round | lockout | CBB | NHL | |
| Jan 1-15 | CFP; **NFL regular season ends Jan 10** | lockout | CBB conference play | NHL | |
| Jan 16-31 | NFL playoffs, CFP final ~mid/late Jan | lockout | CBB conference play | NHL midseason | |
| Feb 1-15 | Super Bowl ~mid-Feb | spring training ~mid-Feb **is the lockout fork** | CBB bubble talk | NHL | CFB signing day ~early Feb |
| Feb 16-28 | **no games** | camps open, or don't | CBB | NHL | NFL combine ~late Feb |
| Mar 1-15 | **no games**; NFL free agency ~mid-Mar | spring training | conference tournaments; **Selection Sunday ~mid-Mar** | NHL | |
| Mar 16-31 | **no games** | **Opening Day ~late March = our anniversary** | **March Madness** | NHL stretch run | |
| Apr | NFL draft ~late April | MLB season | Final Four ~early April; NBA playoffs | NHL playoffs | WNBA draft ~April |

**The hole is February 16 to Opening Day.** No football, baseball maybe locked
out, and only basketball and hockey playing. A queue in that window needs a
basketball piece roughly every third day, and it needs them banked by early
February, not written the night before.

## The round robin, as a target

A target for any seven-day week, not a rule:

- **Nov-Jan:** 2 CFB, 2 NFL, 1 MLB (labor, hot stove, history), 1 basketball, 1 other (methods, markets, NHL).
- **Feb-Mar:** 2 basketball, 1 NFL (draft, free agency, the Super Bowl look-back), 1-2 MLB (lockout or spring), 1 NHL, 1-2 methods or markets.

`queue_health.py` checks the no-back-to-back rule. It does not check the mix;
eyeball the week against this table when queueing.

## Where Jeff fits

Basketball is his beat: college, WNBA and NBA. Nobody else on the board follows
it, which is the reason he is here. Tim and the editor read the WNBA.

- **The NBA has a pitch count.** An NBA piece runs only when Jeff writes or
  champions it, and at most one in any two weeks. WNBA and college basketball are
  open to anyone, with no count.
- **Topics:** use `topic: CBB`, `topic: WNBA` or `topic: NBA` in PUBLISH-META.
  All three get the basketball glyph (`assets/glyph/basketball.svg`). Note that
  the variety rule compares topic strings, so a CBB piece followed by an NBA piece
  is not flagged; avoid it by eye.

### Basketball pieces already in hand (for Jeff to read first)

1. **Angel Reese's self-rebounds** (WNBA). Tim's question. Counted from ESPN
   play-by-play for every player in the league: `scripts/self_rebounds.py`. Needs
   a check against the WNBA's own play-by-play before it runs. `keeps`.
2. **Caitlin Clark's statistical twin** (WNBA). Distance-matching her profile
   against every player in history. Concept worked out; not drafted. `keeps`.

### Basketball ideas worth his opinion

- **March Madness bracket math:** seed-versus-seed history and how often a
  12 beats a 5. Already a tentpole on the CLAUDE.md calendar; Selection Sunday
  ~mid-March. Draft by early March.
- **The coin-flip bracket:** how a perfect bracket's odds compare with a
  well-informed one, the same lesson as the coin-flip pool.
- **Early-season college rankings:** how much a November top-25 predicts March
  (the "after one week, what do we know" question, in basketball).

## Before February, bank these

- At least **four basketball pieces** queued or ready by Feb 10.
- The **Opening Day anniversary issue**, in two versions: the lockout over, or
  the lockout still on.
- The **Super Bowl** eve and morning-after pair.
