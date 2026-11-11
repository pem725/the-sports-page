# Sunday Edition — Next Centerpiece Brief

**Teed up: 2026-11-06 (Fri), before kickoff of Miami at Notre Dame.
For the Sunday Edition built the morning of 2026-11-15**, after the committee's
second rankings (Tuesday 2026-11-10, ~9pm ET). Set by the editor: *"Could it
happen to Miami after we pound the living daylights out of them?"*

> Planning brief, NOT finished copy. The Sunday Edition is built fresh. Every
> number below is a Friday snapshot taken BEFORE the game; re-pull the score,
> the Nov 10 rankings (CFBD `/rankings`, poll "Playoff Committee Rankings") and
> Toney's status, and grade the calls below against them. The calls are written
> down now so the grade cannot be shaded afterwards; this file's commit time is
> the record.

The previous brief (coin-flip pool) ran in Sunday Edition No. 030; it is in git
history.

## The question

**When a team loses its star, does the playoff committee punish it — and does
it discount the team that beats it?** The test case: Miami without Malachi
Toney, against the 2023 precedent of Florida State without Jordan Travis.

## What we know, Friday 2026-11-06

- **Toney:** high ankle sprain at practice Wed 11-04; surgery reported by ESPN
  (Pete Thamel's sources), CBS (Matt Zenitz) and Yahoo (Ross Dellenger). Reported
  timeline 4–6 weeks, aimed at the playoff (first round Dec 18–19). Miami has said
  only that he is being evaluated. No ACC availability report found (ND is not an
  ACC member).
- **Line:** DraftKings ND −7.5, −278/+225, about **70%** vig-free (Wednesday
  night −7, −258/+210, 69%). Total 54.5, from 55.5. Our SP+ model: ND **57%** —
  it does not know about the injury.
- **Committee, Nov 3:** 1 Miami (8–0), 2 Georgia, 3 Utah, 4 Indiana … 11 Notre
  Dame (7–1, last in), 12 Ohio State (first out). Chair Hunter Yurachek: Notre
  Dame lacks "that signature win."
- **Format:** 12 teams; 4 power-conference champions + top Group of Six champion
  get automatic bids; Notre Dame is in if it finishes in the top 12; the top four
  in the rankings get byes regardless of conference title.
- **Precedent:** 2023, 4-team field. FSU 13–0 and ACC champion, ranked 5th in
  the final rankings after Travis broke his leg. Chair Boo Corrigan: "a
  different team." The committee's letter to Sen. Rick Scott cited the protocol's
  "unavailability of key players" clause, which looks at *postseason* performance.

## The calls (graded Nov 15)

The two probabilities come from models; the rest are leans with **no model
behind them**, and the edition must say so.

1. **ND wins:** 70% (market) / 57% (our SP+).
2. **ND wins by 20 or more:** 22% (market spread, sd 16.5) / 15% (SP+).
3. **Lean:** if ND wins, ND moves up from 11th on Nov 10 — the win counts, it is
   not discounted for Toney's absence. The injury clause is about a team's *own*
   availability, not its opponent's.
4. **Lean:** Miami stays in the top 12 whatever happens Saturday. It cannot be
   left out the way FSU was: the field is three times larger and an ACC title is
   an automatic bid.
5. **Lean:** the FSU logic, if it bites at all, bites on the **bye**, not the
   bid. A clear Miami loss without Toney is direct evidence of a "different
   team," which FSU's committee never had; FSU still fell from 4th to 5th.
   Toney's playoff-timed return cuts the other way.

## Calls added Sun 2026-11-08, before the Nov 10 ranking

Result: Notre Dame 31, Miami 24. Call 1 hit; call 2 (by 20+) missed.

**The editor's calls for Tuesday's ranking (no model, his read):**
1 Georgia, 2 Utah, 3 Alabama, Notre Dame 5 (maybe 6 or 7: "they'll keep them on
the cusp"). Iowa from 19 to about 11. Ohio State and Oregon "done" at 6-3. UCLA
rising. No. 4 not called.

**The stand-in's ranking** (`scripts/cfp_sim.py`, strength of record on week 10
SP+, results through Nov 7, nothing simulated): 1 Alabama, 2 Utah, 3 Indiana,
4 Georgia, 5 Texas, 6 UCLA, 7 Notre Dame, 8 Miami, 9 Kentucky, 10 Texas Tech,
11 Oregon, 12 BYU ... 16 Iowa, 18 Ohio State. It ignores head-to-head and
margin, and the editor's case for Georgia at No. 1 rests on the margin.

**The simulation, before and after Saturday, for Notre Dame:** bid 84% -> 96%,
bye 20% -> 43%, final No. 1 under 1%. The Miami win gave +12 bid / +15 bye;
Oregon over Ohio State +6 bye; nothing else measurable.

**More calls, from the editor's Sunday-afternoon call with Patrick jr**
(recorded during it; the AP poll came out mid-call, so all of these were made
before the Nov 10 ranking):

- *The editor, revised:* 1 Utah, 2 Georgia, 3 Alabama, 4 Indiana, 5 Notre Dame,
  6 Texas. This replaces his morning call (Georgia 1, Utah 2). Grade the
  revision and show both: changing a call before the release is allowed, and
  saying so is the point.
- *Patrick jr:* Notre Dame's chance of No. 1 is "zero," and "the highest they'll
  go is four." Georgia 1, Utah 2; the transcript seems to have Miami 3 but is
  garbled there. His claim to test is that the committee will keep the Irish
  lower than the polls do.

**The polls, released Sun Nov 8** (ESPN rankings feed; a second feed is still
needed before anything is graded on them):
- *AP:* 1 Georgia (53 first-place votes), 2 Utah (12), 3 Notre Dame (5),
  4 UCLA, 5 Miami, 6 Indiana, 7 Alabama, 8 Texas, 9 Tennessee, 10 Texas Tech.
- *Coaches:* 1 Georgia, 2 Utah, 3 Notre Dame, 4 UCLA, 5 Indiana, 6 Miami,
  7 Alabama, 8 Texas, 9 Tennessee, 10 Texas Tech.

That makes the real test: the polls, Massey's consensus and Massey's own rating
all have Notre Dame 3rd or 4th. On Nov 3 the committee had the Irish 11th while
the consensus had them 6th. If the committee puts them 5th or lower, the gap
holds and Patrick jr's read wins. If it puts them 3rd, the committee has caught
up with everyone else.

**Third forecast: the computers, recorded Sun 2026-11-08 ~2:40pm ET.**
Neither one was built to predict the committee. Both are on file so Tuesday can
show whose read the committee was closest to.

- *Massey consensus* (masseyratings.com/ranks?s=cf, dated Nov 8, **45 systems
  in so far**; the Nov 1 edition had 91, so the order may shift as more report):
  1 Georgia, 2 Alabama, 3 Notre Dame, 4 Utah, 5 Texas, 6 Miami, 7 UCLA,
  8 Indiana, 9 Tennessee, 10 LSU, 11 Ohio State, 12 Ole Miss, 13 Oregon,
  14 Kentucky, 15 Wake Forest, 16 Texas Tech, 17 BYU, 18 Iowa ... SMU 33,
  Michigan 45, Syracuse 74, Boston College 87.
- *Massey's own rating* (masseyratings.com/cf/fbs/ratings, games through Nov 7):
  1 Georgia, 2 Utah, 3 Alabama, 4 Notre Dame, 5 Indiana, 6 Miami, 7 Ohio State,
  8 Texas, 9 UCLA, 10 Tennessee, 11 Ole Miss, 12 Oregon, 13 Iowa.
- Before Saturday, the Nov 1 consensus (91 systems) had Notre Dame **6th**,
  against the committee's 11th. The systems ranged from 1st to 31st.

**The simulation rerun on Massey's power ratings** (`cfp_sim.py --ratings
data/rating-snapshots/massey-2026-11-08.json`). Massey's power scale matches SP+
almost exactly: spread 12.3 vs 12.4 points, correlation 0.95.

| Notre Dame | SP+ (frozen wk 10) | Massey (thru Nov 7) |
|---|---|---|
| Bid now | 96% | 92% |
| Bye now | 43% | 15% |
| Beat BC: bid / bye | 97% / 45% | 93% / 15% |
| Lose to BC: bid / bye | 70% / 0% | 60% / 0% |

**The bid holds up. The bye does not.** The gap comes from the rivals, not from
Notre Dame: ND's rating (24 vs 25) and résumé so far (+1.8 vs +1.9 wins above a
top-25 team) barely change. Under Massey, Georgia (+2.5), Utah (+2.7) and UCLA
(+2.6) have stronger résumés, and Utah is 63% rather than 49% at Arizona. ND sits
on the edge of the top four, and on that edge small shifts in three or four
other teams cut its chance by a factor of three. Both rating sets agree on Boston
College: a loss costs 27 to 33 points of bid and the whole bye. Caveat: Massey's
ratings have already absorbed Saturday, so its "before Saturday" figures are not
a fair before-and-after. Only the "now" column is comparable.

## Where it goes

Block 3 of the football-season shape, the improbability lesson, or its own
section if the rankings move hard. Stat-card candidates: ND's rank Nov 3 → Nov
10; Miami's rank Nov 3 → Nov 10; the line's half-point for a 1,000-yard receiver.

## What to take home (draft idea)

A star's injury changes three numbers, and they are not the same size: the
line (half a point), the team's ranking, and the opponent's credit for the win.
Watch each one separately.

## Traps

- No poll or ranking cited before its release: Nov 10, ~9pm ET.
- Every score through `check_scores.py`.
- Do not quote the committee protocol from a web summary; find the CFP's own
  text or quote it as reported (Hancock's letter, via Rivals).
- No family team-allegiance name-dropping.

## Graded Wed 2026-11-11 against the Nov 10 committee ranking

**The ranking, confirmed on two feeds** (ESPN rankings feed and CFBD `/rankings`,
week 11, "Playoff Committee Rankings"; identical through 12):
1 Georgia, 2 Utah, 3 Alabama, 4 UCLA, **5 Notre Dame** (from 11), 6 Texas, 7 Miami
(from 1), 8 Tennessee, 9 Indiana, 10 BYU, 11 Kentucky, 12 Texas Tech ... 15 Iowa,
16 Oregon, 20 Ohio State.

| Call (all on file before the release) | Result | Grade |
|---|---|---|
| Editor, Sun morning: 1 Georgia, 2 Utah, 3 Alabama, ND 5 | all four exact | **HIT** |
| Editor, Sun afternoon revision: 1 Utah, 2 Georgia, 3 Alabama, 4 Indiana, 5 ND, 6 Texas | 3 of 6 exact; Georgia and Utah swapped; Indiana 9th | PARTIAL. **The first call was better than the revision.** |
| Editor: Iowa from 19 to about 11 | 15 | PARTIAL: direction right, half the distance |
| Editor: Ohio State and Oregon "done" at 6-3 | 20 and 16, both outside the 12 | HIT |
| Editor: UCLA rising | 8 to 4 | HIT |
| Patrick jr: ND No. 1 chance "zero"; "highest they'll go is four" | 5 | HIT |
| Patrick jr: committee keeps ND lower than the polls (AP 3, Coaches 3) | 5 | **HIT: his read wins the test this file set up** |
| Patrick jr: Georgia 1, Utah 2 | exact | HIT |
| Lean 3: ND moves up if it wins | 11 to 5 | HIT |
| Lean 4: Miami stays in the top 12 | 7 | HIT |
| Lean 5: any FSU-style cost lands on the bye, not the bid | Miami 1 to 7: out of the top 4, in the field | HIT, but a loss alone explains it; this does not isolate the injury |
| Stand-in (`cfp_sim.py`, SP+): 1 Alabama, 2 Utah, 3 Indiana, 4 Georgia, 5 Texas, 6 UCLA, 7 ND | 1 exact (Utah); ND off by 2 | MISS on order |
| Massey's own rating: 1 Georgia, 2 Utah, 3 Alabama, 4 ND | 3 exact; ND off by 1 | near HIT |
| Massey consensus: ND 3 | 5 | off by 2 |

**The lesson for Sunday:** the person, not a computer, called the top of this
ranking best, and his first instinct beat his own revision. One week, one ranking:
a story, not evidence of skill. Grade it again on Nov 17.
