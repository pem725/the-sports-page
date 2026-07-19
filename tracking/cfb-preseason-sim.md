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

## Methodology (encoded in the engine)

- **Prior** = SP+ team-strength ratings (points above average) from CollegeFootballData.
- **Expected margin** of a game = `SP+(home) − SP+(away) + HFA` (HFA = 2.5; 0 at neutral sites).
- **Win probability** = `Phi(margin / SIGMA)`, `SIGMA = 13.5` (CFB margin SD). Same σ used
  in Issue #105's information piece — keep them consistent.
- **JND boundary = 0.75.** A game is a *confident call* only if the favorite clears 75%
  (the same P=0.75 threshold Issue #022 fit to ranked-matchup data). Everything in
  [0.25, 0.75] is an explicit **coin flip** — the model refuses to fake a call. This is the
  editorial spine: honesty about how many games are genuinely too close to call.
- **Outputs**: expected wins per team, projected conference leaders, a projected 12-team
  Playoff (5 conf champs + 7 at-large), a title pick, and the coin-flip fraction.

## 2025 validation (engine smoke test, `--year 2025`)

Run against 2025's *actual* posted SP+, the engine's **title pick was Indiana — the team
that actually won the 2025 national title.** Top strength board (Indiana, Ohio State, Texas
Tech, Oregon, Notre Dame, Georgia) matches the real contender set. ~42% of rated games came
back coin flips — the honesty line works. This is the proof the pipeline is sound.

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
