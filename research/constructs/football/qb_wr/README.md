# Quarterbacks and receivers: what the stats measure, what repeats, and what the voters see (2026-11-26)

Same method as the running backs and defensive linemen (`../README.md`): primitives only, EFA
(scree, parallel analysis, MAP; oblique), split-half CFA, omega, same-player-next-season
reliability, AP All-Pro validation, then today's players pooled and shrunk.

**Status: preliminary, unpublished.** Every correlation reported here is plotted in `fig/`.

## Data

NFL regular seasons 2018–2026 (2026 through the data available on 2026-11-26), counted from
nflverse play-by-play by player id; PFR charting via nflverse `pfr_advstats` (bad throws,
throwaways, pressure, drops, broken tackles); Next Gen Stats (time to throw, aggressiveness,
completion over expected, separation, cushion, YAC over expected). QBs: 200+ dropbacks and 150+
attempts, 322 seasons (294 through 2025). Receivers: WR and TE with 50+ targets, 950 seasons; the
models use WRs (674 seasons through 2025). Counts checked against the record: Lamar Jackson 2024
(41 TD, 4 INT, 4,172 yards), Burrow 2024 (4,918), Chase 2024 (127 for 1,708 on 175 targets),
Bowers 2024 (112 for 1,194).

## Traps

- **A dropback is three things:** a pass attempt, a sack or a scramble. Sacks are not attempts
  and their yards are not passing yards; scrambles are rushes in the box score. Rates here say
  which denominator they use. Spikes are removed (they are official attempts and incompletions).
- **Composites:** passer rating, ANY/A, EPA, yards per attempt and target, and yards per snap are
  sums of the other numbers; they are criteria, not indicators. PFR "times pressured" includes
  sacks. Completion rate duplicates completion over expected; pocket time duplicates time to throw
  (both pushed loadings to 1 or above); raw YAC duplicates YAC over expected.
- **Depth is built into other rates:** deep throws miss more often (bad-throw rate and depth of
  target correlate .43), and deep targets are caught less. Both are modeled as cross-loadings,
  on principle.
- **Bookkeeping:** scrambles and sacks compete for the same failed dropbacks (residual
  correlation, as with complete vs intercepted in the team model).
- **2026 is incomplete in PFR:** season passing charting stops at 2025. 2026 bad-throw rate is
  estimated from the weekly file (bad throws over attempts less the 2025 league throwaway rate);
  in 2025 the weekly sums matched the season total for the median QB but ran as much as 19% under
  it for one, so a 2026 bad-throw rate can be understated (accuracy flattered). 2026 throwaways are filled with the 2025 mean for scoring only (throwaways load on
  "holds the ball", which the ranking does not use).
- **Drop rate** is PFR's: drops per target.

## Quarterbacks

**Constructs.** EFA: parallel analysis 5, MAP 4. The four-factor solution: accuracy, holds the
ball, moves the chains, and downfield. Downfield did not survive confirmation (depth of target
loaded 2.2), and pressure is partly the line, so the confirmed model has three:

- **Accuracy:** completion over expected, fewer bad throws.
- **Holds the ball:** time to throw, scrambles, throwaways.
- **Moves the chains:** TD rate, first-down rate, fewer sacks.

Split-half CFA: CFI .87 / .93 (all .92), SRMR .08–.10, RMSEA .11–.14; adequate, not good.
Accuracy and chains correlate .64; holds is nearly independent of both (−.1). Omega
hierarchical .42: there is no single "good quarterback" factor.

**Interceptions load on nothing.**

**What repeats (same QB, next season, 187 pairs; `fig/qb_reliability.svg`):** scrambles .80
[.74, .85], time to throw .64, holds the ball .64, throwaways .51, bad throws .48, moves the
chains .46, EPA per dropback .46, accuracy .44, ANY/A .41, yards per attempt .38, interceptions
.18 [.02, .32]. Style repeats best; interceptions barely repeat.

**Human judges (AP All-Pro QBs 2018–2025, 17 of 17 found; Wikipedia, one source;
`fig/qb_allpro_auc.svg`):** ANY/A .95 [.92, .98], EPA per dropback .94, touchdowns .92, moves the
chains .90 [.84, .95], yards per attempt .88, the two-construct score .86, passing yards .83,
accuracy .72, dropbacks .73, holds .60. Interceptions .14 (fewer picks marks an All-Pro). Unlike
running backs, **quarterback voters reward efficiency over volume**, and they punish interceptions
even though interceptions barely repeat. The construct adds to passing yards (p = .0002).

**Today (`data/qb_today.csv`):** accuracy + chains, dropback-weighted over 2024–2026 and shrunk
(season reliability .43). 28 active QBs with 200+ dropbacks in 2026. Four clear the average
starter: Brock Purdy, Joe Burrow, Drake Maye, Jared Goff. One falls below: Aaron Rodgers. Lamar
Jackson has fewer than 200 dropbacks in 2026 and is not on the list (his 2024 chain-moving score
was 1.9; the highest in the data are Ryan Fitzpatrick 2018, 2.6, and Purdy 2025, 2.5).

## Receivers (WR)

**Constructs.** EFA: parallel analysis 4, MAP 2; the same four appear for tight ends.

- **After the catch:** YAC over expected, broken tackles.
- **Gets open:** separation, cushion.
- **Hands:** catch rate, fewer drops, targets per snap.
- **Deep threat:** depth of target, TD rate.

Split-half CFA with depth also loading on hands: CFI .93 / .92 (all .94), RMSEA .09, SRMR .06.
Several loadings sit at the bound: broken tackles, catch rate and depth each nearly define their
construct, so these are thin. Omega hierarchical .48: no strong general receiver factor.

**What repeats (401 pairs; `fig/wr_reliability.svg`):** depth of target .67, targets per snap
.62, separation .60, gets open .61, yards per snap .52, receiving yards .50, deep threat .48,
catch rate .45, hands .45, after the catch .36, yards per target .26, TD rate .23, drops .13
[.01, .23]. Drops and touchdowns are mostly noise; earning targets and getting open are the player.

**What the constructs predict:** weighted to predict yards per target, depth takes almost all
the weight (yards per target rises with depth by arithmetic). Weighted to yards per snap instead
(R² .34): hands .43, deep .32, after the catch .19, gets open −.11. **Separation does not turn into
yards** once the rest is held fixed.

**Human judges (AP All-Pro WRs, 44 of 46 found; `fig/wr_allpro_auc.svg`):** receiving yards .98,
targets .95, yards per snap .95, targets per snap .87, receiver score .84 [.78, .89], EPA per target
.83, yards per target .82, hands .75, deep .74, after the catch .61, gets open .50. Like the
running backs, **receiver voters reward volume**. The score adds a little to yards (p = .02).
Getting open, a stable skill, is invisible to the voters.

**Today (`data/rec_today.csv`):** receiver score, target-weighted over 2024–2026 and shrunk (season
reliability .29). 45 active WRs. Two clear average: Puka Nacua and Jaxon Smith-Njigba (both 2025
first-team All-Pros). One falls below: Emeka Egbuka.

## Across positions

| | general factor (omega h) | best-repeating thing | noise | what voters reward |
|---|---|---|---|---|
| RB | .66–.71 | rushing yards (.38) | fumbles | volume |
| QB | .42 | scrambles (.80) | interceptions (.18) | efficiency |
| WR | .48 | depth of target (.67) | drops (.13), TDs (.23) | volume |

## Limits

- All-Pro lists come from Wikipedia alone (one source). The TE first team for 2021 and second team
  for 2020 did not parse; TEs are not validated here.
- Seasons, not routes: no route counts are public, so targets per offensive snap stands in for
  targets per route.
- QB constructs are entangled with the receivers, the line and the play-caller; nothing here
  separates them.
- The same player appears in several seasons; intervals resample seasons, not players.

## Files

`0_build.py` (data) → `1_qb_explore.R` → `2_qb_confirm.R` → `3_qb_reliab.R` → `4_allpro.py` →
`5_qb_judges.R` → `6_qb_today.R` → `7_rec_explore.R` → `8_rec_confirm.R` → `9_rec_reliab_judges.R`
→ `10_rec_today.R` → `11_figures.py` (uses `../../hs_scatter.py`). Raw downloads in `raw/`
(gitignored).
