# Roadmap to Opening Day 2027

*Written 12 August 2026. The plan is: run one complete trip around the sports
calendar, lock down the intellectual property while doing it, and only then turn
on a marketing campaign and the story-testing harness.*

---

## Where this actually stands

| | |
|---|---|
| Published | **137 issues**, plus 26 concept primers |
| Rate | 6.92 issues/week, unbroken since 29 March 2026 |
| Opening Day 2027 | **232 days out** |
| Issues between here and there | ~228 |
| Count on Opening Day 2027 | **~365** — 73% of the way to 500 |
| Readership, week of 2–8 Aug | **1 unique pageview** on the most-read issue |

That last row is the one that matters, and it is the reason to write this down.

---

## The sequencing is right, for a stronger reason than stated

The instinct — *prove the format across a full year before marketing it* — is
correct. But the harness ("generate competing stories, stress test them, find out
who likes what") has a hard dependency that is worth making explicit, because it
determines the order of everything else.

**A/B testing is a hypothesis test, and hypothesis tests need a sample.**

Here is what it takes to detect a difference between two headlines, at 80% power
and the conventional 5% threshold, on email open rate:

| Baseline open rate | Lift to detect | Subscribers **per arm** | Total list needed |
|---|---|---|---|
| 40% | +2 points | 9,493 | **18,986** |
| 40% | +5 points | 1,534 | **3,068** |
| 40% | +10 points | 388 | **776** |
| 40% | +15 points | 173 | **346** |

Current readership is in the single digits.

So the harness cannot produce a signal yet — not because it is badly built, but
because **there is nothing to measure**. Run an A/B test on a list of twenty and
you will get a winner every time, and the winner will be noise. A newsletter whose
entire civic mission is teaching people to resist bad inference cannot be the
thing running an underpowered test and believing the result.

That flips one link in the chain:

> **IP → audience → harness → optimisation**
>
> not IP → harness → audience.

The harness is *phase two*, and its trigger is a number: **roughly 800 subscribers
makes a +10-point difference detectable; ~3,000 makes +5 points detectable.** Below
800, build the *content* machinery — the frame bank — and skip the measurement.

The good news is that the expensive half of the harness is already being built for
other reasons. See below.

---

## Phase 1 — now to Opening Day 2027

### 1. Intellectual property (the number-one item)

| Item | Status | Cost | Blocker |
|---|---|---|---|
| **Trademark — logo** | Package built, `filing/` | $250–350/class gov fee | Needs a clearance search + attorney + your signature |
| **Copyright — 167 works** | Package built, `filing/copyright/` | **$390** (6 × $65) | Needs your eCO account + signature |
| **Copyright — going forward** | Plan written | $780/yr monthly | Set the recurring reminder |
| **Copyright — logo as art** | Recommended | $45 | Not started |
| **Copyright — figures** | Options documented, decision open | $0–$1,190/yr | Needs a decision |

Both packages are built to the point where filing is data entry, not research.
Neither can be filed by me — each requires the applicant's certification and
payment. See `filing/README.md` and `filing/copyright/README.md`.

**Do the copyright first.** It is cheaper, it has no clearance dependency, it can
be done tonight without a lawyer, and it is the one with a clock on it — every
month that passes puts another ~30 issues outside the § 412 window permanently.

### 2. Publish the year

The calendar is already mapped in `tracking/editorial-calendar-2026-27.md`. The
tentpoles between here and Opening Day:

- **Late Aug** — NFL and CFB pre-season simulations (engine built, waiting on 2026 SP+)
- **Sep** — CFB Week 1, NFL Week 1, US Open tennis (a GAP sport, still unsourced)
- **Oct** — World Series. The heaviest MLB month; spend the baseball budget here
- **Nov** — CFP rankings debut, rivalry week
- **Dec–Jan** — bowls, CFP, NFL playoffs
- **14 Feb 2027** — **Super Bowl LXI at SoFi, on Valentine's Day, with no Winter
  Olympics competing.** The single best-positioned date on the board
- **Mar 2027** — March Madness at 76 teams. The month currently forfeited
- **Opening Day 2027** — Year Two retrospective + full-year prediction accounting

### 3. Build the frame bank

**This is the harness, in its content half.** A frame is a pre-written piece with
the evidence baked in and the specifics left as slots — so a recurring event can
be covered the day it happens instead of three days later.

Status: **4 of 48 built.** That is the single biggest lever on Phase 1, because it
is what makes 228 more issues sustainable at this cadence, and it is also
precisely the "generate lots of competing stories" machinery — once two frames
exist for the same trigger, you have variants to test the moment there is an
audience to test them on.

### 4. Grow the list to ~800

Nothing else in Phase 2 unlocks until this does. Worth its own plan; not written
yet, and deliberately not guessed at here.

---

## Phase 2 — after Opening Day 2027

### What the testing harness needs

Recorded now so Phase 1 can lay the groundwork rather than paint into a corner:

1. **Variant generation** — two or more frames per trigger. *Already the frame
   bank's natural shape; just needs the discipline of writing a second angle.*
2. **Assignment** — the site is static on GitHub Pages, so randomisation has to
   live in the email (Buttondown) or in a small client-side split. Email is the
   honest surface: subject line and hero image are testable, article body is not.
3. **Measurement** — GoatCounter gives per-path unique pageviews; Buttondown gives
   opens and clicks. Both are already wired.
4. **Analysis** — this is a Beta-Binomial problem, which is the newsletter's own
   house model. The posterior on "variant A beats variant B" is the natural
   output, and it degrades honestly at small n instead of pretending.
5. **A stopping rule, fixed in advance.** Peeking at an A/B test until it crosses
   significance is how most A/B testing goes wrong, and it is a subject this
   newsletter should write about before it is a practice this newsletter adopts.

### Bake it into the skill

Once the above works, the loop belongs in `SKILL.md`: draft two angles, ship one,
hold one, score both against the prior week, and let the frame bank keep whichever
wins. That is the "rotate different stories and find what gives the best bang for
the buck" the campaign needs — but it is a Phase 2 artefact.

---

## Merch — where it actually stands

Close to done, and the remaining items are yours rather than mine.

| Item | Status |
|---|---|
| Tee art, front + back | **Done.** `merch/tee-front-badge-url-natural.svg`, `merch/tee-01-masthead-natural.svg` |
| Garment chosen | **Done.** Gildan Softstyle, Natural — ΔE 3.5 from the site's own page colour |
| Halo corrected for the garment | **Done.** Otherwise DTG prints a pale ring |
| Polo art | **Done.** `merch/polo-01-badge-reversed.svg`, embroidered, navy |
| Printer instructions | **Done.** `merch/README.md`, including the knockout note |
| **Size breakdown from the four of you** | **Not started — this is the blocker** |
| **Quote and order** | Not started |
| Embroidery digitising | Shop does it; ask for the stitch count before approving |

One live constraint: **Natural stops at 3XL and has no XS.** If anyone needs
outside that range, that person's shirt has to be Off White or Navy.

---

## The honest risk list

- **The list is the bottleneck, not the content.** 137 issues at 6.92/week is a
  real publishing record. One unique pageview a week is a real distribution
  problem. Phase 2 is gated on solving the second, and no amount of the first
  fixes it.
- **§ 412 is expiring continuously.** Every month unfiled is ~30 issues that
  permanently lose statutory damages for anything that happened before filing.
- **The queue runs dry around late August.** The frame bank is the fix and it is
  4/48.
- **US Open tennis is still unsourced** — the ATP match CSVs 404. First GAP-sport
  entry is blocked on data arriving by hand.
