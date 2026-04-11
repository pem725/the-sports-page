# The Past Is Cheating — The Stats Desk Manifesto Piece

> **About this document.** This is an editorial Architecture Decision Record (ADR). See `planning/jimmys-and-joes-series.md` for the full explanation of how ADRs work on this project.

**Status:** Active — planning locked, piece not yet drafted
**Created:** 2026-04-11
**Frozen at launch:** Will freeze when the piece runs (target ~Apr 22–28, 2026)
**Target run window:** ~Apr 22–28, 2026 (post-EO series, pre-summer dry spell) OR evergreen reserve
**Voice:** Pure Professor. No Sal.
**Length:** Probably longer than a standard issue — this one earns extra words because it's foundational

---

## Why this piece exists

The Stats Desk needs a stated epistemology — a piece that says out loud what the newsletter believes about the relationship between data, prediction, and accountability. Right now that epistemology exists in practice (every Sunday recap grades the prior week's predictions), but it is not written down. This piece writes it down.

The editorial stance, in the words used during the 2026-04-11 planning session:

> "I want to describe and make predictive models of the past and then make predictions about the future and hold my predictions accountable. I made predictions and I accept being wrong. The past doesn't always predict the future but it sure as hell often outperforms a guess. Here's hoping but we will test vigorously."

> "These are great opportunities to discuss overfitting (the past) to prediction without understanding (black box treatments that lead to no eventual control — just good prediction). Ultimately, we scientists want to control after we describe and predict."

This piece is the philosophical foundation that every future predictive piece can rest on. Once it exists, every Index tracker piece, every EO-series prediction, every Sunday recap's accuracy report card has a reference frame. It's the piece that makes the Stats Desk feel like a *project* rather than a collection of clever one-offs.

## Working title

**"The Past Is Cheating"**

Alternative titles considered:
- "The Overfitting Problem"
- "Describe, Predict, Control"
- "I Will Be Wrong (And That's The Point)"

"The Past Is Cheating" wins because it's the most hook-like — it's counterintuitive, it immediately raises a question, and it sets up the entire argument in three words. The subtitle can carry the framework: *"A Stats Desk Manifesto on Description, Prediction, and Being Publicly Wrong."*

## The three movements

### Movement 1 — The hierarchy: describe → predict → control

Open with the three things a scientist wants from data, in order of ambition:

1. **Describe** what happened. Easy. Backward-looking. Baseball batting average is description. "Notre Dame went 10-2 last year" is description. Nothing at stake — the data already exists.
2. **Predict** what will happen. Harder. Forward-looking. You build a model on what you know and you apply it to something you don't know. The model can be simple (Bum Phillips saying "it's the Jimmys and the Joes") or complex (a 40-feature gradient-boosted tree). The question is: does it work when the future arrives?
3. **Control** why it happens. Hardest. Mechanism. Understanding the causal structure so you can intervene — change an input and predictably change the output. A program that knows WHY recruiting matters can change its recruiting strategy; a program that only knows recruiting is CORRELATED with winning can't.

**Key claim:** Most sports statistics stop at #1. Most advanced analytics stop at #2. The interesting work lives at #3, and the best we can usually do is #2 with honesty about which is which.

### Movement 2 — The overfitting confession

This is where the title pays off. "The past is cheating" because historical data already knows the answer — any sufficiently flexible model can fit it perfectly. The test isn't fit, it's prediction.

**Concrete example to use:** Take a recruiting-rank-vs-wins model trained on 2015–2020 CFB data. Show how well it "predicts" 2019 (perfectly — 2019 was in the training set). Then show how well it predicts 2024 (probably badly, because the transfer portal changed the game). The gap between the two is the overfitting — the model memorized conditions that no longer hold.

**The moral:** Historical fit is not the same as predictive power. Anyone selling you a model because it "would have predicted" past championships is selling you the crib sheet, not the understanding. A test of a model's honesty is whether it was willing to be wrong about something BEFORE it knew the answer.

**Bonus beat on black boxes:** A neural net that predicts the 2026 champion without explaining why has reached level 2 but not level 3. It might be right, but you can't learn from it. Control requires understanding; prediction alone doesn't. This is why the Stats Desk will always try to explain mechanisms, not just output numbers.

### Movement 3 — The accountability pledge

This is the closing movement and the one that makes the piece actionable. The pledge itself, in near-final form:

> The past often outperforms a guess — but only if you're honest about how it failed. The Stats Desk makes predictions publicly, dates them, and grades them in public. Every Sunday recap includes a prediction accuracy report card. Every predictive piece in this newsletter will eventually be judged by how it aged. When I'm wrong, I'll say so. The goal isn't to be right — it's to improve the model next time.

Concrete commitments the piece should make:
1. **Every predictive piece names an explicit, dated prediction.** No weasel words.
2. **Every prediction is revisited at its natural evaluation point** — the game, the season, the signing day.
3. **Sunday recaps grade past predictions.** (Already true; this piece formalizes it as doctrine.)
4. **Wrong predictions are not quietly deleted.** They are analyzed. *Why* was I wrong? What did the model miss? What changed between training data and reality?
5. **The Stats Desk commits to improving the model, not defending the prediction.**

## Structural notes

- **Opening hook:** Start with a specific prediction the Stats Desk got wrong (or a famously wrong prediction from sports history — "Bills will win Super Bowl XXVI," "Kentucky Derby 2019 results will stand," etc.) Use the concrete wrong-ness to earn the abstract argument.
- **Midpoint example:** The overfitting demonstration with real CFB recruiting data
- **Close:** The accountability pledge, framed as an invitation — "Grade me. That's the point."

## Why this piece runs early (Apr 22–28 recommendation)

Three reasons:
1. **Groundwork utility.** Every piece after it can cite the framework. Running it late means you lose that leverage on all the intervening pieces.
2. **Post-EO series lull.** The week after the EO series wraps is a natural reset moment — readers are primed for a step-back, meta piece that explains what the Stats Desk is actually trying to do.
3. **Before the J&J series needs it.** J&J Part 1 drops ~Jun 22. If the manifesto runs in late April, the vocabulary is fully embedded by the time the J&J series starts using it casually.

**But:** The piece is also evergreen and can live in reserve. If late April gets displaced by a live news hook, the piece holds and drops during the first dry spell.

## Ties to existing content

- **Sunday recaps** — already include prediction accuracy grading. This piece formalizes that practice as a stated commitment, not just a habit.
- **EO series** — made specific predictions about transfer portal reduction, NIL Gini movement, ND's EO exposure. The manifesto provides the frame for grading those predictions later.
- **J&J series and Index** — built on this piece's vocabulary. The manifesto is the opening move.
- **Any future "is X overrated" piece** — now has a principled framework to lean on rather than ad-hoc argumentation.

## Open questions

1. **Length:** Standard issues are ~500 words. This one probably wants ~800–1,000. Worth making an exception? I think yes — foundational pieces earn extra words.
2. **Visuals:** The overfitting demonstration wants a chart (training accuracy vs test accuracy on the CFB recruiting model). That's a small data task to line up before drafting.
3. **Does the piece mention the J&J series by name**, or stay general? I'd stay general — this piece is the foundation for the whole newsletter, not just one series. Let J&J Part 1 cite the manifesto, not the other way around.
4. **Voice check:** Pure Professor. But the Professor can be WARM here — this is him telling you what he actually believes, not lecturing from a distance. The accountability pledge in particular should feel personal, not institutional.

## Data needed before drafting

- [ ] A real CFB recruiting-rank → wins model trained on 2015–2020, tested on 2021–2024. The overfitting demonstration needs actual numbers to be honest, not hand-waving.
- [ ] A list of 2–3 Stats Desk predictions already made (from the published back catalog) that can be reviewed as concrete examples. Which ones are already gradable? Which are still pending?
- [ ] One famously wrong historical sports prediction for the opening hook (options: Bills dynasty, Celtics 2008 threepeat talk, any preseason top-25 poll that aged horribly)

## Status

- Planning doc complete
- Not yet drafted
- Target slot: Apr 22–28, 2026 (preferred) or reserve evergreen
- Voice, length, and three-movement structure locked
- Data pipeline work needed before drafting
