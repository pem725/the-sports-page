# Box Score Anatomy — one stat per issue

Started 2026-10-25 on the editor's brief. His words, compressed:

> "Take runs batted in. What is an RBI? How do you get it? What is it an indicator of? Are there other
> indicators of these things? Get people to start thinking in terms of the constructs... It's a proxy
> variable... Introduce people slowly, slowly. This is stats. We can show people DAGs soon and structural
> equations models and distributions."

## The idea

Every stat is an **indicator** (box) of things we cannot see directly — **constructs** (ovals): power,
contact, plate discipline, clutch, hustle, durability. The series walks the box score one stat at a time,
then starts connecting them. Primer: `concepts/constructs-and-indicators.html` (Concept No. 28).

## The four questions, every issue

1. **What is it?** The rule, plainly. How the scorer credits one.
2. **How do you get one?** What has to be true on the field — including the parts that are not you.
3. **What is it a sign of?** The constructs feeding it, drawn as ovals → box. Whose ingredient is each?
4. **What else is a sign of the same thing?** Other indicators of the same construct, and whether they agree.

Each issue still obeys every house rule: one question, our own computed number, sixth-grade prose, a
figure, a takeaway, limits stated. Keep each short. Depth goes in the primer.

## The ladder (what readers learn, in order)

| Stage | Idea | Picture | Roughly when |
|---|---|---|---|
| 1 | A stat stands for something (indicator → construct) | one box, ovals feeding it | issues 1–4 |
| 2 | One construct, several indicators — do they agree? | several boxes from one oval | 5–8 |
| 3 | Reliability: does the stat repeat next year? (year-to-year correlation) | scatter, this year vs next | 6–10 |
| 4 | Distributions: what a normal season looks like | histogram with the player marked | throughout |
| 5 | Causal arrows between constructs (DAGs): lineup → RBI ← power | small DAG | ~10+ |
| 6 | The measurement model and the structural model in one picture (SEM) | ovals, boxes, arrows | the capstone |

## The slate (draft order — reorder freely; MLB first while it is fresh)

**Baseball — hitting**
1. **RBI** — composite; teammates + lineup + power. *Queued: `186-rbi` (Thu 10/29).*
2. **Home runs** — *Queued: `187-home-runs` (buffer; needs a non-MLB issue before it).* the cleanest power indicator? Reflective: power → HR, but also park, era, the ball. The 1998 lesson: everyone counted homers while doubles and walks went unseen (Bonds).
3. **Batting average** — contact, plus luck on balls in play. Why .300 is a myth of round numbers.
4. **Hits (Ichiro, Rose)** — volume vs rate; hits reward playing every day and never walking.
5. **Walks** — plate discipline; the stat that RBI punishes.
6. **Stolen bases** — speed or the green light? Rule changes (2023) as a natural experiment.
7. **Triples** — speed, parks and luck; the rarest common stat.
8. **Clutch (RISP)** — does performance with runners in scoring position repeat year to year? Construct with weak indicators. Editor flagged "guys who wilt"; test it, do not assert it.

**Baseball — pitching**
9. **Wins** — a team stat with a pitcher's name on it (RBI's twin).
10. **ERA** — the denominator; fielders' fingerprints.
11. **Saves** — a stat that created a job.
12. **Strikeouts** — the cleanest pitching indicator.

**Football**
13. **QB wins** — the composite problem, louder.
14. **Passer rating** — a formula nobody can recite; what it weights.
15. **Rushing yards** — the line's stat with the back's name on it.
16. **Tackles** — more tackles can mean a worse defense.
17. **Time of possession** — effect mistaken for cause.

**Hockey**
18. **Plus/minus** — the most famous composite in sport.
19. **Save percentage** — the defense in front of the goalie.

**Cross-sport constructs** (stage 2+)
- **The hot hand** — real, small, and mostly invisible in the indicators fans use.
- **Clutch / wilting** — one construct, many sports, the same weak indicators.
- **Hustle** — the construct with no box at all.

## Rules for the series

- **Our number, every time.** Each issue computes something (a decomposition, a year-to-year
  correlation, a pair of players with the same skill and different counts). No definition-only issues.
- **Name both sides of the arrow.** For every stat, whose ingredient is each oval: the player's, the
  team's, the manager's, the park's, luck's.
- **Never headline the apparatus.** The series name lives in the kicker, never the headline.
- **Clutch gets tested, not asserted.** No naming of "chokers" without a repeatable indicator.
- **Invite outside voices later.** The editor wants to ask Andrew Gelman and others for ideas once the
  series has a few issues to show them. Draft the ask when stage 2 is running, not before.
