# Editorial Calendar 2026–27 — built from the headline cycle

Source: `us-sports-headlines-past-year.xlsx` (103 headlines, two per week, Aug 2025 → Aug 2026).
Cleaned and classified into `data/headline-cycle-2025-26.csv`.

This answers the question from the thread — *"I wonder if there is a cycle we can roughly
estimate"* — and Sean's follow-up that the list needs **under-reported sports** added.

---

## 1. Yes, there is a cycle. It's about three-quarters of the year.

Every headline sorts into one of three kinds, and the split is the useful finding:

| Kind | Count | Share | What it means |
|---|---|---|---|
| **FIXED** | 27 | 26% | Date knowable a year out. Super Bowl, Masters, Selection Sunday, Opening Day. |
| **RECURRING** | 48 | 47% | *Certain to happen inside a window; actor and timing unknown.* "Upsets reshuffle the rankings." "Trade deadline shakeup." "MVP race narrows." |
| **OUTCOME** | 28 | 27% | Genuinely unforecastable. Knicks' first title since 1973. A 30-1 Derby winner. |

**73% of the sports year is writable in advance.**

The middle row is the important one, and it's exactly what Sean identified: *unscheduled
but entirely predictable.* Nobody knows which Top-10 team loses in Week 2, but somebody
always does, and the rankings always reset. That is a piece you can build the skeleton of
in August and drop the names into in September.

This is also the newsletter's natural home. A pre-written frame plus a fresh number is the
whole format.

---

## 2. Two gaps, and the second one is bigger than it looks

### Gap A — we write about baseball five times more than the world talks about it

| Sport | Share of national headlines | Share of our 134 issues |
|---|---|---|
| NFL | **21%** | ~14% |
| College Football | **17%** | ~25% |
| MLB | **11%** | **~55%** |
| NBA | 10% | 0% (policy) |
| College Basketball | **10%** | **0%** |
| NHL | 7% | ~12% |
| Soccer / Golf / Tennis / Horse Racing / Auto | **19%** | **~0%** |

Some of that skew is deliberate — this started as a family newsletter with the Mets and
Notre Dame at the centre, and that was the right call. But the stated ambition now is
*"All sports. All stats."* with a growth campaign behind it, and against that ambition the
mix is off. MLB is over-weighted about 5×, and roughly **a third of the sports year
happens in sports we have never once covered.**

### Gap B — college basketball is not actually banned

The editorial rule says **no NBA**. It says nothing about college basketball. That's 10% of
the national conversation, an entire month (March 2026 was 7 of 8 headlines), and we have
published **zero** issues on it.

March is currently a dead month for us. It doesn't have to be. Selection Sunday bracket
math is one of the pre-planned tentpoles already written into `CLAUDE.md`, and it has never
been executed.

### The genuinely open space

11 of 103 headlines (11%) **do not recur in 2026–27**:

- **Winter Olympics** (5 headlines, Feb 2026, Milan-Cortina) — next Winter Games 2030.
  February 2027 has a five-headline hole where the Olympics were.
- **Men's World Cup** (6 headlines, Jun–Jul 2026) — next 2030.

Partial replacement: the **FIFA Women's World Cup, 24 June – 25 July 2027, in Brazil** —
the first ever held in South America. Given WNBA coverage is already welcome under the
rules, that's a natural fit and a full month of runway.

February 2027 is the real vacancy. The Super Bowl fills part of it, and **Super Bowl LXI
falls on 14 February 2027 at SoFi Stadium** — Valentine's Day, which is a gift of a hook.

---

## 3. The next eight weeks (the queue runs dry around 20 August)

| Window | Kind | Event | Candidate issue |
|---|---|---|---|
| **Aug 22–28** | FIXED | Last weekend before Week 0 | **CFB Pre-Season Sim** — engine is built and validated; blocked only on CFBD posting 2026 SP+ |
| **Aug 22–28** | FIXED | NFL camps break | **NFL Pre-Season Sim** — same framework, second sport |
| **Aug 29** | FIXED | CFB Week 0 (UNC–TCU, Dublin) | Season-opener baseline: what a Week 0 result is worth |
| **Sep 3–5** | FIXED | CFB Week 1 | ND opener. Prediction scorecard begins |
| **Sep 5–12** | **RECURRING** | *Week 1–2 upsets reset the rankings* | **Sean's example.** Pre-write it now: how much does one September loss actually move a playoff probability? Answer is "less than the polls act like." |
| **~Sep 10** | FIXED | NFL Week 1 | Jets opener; pre-season sim's first grade |
| **Sep (late)** | RECURRING | MLB pennant races / final stretch | Mets are 20 back — the honest version is elimination math |
| **Aug 31–Sep 13** | FIXED | **US Open tennis** | **GAP sport.** First tennis issue: service-hold rates as a base-rate lesson |

Note how many of those are **FIXED or RECURRING** — every one can be drafted before the
event, which is exactly the buffer the queue needs.

---

## 4. Month-by-month, forward

Dates marked ✓ are verified. Everything else is the typical window and must be confirmed
before it anchors an issue.

- **Sep 2026** — NFL Weeks 1–4; CFB rankings churn; MLB final stretch; US Open tennis.
  *Recurring gift: "early MVP race narrows" — a piece on how bad September MVP odds are.*
- **Oct 2026** — MLB postseason + World Series; NBA opens (skip); WNBA Finals; CFB
  conference races. *Heaviest MLB month of the year — spend the baseball budget here, not in June.*
- **Nov 2026** — NFL trade deadline; first CFP rankings; rivalry week (Thanksgiving);
  CBB tips off. *Notre Dame's most-watched stretch.*
- **Dec 2026** — CFB conference championships; Heisman; CFP bracket; bowl season;
  NFL playoff seeding.
- **Jan 2027** — CFP quarterfinals → national championship; NFL playoffs.
- **Feb 2027** — **Super Bowl LXI, Sun 14 Feb, SoFi ✓.** *No Olympics this year — five
  headlines of open space. The Valentine's Day Super Bowl is the obvious centrepiece.*
- **Mar 2027** — Conference tournaments, Selection Sunday, March Madness.
  *The month we currently forfeit. Bracket math is already a planned tentpole.*
- **Apr 2027** — NCAA finals; the Masters; NHL playoffs begin; NFL Draft; MLB Opening Day
  (**newsletter anniversary — Year Two retrospective**).
- **May 2027** — Kentucky Derby; Preakness; PGA Championship; Indy 500; NHL conference finals.
  *Four GAP sports in one month.*
- **Jun 2027** — Stanley Cup Final; US Open golf; Belmont; College World Series;
  **Women's World Cup opens 24 Jun ✓**.
- **Jul 2027** — **Women's World Cup through 25 Jul ✓**; MLB All-Star break; trade deadline.
- **Aug 2027** — Camps open; pre-season sims again; the cycle restarts.

---

## 5. What I'd actually do with this

1. **Pre-write the RECURRING pieces.** 48 of them, all guaranteed, none date-locked. This
   is the answer to the queue running dry — a bank of frames waiting for numbers.
2. **Take college basketball off the bench.** It costs nothing, it's not banned, and it
   fills the emptiest month on the board.
3. **Pick two GAP sports and actually own them.** Tennis and horse racing are the cheapest
   entries — both are dense with base-rate and small-sample material, and neither has an
   incumbent doing statistical explainers for a general audience. This is the
   "Far Side of sports geekdom" position.
4. **Rebalance MLB seasonally** rather than cutting it. Heavy Oct, light Jun.
5. **Claim 14 February 2027 now.** A Valentine's Day Super Bowl at SoFi with no Olympics
   competing for attention is the single best-positioned date on the calendar.

---

*Rebuild the dataset: `data/headline-cycle-2025-26.csv` is generated from the source xlsx;
the classifier lives in the session notes. Source files kept at repo root.*
