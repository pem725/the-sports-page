# Days to watch vs days to publish — a question for the board

Raised by the editor, 2026-10-26:

> "Sports happens and sports reporting happens afterwards... We got to start thinking about the days
> to publish versus the days to watch. Maybe we start rethinking the way we pace out the sports page."

## The problem in one table (football season, September to January)

| Day | What fans watch | What we publish now (4:30am) | Can that issue know what happened? |
|---|---|---|---|
| Sat | college football, all day | a queued piece | no — the games have not been played |
| **Sun** | **the NFL, all day** | **Sunday Edition**: Saturday's college recap + today's NFL card | college yes, NFL no |
| **Mon** | Monday Night Football; everyone reads about Sunday | **a queued piece, written days earlier** | **it could, and it doesn't** |
| Tue | (CFP rankings from November) | queued | — |
| Wed | — | queued | — |
| Thu | Thursday Night Football, some college | queued | — |
| Fri | Friday college | queued | — |

The Sunday paper habit — the reader's Sunday morning — is real, and the football-season shape already
uses it well: Saturday's college results are measured, and the NFL card is ranked by nearness to a coin
flip. The gap is **Monday**. It is the day the whole country reads about sports, the day after the NFL
plays, and we fill it with a piece that was queued last week.

## Options

**A. Keep it.** Sunday Edition as is; Monday stays a queued piece. Costs nothing. Leaves the NFL weekend
unreported until the following Sunday, when it is a week old.

**B. Add a Monday recap of the football weekend (recommended).** The Sunday Edition stays as it is.
Monday morning carries a generated block: Sunday's NFL results against the lines (expected upsets vs
actual, the week's longest shot), plus the stat line of the weekend from both levels — the way the
Monday memo of 10-26 worked through Saturday's box scores. Generated, not recalled, like
`scripts/sunday_football.py`, because Sunday night at 11pm is when wrong numbers get typed. The rest of
Monday's issue can still be a queued piece; the recap is a block on top of it, or a short issue of its own.

**C. Move the edition to Monday.** Sunday becomes a short NFL-watch issue; the big weekly edition
moves to Monday, covering Saturday and Sunday together. The truest to how sport happens, but it gives
up the Sunday-morning reading habit, and the prediction scorecard would grade a week that ends on Sunday.

## What each option costs

- **The queue is built for pieces that keep.** A recap is `hot` by definition and must be produced the
  night before. A or C need one fresh piece a weekend; B needs two (Saturday night, Sunday night) unless
  the Monday block is generated. That is the argument for generating it.
- **Monday 4:30am cannot include Monday Night Football.** MNF belongs to Tuesday or the next Sunday.
- **Buttondown mails when the feed updates,** so a late Monday publish is a late Monday email.

## The rest of the week, if B is adopted

| Day | Job |
|---|---|
| Sun | Sunday Edition: college Saturday, measured; the NFL card by leverage; the improbability lesson |
| Mon | The weekend recap (generated block) + a queued piece |
| Tue | Box Score Anatomy or another piece that keeps; CFP rankings from November |
| Wed | Series / A Reader Asks |
| Thu | College weekend preview — the games that matter, by leverage |
| Fri | Flex: NFL, hockey, WNBA, MLB |
| Sat | College game-day piece |

The variety rule still holds: a CFB Sunday followed by an NFL-and-CFB Monday needs a ruling (the
recap counts as its own topic, or Monday carries `allow_clash: true`).

Off-season it reverts: baseball plays every day, so every day is a recap day.

## Coverage mix — decided by the editor, 2026-10-26

- **No NBA coverage.** The board brief asked for a yes or no; the answer is no.
- **WNBA is welcome**, including shooting stats and how WNBA players measure against the men's game —
  told from the WNBA side. The banked Caitlin Clark distance-matching piece is the model.
- **Hockey stays occasional.** Fewer pieces, chosen when a number earns it.

## What would settle it

Opens and visits by weekday since September. If Monday already reads well with a queued piece, B is a
nice-to-have; if Monday lags Sunday by a lot, the reader is telling us where the recap belongs. Those
numbers stay inside the locked board page, never in this file.
