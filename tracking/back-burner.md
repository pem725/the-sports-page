# The Back Burner — pieces held deliberately, and what brings them back

Not a graveyard. Every file here is finished or near-finished work that is
*waiting on something*: a date, an outcome, a cooled-off news cycle. The purpose
of this file is that the trigger survives the session that noticed it.

**A benched file is kept in `queue/` but left OUT of `QUEUE_ORDER.txt`.** That is
what stops autopublish taking it. Do not delete a benched file, and do not
"tidy" it back into the order without checking the trigger below.

---

## `088-sorsby-supplemental-bet.html` — Sal's Column

**Status:** held for a one-year follow-up. Do not publish as written.

**Two independent reasons it is benched, and both must clear:**

1. **It is Sal's Column.** Per CLAUDE.md, the scheduled agent must NEVER publish
   in Sal's voice. Sal writes only when the human explicitly invokes him. This
   file can therefore never be autopublished, whatever the calendar says.
2. **The story is not finished.** The piece's own stat line reads *"2027 — the
   earliest he may now reach the NFL — a year, gone."* It was written in June
   2026, about a month into the argument. Its subject is the five institutions
   that each offered Brendan Sorsby a door and then declined to open it; the
   supplemental draft has chosen exactly one player since 2019.

**The revival trigger — "where is he now":**

| When | Why then |
|---|---|
| **Late April 2027**, the NFL Draft | The first moment the question has a factual answer rather than a projection |
| **July 2027**, the supplemental draft | The mechanism the original piece was actually about |
| ~**May–June 2027** | One year from the case itself, if the anniversary is the better hook |

**What the follow-up has to establish before a word is written** — none of this
is knowable now, and all of it must be sourced, not inferred:

- Where he actually is: roster, league, or out of football entirely
- Whether any club used a supplemental pick on him, and whether one was even held
- What the five institutions did afterwards — the original piece's real subject
  was them, not him, and the follow-up should stay pointed there
- Whether the base rate moved: one supplemental selection since 2019 was the
  spine of the argument

**Technical note if it is revived:** this file has no `<div class="footer">` and
therefore never received the `<!-- WATCH_BLOCK -->` marker or the `.watch`
styles. Both must be added before publishing, or it ships without the daily
What to Watch section. Start from `queue/_TEMPLATE.html` if in doubt.

---

## `104-payroll-explosion-arms-race.html`

**Status:** benched for topic saturation, not for quality.

The queue was beating the payroll drum too hard. Bring it back when several
weeks have passed without a money/payroll piece, and check the recent run before
restoring it to `QUEUE_ORDER.txt`.

## Benched 2026-09-06 — sport out of season, by editorial direction

The paper alternates **college football and baseball only** until baseball ends,
then college football and the NFL. These two are held, not dropped, and neither
has rotted:

- **`140-one-kick.html`** (NFL, kicking probability, answers Gene). *Revival
  trigger:* the day the NFL becomes a rotation sport — when the baseball season
  ends. It is `dated` only in the loose sense that it references a current
  season; check its figures still hold before restoring.
- **`149-where-players-die.html`** (NFL, the Cleveland refutation). *Revival
  trigger:* same. This one is `keeps` and will not go stale — the within-player
  design covers 2015–2022 and nothing about it decays.

Neither is in QUEUE_ORDER, so autopublish cannot pick them up. Restore both by
adding them back to the order once the NFL is in rotation.

## Held 2026-09-09 — waiting on a non-CFB slot

- **`147-talent-addresses.html`** (CFB, where elite recruits actually come from).
  `keeps`, so nothing rots. Held only because the queue currently carries three
  college football pieces and two of anything else, which cannot be interleaved
  without a clash. *Revival trigger:* the moment one more baseball piece lands —
  the Detroit run-differential story is the obvious one.
