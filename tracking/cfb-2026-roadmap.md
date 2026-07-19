# College Football 2026 — Content Roadmap & Modeling Project

The user's stated passion. Goal: model the 2026 CFB playoff picture — contenders,
dark horses, key matchups, key weeks — and track it from now through the season.

## The thesis (the user's own)

**Maturity + talent + sound fundamental football wins.** Operationalized:
- **Maturity** = returning production / roster experience (a well-known CFB
  predictor — returning production, especially on offense, forecasts
  year-over-year success). This is the spine of the contender model.
- **Talent** = recruiting/portal talent (blue-chip ratio, portal hauls).
- **Fundamentals** = a coach who builds it (the "Saban way").
- **Dark horses** = high returning production + a proven program-builder +
  a favorable schedule. Precedent: **Kurt Cignetti came out of nowhere**
  (Indiana). Candidate floated: **Texas Tech** (caveat: QB question unresolved).

## Pieces to build (proposed sequence)

1. **"Maturity Wins" — returning production as a playoff predictor** *(buildable now)*.
   Rank the 2026 field by returning production + talent; show the historical
   correlation between returning production and CFP appearances. Directly
   encodes the user's thesis. On-thesis, data exists pre-season.
2. **Contender shortlist + dark-horse board** *(buildable now-ish)*. Who has a
   "fighter's chance," who's the Cignetti-style dark horse, with the maturity/
   talent model as the engine.
3. **"The weeks that matter" — a 2026 CFB marquee-week calendar** *(BUILT 2026-07-18
   as `queue/105-cfb-weeks-that-matter.html`)*. Answers the user's direct question:
   which weeks to focus on. Statistical spine = **information content (Shannon
   entropy)**: the highest-leverage games are contender-vs-contender toss-ups
   (a coin-flip = 1 bit; a blowout ~ 0 bits). Pulled the real 2026 schedule +
   opening lines from CFBD (`scratchpad/cfb_sched.py`, `cfb_entropy.py`): 22
   contender-vs-contender games; only the Sept openers carry lines this far out
   (Ohio State @ Texas -1.5 -> 0.99 bits; Oklahoma @ Michigan -2.5 -> 0.98; Clemson
   @ LSU -11.5 -> 0.72). Six marquee weeks tabled (Wk2, 4, 6, 7, 10-11, 13). Segment
   note for CFB-first vs NFL-first ("clear only three Saturdays: Sep 12, Oct 10,
   Nov 28"). Figure = the entropy dome with the three priced games. Queued as the
   non-MLB buffer between payroll #103 and #104. **Ideal Tier-2 follow-up: an
   "Information & Surprise" concept primer** (entropy/bits) — wired here only to
   the existing communicating-uncertainty primer as a stopgap.
4. **CFB Pre-Season Simulation** *(late August — last weekend before Week 0/1)*.
   The existing tentpole. Uses the "Pre-Season Simulation Framework" methods
   piece + Vegas win totals as priors + JND threshold. Grade weekly in Sunday
   Editions. (See CLAUDE.md "Pre-Season Simulation" + scripts/build_cfb_jnd_dataset.py,
   fit_cfb_jnd_curves.py — CFB modeling infra already exists; Issue #022 used it.)

## Key matchups to track (populate from the 2026 schedule)

- **LSU @ Ole Miss** (user-flagged as a playoff-contender measuring stick).
- (To populate: marquee non-conference games, SEC/Big Ten deciders, rivalry week.)

## Audience note

CFB fans vs NFL fans are different segments. Lead CFB for the user's audience;
tag NFL separately. **Tim = Buffalo Bills fan (NFL), laughs at the Jets** — NFL
content should keep Tim in mind (Bills angle welcome).

## Status / next data needs

- Pull the **2026 CFB schedule** (marquee games + key weeks).
- Pull **2026 returning-production / portal / blue-chip data** for the contender model.
- Verify everything before drafting (triple-verify rule) — this file is ideation,
  not vetted copy.

This file lives in `tracking/` so the autopublish bot ignores it.
