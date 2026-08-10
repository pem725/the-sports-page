# Frame bank — the 48 recurring pieces

Every entry is an event that is **certain to happen** inside its window, with the
actor unknown. That is what makes it pre-writable. Generated from
`data/headline-cycle-2025-26.csv`; windows shifted forward one year.

`BUILT` = a frame exists in `frames/`.  `GAP` = a sport we have never covered.

| Fires | Sport | The recurring event | Status |
|---|---|---|---|
| Aug 2026 | MLB | MLB pennant races tighten as September call-ups loom |  |
| Aug 2026 | NFL | NFL preseason games begin league-wide; rookie QB and depth battles in focu |  |
| Aug 2026 | Tennis | US Open tennis begins in Flushing Meadows | GAP |
| Aug 2026 | College Football | Teams open fall camp with season openers one week away |  |
| Aug 2026 | Tennis | US Open tennis heads into its second week | GAP |
| Aug 2026 | College Football | College football's opening weekend kicks off the 2025 season (Aug 30) |  |
| Sep 2026 | Tennis | Aryna Sabalenka defends her US Open women's title, beating Amanda Anisimov | GAP |
| Sep 2026 | NFL | NFL Week 1 kicks off the 2025 season |  |
| Sep 2026 | NFL | NFL Week 2 storylines take shape |  |
| Sep 2026 | College Football | Rankings shuffle after upset-filled weekends | **BUILT** |
| Oct 2026 | MLB | MLB regular season ends and wild-card round begins |  |
| Oct 2026 | College Football | Conference races intensify heading into November |  |
| Oct 2026 | NBA | NBA regular season tips off | skip (NBA) |
| Nov 2026 | NFL | MVP race narrows to Drake Maye and Matthew Stafford |  |
| Nov 2026 | NFL | Week 10 playoff picture takes shape |  |
| Nov 2026 | College Football | CFP rankings debate top contenders, incl. undefeated Indiana and Ohio Stat |  |
| Nov 2026 | NFL | Weeks 11-12 storylines continue |  |
| Nov 2026 | College Basketball | Season tips off with early-season tournaments | GAP |
| Dec 2026 | College Football | Big Ten and SEC title games shape the College Football Playoff field |  |
| Dec 2026 | NFL | Week 15 playoff races heat up in both conferences |  |
| Dec 2026 | NFL | Week 16 division races intensify |  |
| Dec 2026 | College Football | Bowl season begins |  |
| Dec 2026 | NFL | Week 17 playoff seeding battles continue |  |
| Jan 2027 | NFL | NFL playoffs open with Wild Card Weekend |  |
| Jan 2027 | NFL | Divisional Round narrows the Super Bowl field |  |
| Jan 2027 | NFL | Super Bowl LX week begins with Seahawks-Patriots buildup |  |
| Feb 2027 | Olympics | Winter Olympics open in Milan-Cortina (Feb 6) | GAP |
| Feb 2027 | NFL | Super Bowl LX buildup continues; Bad Bunny halftime show a major storyline |  |
| Mar 2027 | NHL | Playoff races tighten across both conferences |  |
| Mar 2027 | College Basketball | Conference tournaments begin | GAP |
| Mar 2027 | College Basketball | March Madness tips off with the First Four and opening rounds | GAP |
| Apr 2027 | NBA | Playoff seeding races conclude | skip (NBA) |
| Apr 2027 | NHL | Stanley Cup playoffs begin (Apr 18) |  |
| Apr 2027 | NBA | Playoffs open across both conferences | skip (NBA) |
| Apr 2027 | NBA | First-round playoff series continue | skip (NBA) |
| Apr 2027 | NHL | First-round playoff series continue |  |
| May 2027 | NBA | Conference semifinals get underway | skip (NBA) |
| May 2027 | NHL | Conference semifinals get underway |  |
| May 2027 | Golf | PGA Championship week begins in Newtown Square, PA | GAP |
| May 2027 | NBA | Conference finals begin | skip (NBA) |
| May 2027 | NHL | Conference finals begin |  |
| Jun 2027 | NBA | NBA Finals begin between the Knicks and Spurs (Jun 3) | skip (NBA) |
| Jun 2027 | Soccer | FIFA World Cup kicks off across the US, Mexico, and Canada (Jun 11) | GAP |
| Jun 2027 | Soccer | World Cup group stage wraps up and knockout rounds begin; USMNT run a majo | GAP |
| Jul 2027 | MLB | All-Star break arrives at the season's midpoint |  |
| Jul 2027 | MLB | Pennant races intensify as contenders position for the trade deadline |  |
| Aug 2027 | NFL | Training camps and preseason games begin league-wide |  |
| Aug 2027 | MLB | Pennant races head into the season's final stretch |  |

**48 recurring events.** 3 built, 45 to go.

## Build order (soonest first, weighted to gaps)

1. `cfb-september-loss-base-rate` — **BUILT**, fires on the first top-10 upset
2. `nfl-week1-overreaction` — **BUILT**. Finding inverted the premise: Week 1 predicts a *lot*, and the gap survives controlling for the spread
3. US Open tennis — first entry into a GAP sport. **BLOCKED:** the public ATP match CSVs (JeffSackmann/tennis_atp) 404 on every raw URL tried and the GitHub API would not return the default branch. Needs either a working source or the file dropped in by hand, the way the headline dataset arrived
4. MLB elimination math — what 'still alive' actually means in late September
5. `mlb-mvp-race-already-over` — **BUILT**. The Aug-31 OPS leader wins 54% of the time and the winner is already in the top three 86% of the time; September rarely introduces a new name
6. NFL trade deadline — the log5 swing, reusing the Skubal machinery
7. First CFP rankings — how much the first poll predicts the final field
8. Rivalry week — Notre Dame's series records against the numbers

## Rules

- A frame never sits in `queue/` until its slots are filled.
- `scripts/autopublish.py` hard-fails on any `{{SLOT}}` that reaches the queue.
- Bake the historical evidence in at build time; re-verify before publishing.
- Each frame names its own trigger, so the fill step is mechanical.
