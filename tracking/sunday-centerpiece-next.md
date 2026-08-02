# Sunday Edition — Next Centerpiece Brief

**Teed up: 2026-08-01 (Sat). For Sunday Edition No. 17, built the morning of 2026-08-02.**

> Planning brief, NOT finished copy. The Sunday Edition is built FRESH Sunday
> morning with live data (SKILL.md "Sunday Edition Workflow"). Every number below
> is a Saturday-night snapshot and MUST be re-fetched Sunday AM before it ships.
> **Pull from the MLB Stats API (statsapi), not web summarizers** — reconcile to
> the W-L record. Do not ship stale numbers.

## This edition
- **Sunday Edition No. 17** (16 already published).
- **Recap window (reader issues #119–#126):** #119 NFL-spending/Jets QB · #121
  Mets standings-vs-franchise · #122 CFB Ohio State–Texas line (entropy) · #123
  Cubs/Red Sox droughts (one man ended both) · #124 CFB "fool's errand" contender
  board · #125 no franchise cycles · #126 variance is king (fantasy). (#120 was
  last week's Sunday Edition No. 16.)

## The centerpiece: the deadline came, and the Mets sold
**The hook:** The trade deadline just passed. Issue **#121 — "The Standings Say
the Mets Should Bounce Back. The Franchise…"** — argued the talent/standings
pointed to a rebound while the franchise itself looked broken. Reality answered
at the deadline: the Mets acted like **sellers**, not a team betting on the
bounce-back. That is a gradeable call, and grading our own framing against what
the front office actually did is the whole point of the Sunday Edition.

**Voice:** The Professor (Sundays always). Measured, honest, scoring the call.

## Verified-ish as of Sat 8/1 — ALL **(RE-PULL Sun AM via statsapi + reporting)**
- Mets posture at the deadline: **sellers.** Reported: dealt reliever **A.J.
  Minter** (to the Twins); shopping **Clay Holmes, Freddy Peralta, Luis Robert
  Jr.**; "everyone but the core" available. **(RE-PULL: confirm which deals
  actually closed by the deadline — this is the single most important check.)**
- Mets record / NL East: snapshot had them well under .500 and out of it (a
  search read ~32–40, 5th, ~14.5 back — **UNVERIFIED, statsapi it**).
- Context we've built on the Mets this year: #118 (cost-per-title, $380M vs a
  Royals-level record), #121 (standings vs broken franchise), the WSJ "biggest
  waste of money" thread. The deadline sell-off is the through-line paying off.

## Fresh data to pull Sunday morning (REQUIRED, statsapi first)
1. **Mets final deadline ledger** — who they actually traded, for whom. Turns
   "acted like sellers" into a concrete list. Most important item.
2. **Mets current record + NL East / wild-card standing**, run differential,
   games back.
3. Any **other newsletter-covered player/team** moved at the deadline (Pirates?
   Skenes trade rumors? the sellers from #118 / the deadline pieces).
4. **Paul Skenes' latest line** — the Skenes two-parter publishes Mon/Tue
   (below), so a current stat check keeps the road-ahead honest.

## Predictions scorecard (score what's gradeable; mark the rest PENDING)
- **#121 Mets bounce-back** — GRADEABLE: standings said rebound; front office
  sold. Grade the framing (did "broken franchise" or "should bounce back" win?).
- **Sunday Edition No. 16's open predictions** — carry forward and re-score.
- **#122 Ohio State–Texas line / #124 CFB contender board** — PENDING (CFB
  season hasn't started; nothing to grade yet).
- #123 / #125 / #126 — methods/teaching pieces, not predictions. Nothing to grade.

## Road ahead (strong this week — the founding subject returns)
- Tease the **Paul Skenes two-parter** publishing Mon/Tue: (1) his "struggling"
  9–9 season is mostly noise — outcome stats lie; (2) "the radar gun knows first"
  — which numbers predict vs revert, sparked by a reader's velocity question.
  The newsletter's Issue-#1 subject, back, teaching the founding lesson.
- And the new **Concept No. 26, Signal vs. Noise** primer that anchors them.

## Reminders
- Copy the template, don't consume it: `cp reserve/sunday-recap-template.html queue/sunday-017.html`
- Inject the readership block: `python3 scripts/fetch_readership.py --inject queue/sunday-017.html`
- Reader-facing number = published non-sunday + published sunday + 1.
