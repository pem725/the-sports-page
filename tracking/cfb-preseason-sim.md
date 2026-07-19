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

1. **Conference title games** — the current field takes the highest-rated team per conference
   as its "champ." The real bid runs through a conference championship game; add that round.
2. **Group-of-5 auto-bid** — the 5th champ slot is the top G5 conference champion. The engine
   currently lets raw SP+/expected-wins pick it (2025 test surfaced North Texas); tighten to
   the actual G5 title-game participants once schedules/odds firm up.
3. **At-large by quality** — already fixed: at-large is chosen by SP+ quality, not raw
   expected wins, so a G5 team padding wins on a soft schedule can't steal a bid.
4. **Independents** — already handled: Notre Dame (no conference) is excluded from champ
   logic and can only enter as an at-large.
5. Consider blending SP+ with **Vegas season win totals** as a second prior when they post.

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
