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
