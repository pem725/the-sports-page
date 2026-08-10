# CFB Pre-Season Simulation — engine + build plan (Roadmap Part IV)

The late-August tentpole. Drops the **last weekend of August**, before Week 0/1, and
every Sunday Edition grades the season against this baseline. This file is the recipe;
the engine is `scripts/cfb_preseason_sim.py`.

## Why it is NOT queued yet (built 2026-07-18)

The engine is done and validated, but the **2026 prior does not exist yet**: SP+ and FPI
ratings for 2026 are not posted in CFBD as of mid-July (the `/ratings/sp?year=2026`
endpoint returns 0 rows). Preseason SP+ typically posts in August. Publishing a forecast
now would bake in stale, pre-camp expectations. So: engine now, **refresh + publish the
last weekend of August**, once `--year 2026` returns a full ratings table.

### UPDATE 2026-08-09 — the blocker has a way around it: use FPI

`/ratings/sp?year=2026` still returns **0 rows**. But `/ratings/fpi?year=2026` now returns
**138 teams**, and FPI is the same kind of quantity as SP+ — points above an average team —
so it is a drop-in prior, not a different model.

The scales are close enough to swap with one adjustment:

| | n | mean | SD | range |
|---|---|---|---|---|
| FPI 2026 | 138 | 0.00 | **11.33** | −19.3 … +28.7 |
| SP+ 2025 | 137 | +0.70 | **13.05** | −36.6 … +32.4 |

FPI is slightly compressed. `TAU` and `SIGMA` were tuned against SP+'s spread, so either
scale FPI by ≈1.15 (13.05/11.33) before feeding it in, or leave it and accept a marginally
tighter distribution of outcomes. **Scaling is the better choice** — it keeps the engine's
validated constants meaningful instead of silently changing what they mean.

FPI 2026 top five: Ohio State +28.7, Texas +26.9, **Notre Dame +25.9**, Oregon +25.3,
Georgia +24.8. (Consistent with the published FPI having ND at No. 3 while the preseason
Coaches Poll has them 5th — a gap that is itself an issue.)

`/lines?year=2026&week=1` also returns 99 rows, so the "blend in Vegas as a second prior"
idea from refinement #5 is now actionable too.

#### First 2026 run (FPI prior, 4,000 iterations)

| Team | Wins (80%) | Playoff | Title |
|---|---|---|---|
| Ohio State | ~10 (8–12) | 89% | **21%** |
| Texas | ~10 (8–12) | 80% | 16% |
| **Notre Dame** | **~11 (10–12)** | **95%** | 11% |
| Oregon | ~9 (8–11) | 77% | 11% |
| Georgia | ~9 (7–11) | 70% | 10% |

Note the Notre Dame shape, because it is the issue: **the most wins and the highest Playoff
probability in the country, but only the third-best title odds.** An independent schedule
with no conference title game to lose is the easiest path *into* the bracket; it does
nothing once you are in it, where only strength matters. Wins and quality are different
quantities and the bracket only prices one of them.

#### CAUTION — do not publish the coin-flip number as a year-over-year change

The JND pass returns **56% coin flips for 2026** against ~42% in 2024 and 2025. That looks
like a parity explosion. Most of it is not.

Same 2025 schedule, both priors:

| | coin flips |
|---|---|
| 2025, SP+ | 42% |
| 2025, FPI rescaled | **48%** |
| 2026, FPI rescaled | **56%** |

FPI is more compressed through the middle of the distribution than SP+ even after the
standard deviations are matched, and that alone moves the figure ~6 points. So of the
14-point jump, roughly **6 points is the instrument and 8 points is the season**.

The honest published comparison is therefore **FPI-to-FPI: 48% → 56%.** Reporting
"56%, up from 42%" would swap the measuring device and the subject at the same time and
credit the world with the difference — which is precisely the confound this newsletter
exists to name. If SP+ posts before the run, use it and the problem disappears.

**Massey Ratings is not an option.** It was suggested as another source, but
`masseyratings.com/robots.txt` carries `User-agent: ClaudeBot / Disallow: /`, plus
`Content-Signal: ai-train=no, use=reference` and an express Article 4 reservation of
rights, and the site's data endpoint is deliberately obfuscated. Do not scrape it. If those
ratings are wanted as a prior, a human should retrieve them under their own browser session
and drop the file in, the same way the headline dataset arrived.

## Methodology (encoded in the engine — TWO modes)

Prior for both = **SP+ team-strength ratings** (points above average) from CollegeFootballData.

**`--mode bayes` (DEFAULT, the one to publish).** This is the heavy-Bayesian analysis the
user asked for (2026-07-19): "use these Bayesian tools I've used over the years; dig deep
into parameter estimates; tune people into heavy data analysis." Team true strength is
UNCERTAIN — SP+ is an estimate, not gospel — so each iteration draws `theta_i ~ Normal(SP+_i,
TAU=6)`, plays the full regular season with game noise `Normal(0, SIGMA=13.5)` + HFA=2.5,
builds the 12-team field, and simulates the fixed CFP bracket to a champion. 4,000 iterations
→ **posterior-style distributions**: a win total with an 80% credible interval, and honest
probabilities of making the Playoff / winning the league / winning it all. Reports RANGES,
not point estimates — the method embodies the [[feedback-significant-digits]] rule (≤2 sig
figs, ranges over false-precision decimals) and concepts communicating-uncertainty (No. 18)
and information-and-surprise (No. 20). Future upgrade the user wants taught: **update the
posterior weekly** with observed results (conjugate Normal-Normal on strength, or the
newsletter's Gamma-Poisson / Beta-Binomial tools per CLAUDE.md) so Sunday Editions show
Bayesian updating in action — the preseason sim is the PRIOR, each week is the update.

**`--mode jnd`.** Single deterministic pass. A game is a *confident call* only if the favorite
clears **P=0.75** (the threshold Issue #022 fit to ranked-matchup data); [0.25, 0.75] = explicit
**coin flip**. Yields the honesty line ("~42% of games are coin flips"). Appended to the bayes
report automatically.

- **Sig-digit mandate for the published issue:** every reader-facing number ≤ 2 significant
  figures; prefer ranges ("about 11 wins, 9–12") and probabilities rounded to whole percents.
  Do NOT print model constants (σ, τ, HFA) as precise reader-facing numbers — describe them
  qualitatively. This is forcefully defended, not optional.

## 2025 validation (engine smoke test, `--year 2025 --mode bayes`)

Run against 2025's *actual* posted SP+, the Bayesian engine's **title pick was Indiana — the
team that actually won the 2025 national title — at ~25%** (Ohio State ~18%, Texas Tech ~13%),
with Indiana's win total ~11 (80% range 9–12) and an 81% Playoff probability. The honest
framing falls straight out of the numbers: a 25% favorite means the field is likelier to win.
~42% of rated games came back coin flips (JND pass). Runs in ~3 s for 4,000 iterations. This
is the proof the pipeline is sound.

## Known refinements to finish in the August build

1. ~~**Conference title games**~~ — **DONE 2026-08-06.** `conference_champions()` now sits the
   top two finishers in each league down at a neutral site and plays the title game, so the
   regular-season leader is a favourite rather than a lock. Resolved ONCE per iteration in
   `simulate_bayes` and passed into `build_field`, so the champion that gets seeded is always
   the same one the conference-title tally counts (calling it twice would have drawn two
   independent winners). Conferences under `MIN_CONF_TEAMS=4` are skipped — the 2025 Pac-12
   had two members and a realignment remnant must not be able to award an auto-bid.
2. ~~**Group-of-5 auto-bid**~~ — **DONE 2026-08-06.** The five auto-bids are now the four
   best champions plus the highest-rated champion from outside `P4`, instead of top-5-by-rating.
   At-large then fills to twelve via `12 - len(champs)` rather than a hardcoded 7.
   *2025 re-validation after both changes: Indiana still the title pick at ~25%, Ohio State
   ~17%, Texas Tech ~13% — the documented baseline is preserved.*
3. ~~**At-large by quality**~~ — **DONE 2026-08-06, by user decision.** This entry had
   previously been marked done when it was not: `build_field` was still sorting at-large
   candidates **wins-first**, which is what put North Texas at 56% Playoff in the 2025 test.
   The G5 auto-bid fix did not move it, because the bid was coming through at-large.
   User chose a **blend** over pure-SP+ or status quo, on the grounds that the real committee
   weighs both: at-large candidates now rank on `wins + theta/ATLARGE_W` with `ATLARGE_W = 8.0`,
   i.e. **about 8 SP+ points of strength is worth one win**. The same key seeds them, so
   selection and seeding can't disagree.
   *2025 effect, exactly the intended direction:* North Texas 56% → **50%**, Ole Miss 45% →
   **55%**, Oregon 31% → **47%**, Notre Dame 70% → **74%**. Title picks unchanged (Indiana
   ~25%, Ohio State ~17%, Texas Tech ~12%), so the validated baseline still holds.
   `ATLARGE_W` is the one knob here — lower it to punish soft schedules harder. It was not
   tuned to any single team's number.
4. **Independents** — already handled: Notre Dame (no conference) is excluded from champ
   logic and can only enter as an at-large.
5. Consider blending SP+ with **Vegas season win totals** as a second prior when they post.

## Scheduled cloud routine (set 2026-07-19)

A one-time cloud routine is scheduled to build + publish this automatically:
`trig_014MmrwW5Ln87kzjcArdEWRg`, fires **2026-08-29 05:30 UTC (1:30am EDT, Sat)** —
before the autopublish bot's earliest run, so the sim becomes that day's issue and the
bot stands down via its same-day `already_published_today` guard (the routine commits with
a `Publish Issue #N:` prefix, which the guard detects). Model: claude-sonnet-4-6.
Manage at https://claude.ai/code/routines/trig_014MmrwW5Ln87kzjcArdEWRg

**BLOCKER the human must clear: `CFBD_KEY` in the cloud environment.** The cloud agent does
NOT inherit the local `~/.zshrc` key, and a secret cannot be embedded in the routine prompt.
Provision `CFBD_KEY` in the routine's cloud environment before Aug 29, or the routine will
open a `publish-failure` GitHub issue and publish nothing (it will NOT fabricate numbers).
Re-arm the routine each year (or convert to recurring) for future seasons.

## Build-day checklist (last weekend of August)

1. Sync repo (fetch/pull --ff-only).
2. `CFBD_KEY=... python3 scripts/cfb_preseason_sim.py --year 2026` → capture the forecast.
3. Triple-verify the marquee numbers (title pick, top seeds) against SP+/FPI/Vegas.
4. Draft the issue in The Columnist voice: the forecast, the coin-flip honesty, the
   championship pick with a date on it. Figure = seed board or the coin-flip fraction.
5. Wire hover-(i) to `communicating-uncertainty` ("a projection, not a promise") and to
   `information-and-surprise` (the coin-flip games).
6. Add PUBLISH-META (topic: CFB), queue as a CFB piece, mind the variety rule.
7. This becomes the weekly grading baseline — note it in the Sunday Edition workflow.

This file lives in `tracking/` so the autopublish bot ignores it.
