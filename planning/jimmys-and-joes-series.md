# Jimmys and Joes: A Statistical History of College Football's Talent-Access Loopholes

> **About this document.** This is an editorial Architecture Decision Record (ADR) — a frozen snapshot of the decisions, rationale, and open questions behind a planned series, committed to the public repo so contributors can see how a Sports Page series gets planned. It is not the finished piece; it is the *reasoning* behind the finished piece. Think of it as a public lab notebook.
>
> ADRs on this project follow three rules: (1) decisions are dated, (2) the document is frozen once the series launches — later changes become new documents, not in-place edits, (3) "wrong" entries stay in, because being wrong in public is part of the accountability pledge.

**Status:** Active — planning locked, series not yet launched
**Created:** 2026-04-11
**Decisions locked:** 2026-04-11 (see "Decisions locked" section below)
**Frozen at launch:** Will freeze when Part 1 runs (~Jun 22, 2026)
**Target run window (series):** Late June – Mid July 2026 (summer content bridge)
**Target run window (Index tracker):** Aug 2026 – Jun 2027 (full 2026–27 CFB season)
**Slot in editorial calendar:** Runs AFTER the April 2026 EO series (Issues #9–16) concludes; designed to anticipate the Aug 1, 2026 EO effective date and track its consequences across the 2026–27 season.

**Scope:** 3-part foundational series + 1 Sal teaser + **7-piece Index tracker** (pruned from an initial 12) + 1 optional reactive slot if news warrants + 1 Professor manifesto piece ("The Past Is Cheating"). Total project scope: **12 pieces** (13 with reactive slot used), ~2.4% of the 500-issue goal. Prune rationale: audience burnout concerns — tracker pieces serve as periodic *reminders* of a vital framework, not a full-time beat.

---

## One-sentence thesis

**College football dynasties are built by whoever finds the next talent-access loophole first — and they fall when everyone else copies the trick or the rules close it.**

This is explanatory (it explains past dynasties from Rockne to Saban) AND predictive (it tells us who wins the post-EO era: whoever finds the next edge).

## Why this series

1. **Dovetails with the April 2026 EO series.** The Cignetti piece (EO Part 4) argues "the drawbridge rises after the king enters." This series generalizes that claim — Cignetti is just the latest data point in a century-long pattern. Every era has a Cignetti.
2. **Summer content bridge.** Late June through mid-July is a dry spell: NBA Finals winding down, NHL Stanley Cup over, MLB All-Star break not yet here. This series keeps readers engaged while baseball heats up and builds anticipation for the Aug 1 EO effective date.
3. **Teaches real statistics through irresistible history.** Every mechanism is a testable variance-decomposition claim. The folk saying ("it ain't the X's and O's, it's the Jimmys and Joes") becomes the statistical hypothesis the series investigates.

## The core structural insight

Every era of college football dominance can be mapped to a **talent-access innovation** that the dominant program exploited before rules caught up. When the rule closes (or everyone copies it), the dynasty ends — UNLESS the program has already moved to the next loophole.

## Era taxonomy — the loophole ledger

| Era | Mechanism | Beneficiary | How it ended |
|---|---|---|---|
| 1920s–40s | **Regional monopolies** (limited travel, radio as broadcast weapon, "subway alumni" fundraising) | **Notre Dame** (Rockne), Army | Air travel, integration, and TV democratized reach |
| 1950s–60s | **Segregation as a talent moat** | Alabama, Texas, SEC schools (southern lock on white QBs; northern programs couldn't reach black players either) | 1970 USC-Alabama game, full integration |
| 1960s–70s | **Unlimited scholarships** (no cap on roster size) | Bear Bryant Alabama, Woody Hayes OSU | Scholarship limit 1973 (105 → 95 → 85 by 1992) |
| 1980s | **Outright cheating / bag games / boosters** | SMU, Oklahoma (Switzer), Miami | SMU death penalty 1987, NCAA enforcement era |
| 1990s | **Partial qualifiers / Prop 48 workarounds** | Florida State (Bowden), Miami, Nebraska | Academic standards tightened |
| 2000s | **Oversigning** (signing more than 85, cutting losers in August) | Alabama (Saban), LSU, Ole Miss | SEC banned oversigning 2011 |
| 2000s–10s | **Cost-of-attendance stipends + facilities arms race** | Alabama, Ohio State, Clemson | NIL replaced it |
| 2010s | **Grad transfer rule** (2006, exploited late) | Ohio State (Fields), Oklahoma (Hurts, Mayfield) | Became universal |
| 2021–26 | **NIL + unlimited transfer portal** | Indiana (Cignetti), Colorado (Prime), Ole Miss (Kiffin) | April 2026 EO |
| Aug 2026– | **???** | **This is the prediction** | — |

**Key observation:** Notre Dame appears in the first row. This is not an oversight — it is intentional and fair. Rockne-era ND was the most sophisticated talent pipeline of its time: radio network reach, train travel budget, "subway alumni" fundraising that funded scholarships other programs couldn't match. Handling ND fairly strengthens the thesis rather than diluting it. The point is that **everyone finds edges** — the question is just whether the edges are organizational genius (ND) or briefcases at the airport (SMU).

## Statistical hooks (testable claims, not just history)

These are the quantitative spines that make this Stats Desk material, not just sports journalism:

1. **Recruiting rank → wins R² by decade.** Prior: it has risen from ~0.25 in the 1970s to ~0.55 in the 2010s as information has gotten better. If that's true, "Jimmys and Joes" is *more* true now than when Bum Phillips said it. Data source: 247Sports / Rivals composite back to ~2002, earlier decades via Blue Chip Ratio or retro-constructed rankings.
2. **Dynasty half-life by era.** How long did each loophole last before it was closed or copied? Hypothesis: the half-life is shrinking. Bryant's run was ~25 years; Saban's ~15; Cignetti may get 2 before the portal closes.
3. **Gini coefficient of talent distribution over time.** The NIL Gini (0.31 per EO Part 2) fits naturally here as "the current chapter of an old story."
4. **First-mover premium.** What share of championships went to the FIRST program to exploit each loophole vs fast-followers? This is the Cignetti question in disguise — and the prediction mechanism for Part 3.

## Voice and tone

**Main narrator: The Professor** — academic, measured, rigorous. Variance decomposition, R² tables, "one might argue" hedging. The voice that can say "the data suggest Alabama's 2009–2011 roster advantage was largely attributable to signing class attrition practices" with a straight face.

**Intermittent cameo: Sal** — irreverent, sarcastic, once-every-2-3-weeks max. Sal NEVER narrates the main argument. Sal appears in pull-quotes and sidebars when the history gets absurd and the Professor's measured voice would undersell the insanity. Structurally: Professor does the R², Sal does the color.

**Sal appearance candidates for this series:**
- The SMU briefcase-at-the-airport story (1985–86)
- Switzer's "Sooner Magic" being mostly his rolodex
- Saban signing 32 guys for 25 spots and cutting the losers in August
- Colorado Prime's first NIL press conference

**Style analogy:** David Foster Wallace footnotes. Main text is dry and rigorous; footnotes/sidebars are where the jokes live. This separation protects the series' statistical credibility while keeping it fun.

## Structural choice: Option B (3-part arc)

Rejected alternatives:
- **Option A (6-part weekly):** Too much commitment for summer window; reader fatigue risk
- **Option C (anchor + recurring):** Loses the narrative arc; too close to just dropping one-offs

**Chosen: Option B, 3-part arc with close sequencing.**

### Part 1 — "The Variance Question"
**Hook:** Bum Phillips said "it ain't the X's and O's, it's the Jimmys and the Joes." Was he right? And has he become *more* right over time?
**Core:** Recruiting rank vs wins R² by decade. Show the information-efficiency argument — as scouting improved, talent predicted outcomes more reliably.
**Payoff:** Establishes the framework. If wins are mostly talent, then the question becomes: how do programs GET talent? That opens the door to Part 2.
**Professor-heavy. Little to no Sal.**

### Part 2 — "The Loophole Ledger"
**Hook:** Every dynasty was built on a talent-access mechanism that seemed legitimate at the time and looks sketchy in hindsight. Including Notre Dame.
**Core:** The era taxonomy table above, with each row getting a paragraph. Dynasty half-life chart.
**Payoff:** The pattern is visible — loopholes shrink, rules chase them, and the programs that thrive are the ones that find the next edge first.
**Professor narrates. Sal gets 2–3 sidebar cameos for the most absurd episodes (SMU, Oklahoma, Saban oversigning).**

### Part 3 — "The Next Edge"
**Hook:** August 1, 2026, the EO takes effect. Who finds the next loophole?
**Core:** First-mover premium analysis. Candidates for the next edge: international recruiting pipelines, NIL structured as legitimate employment contracts with state-sponsored universities, academic partnerships as de facto payment, private equity ownership models. Ties EXPLICITLY back to Cignetti piece (EO Part 4) — he's Exhibit A in the general theory.

**NAMES NAMED (decision locked 2026-04-11):** Part 3 identifies four specific programs as tracker subjects with distinct theses:

| Program | Thesis | Role |
|---|---|---|
| **Notre Dame** | Conservative NIL + HS-first recruiting + the EO favors this model. The counter-intuitive "boring" winner. | The quiet theory |
| **Ole Miss (Kiffin)** | Shameless experimentalist. First to probe whatever the next workaround is. | The experimentalist theory |
| **Oregon** | Phil Knight infrastructure means whoever finds the edge, Oregon can buy in first. | The capital theory |
| **Indiana (Cignetti)** | NEGATIVE case — can a portal-built program survive the freeze? If yes, the whole framework needs rewriting. | The control group |

Four is the right number: too few is boring, too many is diluted. Each program has a distinct predictive thesis that the Index (see below) will test across the 2026–27 season.

**Payoff:** Reader leaves with a framework for watching the 2026 season AND four specific programs to track. This is the piece that launches the Jimmys & Joes Index.
**Professor narrates. Sal closes with a one-line cameo — something like: "Whoever finds it, just remember: someone's grandkids will be writing dissertations about it in 2070."**

---

## The Jimmys & Joes Index (franchise tracker, expansion locked 2026-04-11)

The four named programs from Part 3 become ongoing tracker subjects across the 2026–27 season. The Index is a multi-dimensional scorecard that updates at natural CFB milestones. The editorial intent is a "broad and deep" tracker — high bandwidth on the underlying data, high fidelity on the measurement — that still respects the "one question per issue" rule by leading each tracker piece with a single dimension.

### Seven dimensions

| # | Dimension | Measurement | Update cadence |
|---|---|---|---|
| 1 | **Record** | W-L, normalized vs common opponents (SP+ adjusted) | Weekly |
| 2 | **Performance vs peers** | Composite of SP+, SRS, FPI; margin of victory vs expectation | Weekly |
| 3 | **Attendance** | Home attendance % of capacity; road-game draw | Per home game |
| 4 | **Press attention** | Google Trends index, ESPN mention volume, national TV window counts | Weekly |
| 5 | **Fan sentiment** | Social media sentiment ratio (positive/negative); message board volume | Weekly |
| 6 | **Recruiting** | 247 composite class ranking; week-over-week movement; portal activity | Weekly, plus signing days |
| 7 | **Player awards attention** | Heisman odds, position-award watchlist presence (Biletnikoff, Bednarik, Thorpe, Outland, etc.) | Biweekly |

Each program gets a composite Index score trackable over time. The scorecard itself becomes a recurring visual element.

### Design constraint: broad data, single-question pieces

The Index collects data on all 7 dimensions continuously, but **each tracker issue leads with ONE dimension** as the single-question focus (consistent with the "single-question focus" editorial rule). The full composite scorecard appears as a sidebar table that accumulates across issues but never dominates the lead. Rotation across the season ensures no dimension is stale.

### Tracker milestone calendar (2026–27 season) — pruned to 7

| Date (approx) | Event | Lead dimension |
|---|---|---|
| **Aug 30, 2026** | Week 0/1 kickoff | Press attention — preseason Index baseline |
| **Nov 5, 2026** | First CFP rankings released | Record + committee divergence from Index |
| **Nov 27, 2026** | Rivalry week (ND-USC, Iron Bowl, The Game) | Fan sentiment — the pressure test |
| **Dec 14, 2026** | CFP selection | Composite Index check — playoff representation |
| **Jan 20, 2027** | National championship | Season-end Index snapshot |
| **Feb 4, 2027** | National signing day | Recruiting — did Index programs land classes? |
| **Jun 1, 2027** | Post-EO one-year anniversary | **BIG RETROSPECTIVE: "The Jimmys & Joes Index — Year One"** |

**7 tracker pieces** (plus 1 optional reactive slot held in reserve for if a named program implodes mid-season). Pruned from an initial 12-date plan to avoid audience burnout. The dropped dates (Sep 13, Oct 4, Dec 6, Jan 1, Apr 15) were either too early to have meaningful data or redundant with adjacent milestones.

**Design principle for tracker pieces:** They serve as periodic *reminders* that this framework matters, not as a full-time beat. Each one should feel like a check-in, not a procedural update.

### The Year-End Retrospective (Jun 1, 2027)

The Jun 1, 2027 piece is the statistical payoff of the entire franchise. It answers:
- Which named program's thesis held up?
- Which dimension of the Index was most predictive?
- Did the Index beat the AP poll? The committee? The betting markets?
- What's the new prediction for Year Two?
- Does the franchise continue?

If this piece lands, the Index runs every year and becomes a recurring Stats Desk feature alongside The Sports Page itself.

### Relationship to "The Past Is Cheating" manifesto piece

A separate planning doc at `planning/stats-desk-manifesto.md` covers the manifesto piece that should run as groundwork for the entire J&J franchise (and the newsletter more broadly). Every piece in this series — and every tracker piece — should cite the manifesto's **describe → predict → control** framework where relevant. The manifesto establishes the vocabulary; this series demonstrates it.

**Recommended cadence:** Manifesto runs ~Apr 22–28, 2026 (after EO series wraps, after Sal teaser, before summer dry spell). By the time Part 1 of the J&J series runs in late June, every reader should already know what the Professor means by "overfitting the past."

### Tracker piece economics

Tracker pieces are **lower-cost per issue** than one-offs because:
- Scorecard template is reusable
- Data pipeline (once built) feeds every piece
- Visual elements accumulate rather than rebuild
- Single-dimension lead means less brainstorming per piece

This is why 12 additional pieces is tractable within the 500-issue budget — the marginal cost of each tracker piece is meaningfully lower than a cold-start issue.

## Timing decision: 3b (hold for summer window)

**Why not 3c (anchor + recurring):** That's Option C in disguise. Just rejected it. The arc's power comes from close sequencing.

**Why 3b:** The summer dry spell (late June – mid July) is exactly where this series earns its keep. Readers are starved, baseball alone can't carry the newsletter, and the EO takes effect Aug 1 — so a June/July run builds anticipation for a real news event rather than competing with one.

**Proposed dates (to be finalized closer to the run window):**
- **Apr 15–16 (immediately post-EO series):** Short teaser piece setting the table. Possibly a Sal column: "The Professor's been in the archives. Something's coming this summer about every dynasty being built on a loophole, including the ones in gold helmets. Stay tuned."
- **~Jun 22 (Part 1 — The Variance Question):** Recruiting rank vs wins R² by decade
- **~Jun 29 (Part 2 — The Loophole Ledger):** Era taxonomy with ND included fairly
- **~Jul 06 (Part 3 — The Next Edge):** First-mover prediction piece

Exact dates will depend on what else is running and whether any live news hooks force rearrangement.

## Standalone spin-offs (between Parts 2 and 3 or later)

If news breaks during the run window (a program gets caught doing something, a new NIL workaround surfaces, a court ruling on the EO), drop Sal-flavored standalones that reference back to the series: "Today's reminder that this is just 1986 Oklahoma wearing new clothes." These aren't part of the arc but extend its useful life.

## Data and research needs (to do before drafting begins)

- [ ] Recruiting rank → wins R² by decade. Start with 247Sports composite 2002–present, extrapolate earlier decades via Blue Chip Ratio
- [ ] Dynasty half-life table — define "dynasty" operationally (e.g., top-5 finish in 3+ years of a 5-year window), then compute duration for each era's beneficiary
- [ ] SMU death penalty primary sources — verify the airport briefcase story is actual history, not apocrypha
- [ ] Oversigning numbers — SEC totals 2008–2011 before the ban
- [ ] Rockne-era ND financial records — at minimum, the "subway alumni" fundraising totals and the radio network reach. Fair treatment of ND requires real numbers, not just vibes
- [ ] Gini coefficient calculation for talent distribution — reuse EO Part 2 methodology but extend back as far as data allows

## Decisions locked (2026-04-11 planning session)

1. ✅ **Teaser piece (Apr 15–16) is a Sal column.** Sal gives the lead-in before the Professor takes over the 3-part arc. Ensure Sal's cameos in Part 2 are distinct enough in tone/topic to avoid overexposure.
2. ✅ **Part 3 names four specific programs** as tracker subjects: Notre Dame, Ole Miss (Kiffin), Oregon, Indiana (Cignetti, as negative control). See Part 3 section above for theses.
3. ✅ **Retrospective is a full-season Index tracker**, not a single August piece. Initially scoped as 12 tracker pieces, **pruned to 7** later in the same session over audience-burnout concerns. The seven dates are listed in the milestone calendar above; they culminate in a Year One retrospective Jun 1, 2027.
4. ✅ **Sal is eligible to take 2–3 of the tracker slots** as reactive pieces if field events warrant it (e.g., a named program collapsing mid-season). Dates to be chosen at publication time, not pre-assigned.
5. ✅ **The manifesto piece "The Past Is Cheating"** runs as groundwork for the entire franchise. See `planning/stats-desk-manifesto.md`.

## Open questions

1. **Exact run dates for the 3-part series** — depends on what else is in the queue when we get to mid-June
2. **Data pipeline build-out:** The Index needs a data pipeline before Aug 30, 2026. Sources to wire up: 247 composite API, SP+/SRS/FPI feeds, Google Trends, a social sentiment scraper, attendance data (ESPN/school reporting), Heisman odds feeds (DraftKings/FanDuel). This is a real build and needs to start by ~Jul 15 to be ready for the Aug 30 baseline piece. See the README's "Lane 2 — The innards crew" section; this is the single highest-leverage contribution someone with API/scraping experience could make.
3. **Whether the Index continues beyond Year One** — to be decided based on the Jun 1, 2027 retrospective's reception. If it lands, Year Two launches Aug 2027 with potentially new named programs.

## Tie-ins with existing content

- **EO Part 4 (Cignetti)** — direct predecessor. Series should reference it explicitly in Part 3
- **EO Part 2 (NIL Gini)** — provides one of the statistical hooks; cite in Part 2
- **cfb-coaching-stabilization** (reserve evergreen) — "Year 1 = 60% of coaching ability" finding is complementary; Part 1 could reference it
- **Any future "rules arms race" pieces in other sports** — this series establishes a template for investigating talent-access mechanisms in any league

## Why this matters beyond sports

The deeper point, and the reason this fits The Stats Desk's mission: **rule systems shape outcomes more than effort does, and the programs that understand this win.** This is a lesson that applies far beyond football — to finance, academia, corporate strategy, regulation. A reader who internalizes the Jimmys-and-Joes framework has learned something about how the world actually works, not just how football works. That's the Stats Desk brief: statistics that describe our world and the forces that really shape it.
