# The stats road map

*Requested by Sean McKnight on the 17 September call. His words:*

> "I think it would be good if we had, like a road map so they could understand. And maybe even
> utilizing that same learning example across multiple different stories."

This is the ladder the registry already describes — an **issue** shows you the idea, a **primer**
teaches it, a **book chapter** gives the full treatment — arranged into a reading order, with the
holes marked.

---

## Where coverage actually stands

**23 of 27 concepts have at least one issue that demonstrates them. Four do not.**

That is a better position than the registry reported until today. Twenty-one entries read as having
zero issues when the links were sitting in the published HTML the whole time, so the file was
understating the newsletter's own teaching by a wide margin. The `issues` arrays are now rebuilt by
scanning `published/`. Re-run that scan after a publish rather than editing the arrays by hand.

---

## The four holes

Each of these has a finished primer and nothing in 177 issues that points at it. They are the
commissioning list.

| Concept | Theme | What a story for it would need |
|---|---|---|
| **Post Hoc Ergo Propter Hoc** (No. 5) | inference-traps | A sequence everyone reads as cause and effect. Coaching change followed by a winning streak is the obvious one, and the obviousness is the point. |
| **Nomothetic vs. Idiographic** (No. 27) | uncertainty | Where the league-wide average says one thing and one player's own history says the opposite. Sean's own framing on the call: what the group does tells you little about this guy. |
| **Heuristics: Biases vs. Ecological Rationality** (No. 19) | judgment | A scout's rule of thumb that beats the model in its own environment. This is the one that stops the newsletter reading as "experts are dumb," so it is worth doing well. |
| **Do We Believe the Data, the Model, or the Theory?** (No. 16) | epistemics | A case where all three disagree and someone had to pick. |

---

## The reading order

Sorted by how much material already backs each concept, so a reader who starts at the top always
lands on something with several worked examples behind it.


### inference-traps

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 1 | [Base Rate](base-rate.html) | 14 | `020-jets-first-round-busts` |
| 3 | [Regression to the Mean](regression-to-the-mean.html) | 13 | `053-raleigh-slump-shower-oblique` |
| 6 | [Sample Size](sample-size.html) | 9 | `026-stabilization-thresholds` |
| 4 | [Survivorship Bias](survivorship-bias.html) | 5 | `055-superstition-baseball-math` |
| 8 | [Counterfactuals](counterfactuals.html) | 5 | `084-peer-enforcement` |
| 9 | [Conditioning on the Consequence](conditioning-on-the-consequence.html) | 1 | `083-ncaa-enforcement-collapse` |
| 25 | [The Denominator Problem](denominator-problem.html) | 1 | `114-mets-royals-cost-per-title` |
| 5 | [Post Hoc Ergo Propter Hoc](post-hoc.html) | 0 | **none yet** |

### measurement

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 14 | [Measurement: Building a Metric](measurement-building-a-metric.html) | 3 | `097-acceleration-second-derivative` |
| 7 | [Precision vs. Accuracy](precision-vs-accuracy.html) | 1 | `134-ranking-jnd` |

### modeling

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 23 | [Variance](variance.html) | 5 | `113-pull-the-goalie` |
| 12 | [Pearson Correlation](pearson-correlation.html) | 2 | `019-spurious-correlation` |
| 15 | [All Models Are Wrong (and Overfitting)](all-models-are-wrong.html) | 2 | `040-three-lies-scatter-plot` |
| 21 | [Rates of Change: Level, Velocity, Acceleration](rates-of-change.html) | 2 | `097-acceleration-second-derivative` |

### uncertainty

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 10 | [Bayesian Inference](bayesian-inference.html) | 6 | `001-skenes-era` |
| 18 | [Communicating Uncertainty](communicating-uncertainty.html) | 5 | `102-cfb-contender-board` |
| 26 | [Signal vs. Noise](signal-vs-noise.html) | 3 | `128-the-bullpen-nobody-needed` |
| 11 | [P-Value](p-value.html) | 2 | `019-spurious-correlation` |
| 20 | [Information & Surprise](information-and-surprise.html) | 1 | `105-cfb-weeks-that-matter` |
| 27 | [Nomothetic vs. Idiographic](nomothetic-vs-idiographic.html) | 0 | **none yet** |

### judgment

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 2 | [Confirmation Bias](confirmation-bias.html) | 1 | `055-superstition-baseball-math` |
| 19 | [Heuristics: Biases vs. Ecological Rationality](heuristics-and-ecological-rationality.html) | 0 | **none yet** |

### epistemics

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 13 | [Necessary vs. Sufficient](necessary-vs-sufficient.html) | 2 | `086-nd-dynasty-test` |
| 16 | [Do We Believe the Data, the Model, or the Theory?](believe-data-model-theory.html) | 0 | **none yet** |

### design

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 22 | [The Unit of Analysis](unit-of-analysis.html) | 5 | `108-nfl-own-mean` |
| 17 | [Why Research Design Matters](research-design.html) | 1 | `135-home-field-ranks` |

### decision

| No. | Concept | Issues | Start with |
|---|---|---|---|
| 24 | [The Objective Function: What Are You Actually Maximizing?](objective-function.html) | 3 | `113-pull-the-goalie` |

---

## The reusable example Sean asked for

He wanted one teaching example carried across several stories rather than a new one every time. Two
candidates already earned it without anyone planning it:

- **Base rate — 14 issues.** Start at `020-jets-first-round-busts`.
- **Regression to the mean — 13 issues.** Start at `053-raleigh-slump-shower-oblique`.

Those two are the spine. If a reader understands only two ideas from this newsletter, these are the
two, and there is already a fortnight of reading behind each. The recommendation is to name one of
them as the running example and refer back to it by number the way Sean described: *"go take a look
at episode 168, this is a classic example of confirmational bias."*

---

## The quiz

Sean's spec, close to verbatim, so it does not drift:

> "Maybe in the future, Pat, we do what The Neuron does, and we have a quiz at the end. A simple
> one, one or two questions. Or if you want to do three, you could, but don't make them hard. Make
> them geared towards what we're learning."

Which means:

- **One or two questions. Three is the ceiling, not the target.**
- **Easy on purpose.** The quiz checks that the point landed. It is not an exam and it is not a
  chance to be clever.
- **Tied to the concept box in that issue**, not to the sport. A reader who skimmed the box should
  get it right.
- One line of feedback per answer, explaining why, because the explanation is the teaching.

`commercial-gain-quiz.html` already has a working quiz engine — scorebar, option buttons, per-answer
feedback. It is built as a standalone page. Lifting the mechanics into a small end-of-issue block is
the job, and it is mostly extraction rather than new code.

---

## The concept box

Sean asked for a second coloured box beside the existing provenance box:

> "The boxes that you have, you know, have a different coloured box in there, the way you already do
> where you're talking about where the data came from. But maybe now we have one on statistical
> concept."

> "Keep it simple. Don't make it three pages long. It's like one or two paragraphs."

So: one or two paragraphs, its own colour, naming the concept, linking to the primer, and linking to
one earlier issue that shows the same idea. That last link is what turns 177 separate issues into a
course.

---

## Proposed Concept No. 28 — when the rules change, the numbers mean something else

Sean brought a story to the call that does not fit any of the 27:

> "The number of position players being utilized in MLB now... they're throwing in the low 40s.
> The stats can change, but they change when the rules change. All of a sudden it creates a new
> environment."

The three-batter minimum removed the one-batter specialist, so bullpen usage changed, so position
players pitch more. Any trend line drawn across that rule change is comparing two different games.

That is not survivorship bias and it is not a denominator problem. It is its own trap, and it is
everywhere in sport because the rules move constantly. Sean thinks the source is a Wall Street
Journal piece and is looking for it.

His second example fits the existing **survivorship bias** primer rather than needing a new one:

> "There is no normal curve. You're looking at high-end pitchers and you don't get a normal curve.
> There's a selection bias, because no one wants a guy throwing 62 miles an hour."

A truncated distribution that people keep treating as a full one. Survivorship bias has five issues
behind it already, so that story has somewhere to live today.

---

*Coverage figures generated from `published/*.html` on 17 September 2026. Anything that says "none
yet" is a commission, not an oversight.*
