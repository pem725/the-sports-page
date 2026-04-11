# The Sports Page

*A daily sports statistics newsletter that takes one strange number and explains what it actually means.*

**Live:** https://pem725.github.io/the-sports-page/

---

## What this is, in one paragraph

Every day, a strange number appears in sports. A pitcher gives up five earned runs in two-thirds of an inning and posts a 67.5 ERA. A hitter starts the season 6-for-9 and the papers call him MVP. A seven-win team fires its coach after one season. Most people see these numbers and feel something. The Sports Page takes the same numbers and asks what they actually mean — the history, the math, the forecast, and the honest assessment of what happens next. It's a newsletter for friends and family, built for people who don't need statistics lectures but do want to be told the truth about what the numbers are and are not saying.

The goal is **500 issues over roughly two years**. We're keeping score. See the archive at the live site for where we stand.

---

## The house philosophy

The Sports Page is built on one stubborn idea: **there are three things you can do with data, and you should always know which one you're doing.**

1. **Describe** what happened. (Easy. The data already knows the answer.)
2. **Predict** what will happen. (Harder. The future is a real test.)
3. **Control** *why* it happens. (Hardest. Requires mechanism, not just fit.)

Most sports writing stops at #1 and pretends it's doing #2. Most advanced analytics stops at #2 and pretends it's doing #3. We aim for #3 when we can, settle for #2 with honesty about which is which, and label #1 as #1. The mantra, borrowed from every working scientist who has ever been wrong in public: *the past is cheating — any flexible enough model fits it perfectly. The real test is predicting the future, and the real discipline is admitting when your prediction was wrong.*

Which brings us to **the accountability pledge**:

> Every prediction this newsletter makes is explicit, dated, and publicly graded. Every Sunday, the prior week's predictions get a report card. When we are wrong — and we will be — we say so, we analyze why, and we update the model. The goal is not to be right. The goal is to improve the model next time.

If you've ever read a hot take and thought *I'll never know if this person was right*, The Sports Page is the opposite of that.

---

## Meet the writers

The newsletter has six voices. They are not the same person with different hats — each one is suited to a specific kind of story, and the right voice is part of the craft.

| Voice | What it sounds like | When it shows up |
|---|---|---|
| **The Columnist** | Dry wit, editorial authority, measured confidence. The default. | Most daily issues, analytical pieces, series installments |
| **The Heckler** | Bar-stool sarcasm, trash talk, no patience for front-office excuses | Bad drafts, misread contracts, coaches who deserved it |
| **The Professor** | Patient, warm, teaches the math gently without condescending | Sunday recaps, methodology pieces, anything that needs a framework |
| **The Eulogist** | Respectful, melancholic, beautiful prose about loss | Career-ending injuries, end-of-era pieces, franchise collapses |
| **The Fan** | Raw, first-person, unapologetically emotional | Playoff heartbreak, loyalty pieces, droughts that have gone on too long |
| **Sal** *(guest columnist)* | Perfectly worded sarcasm, long winding sentences, accumulated wisdom | Once every 2–3 weeks, on a question that has been simmering for a while |

Sal is a rare appearance. He only writes when (a) a question has been rattling around the newsletter for 2+ weeks, (b) enough data has piled up to make a real argument, and (c) the editor explicitly invokes him. He is a scalpel, not a hammer.

---

## How the machine works

```
queue/     ->   An issue is ready, waiting for its publish date
reserve/   ->   An evergreen issue, waiting for a slow news day
published/ ->   Live on the site, linked from index.html
index.html ->   The homepage, which is also the archive
publish.sh ->   The one-command script that moves things to live
```

Each morning, one of three things happens:
- **A scheduled agent** (runs at 4:30am ET) reads the queue, picks the most time-sensitive piece, runs the 7-step publish workflow, and pushes to GitHub Pages
- **A timely piece** gets written from scratch in response to a fresh event and published the same day
- **An evergreen reserve piece** fills a genuine dry spell

Sundays are different. The **Sunday Edition** is built fresh every Sunday morning — never from a stale template. It recaps the week, grades every prediction the newsletter made, and sets up what's coming. If a Sunday skeleton exists in the queue, it is treated as a template only; all statistics, model outputs, and predictions get rerun with fresh data the morning of publication.

---

## Want to help? Pick a lane.

There are two ways in. Pick whichever one sounds like fun. You can also do both, and the people who do both tend to be the most dangerous contributors.

### Lane 1 — Content curation (no coding required)

If you love sports and notice the weird stuff, this is your lane. The newsletter runs on strange numbers, and the best strange numbers come from people who watch carefully and get annoyed by misleading coverage.

**Concrete ways to help:**

- **Send a stat.** Spot something strange and send it — ideally with a sentence about why it looks strange. The denominator is usually the tell. "Through 3 ABs, he's hitting .667" is a candidate. "Through 600 ABs, he's hitting .320" is not (that's just a good year). The smaller the denominator, the better the piece.
- **Flag a prediction to grade.** If you remember that the newsletter said something and you want to know if we were right, say so. The answer becomes a Sunday Edition item.
- **Suggest a voice.** Read something in the queue and tell the editor which of the six voices you think fits. "This piece is dry, but it's really a Heckler piece" is a useful note. Queue files live in `queue/` as readable HTML.
- **Catch errors.** Typos, wrong dates, a player on the wrong team, math that doesn't add up. The best catches come from readers, not writers.
- **Suggest a series.** If you see a question that keeps surfacing, propose a series. Recent examples: the executive-order college sports series, the Jimmys & Joes loophole-history franchise, the coaching stabilization piece.
- **Argue back.** If a prediction seems wrong, say why. Disagreement is a first draft of a future piece.

Submissions can go via GitHub issue (if you have an account), email, text message, or hand-delivered on a napkin. The napkin method has worked before.

### Lane 2 — The innards crew (some coding required)

If you like building infrastructure, there is plenty of it and the barriers are low. Most of the code is shell scripts, HTML, and small Python programs. Nothing is exotic.

**Concrete places to start:**

- **`publish.sh`** — the one-command publisher. Read it. If it could do one more useful thing at publish time (link check, image optimization, RSS update), it could grow. PRs welcome.
- **`index.html`** — the homepage is hand-maintained. Each new issue adds a `<div class="issue">` block at the top. A script that takes a new issue file and automatically updates `index.html` would save real time. Bonus points if it handles the tag classes (`.mlb`, `.nfl`, `.nhl`, `.cfb`) correctly.
- **Cross-reference checker** — issues sometimes reference other issues ("as we noted in Issue #7"). The SKILL.md includes a grep-based check, but a proper tool that parses the queue, finds every `Issue #N` reference, and verifies the target is actually published would prevent broken chains.
- **Data pipelines (the big one)** — the Jimmys & Joes Index tracker (see `planning/jimmys-and-joes-series.md`) needs real data feeds by July 2026 for 247 composite recruiting rankings, SP+/SRS/FPI team ratings, Google Trends volume, social sentiment, attendance, and Heisman odds. This is a real build. If you like wiring APIs together, this is where the biggest marginal impact lives.
- **Recovery model generalization** — the Bayesian recovery model currently handles Gamma-Poisson (pitching ERA) and Beta-Binomial (batting average, field goal percentage, save percentage). Extending it to a new rate stat is usually 20 lines of Python and a new example in the queue.
- **Broadsheet component library** — the newsletter's aesthetic is "aged newsprint editorial broadsheet," built with Playfair Display, Libre Baskerville, and Roboto Mono. If you have design skills, the component library (stat cards, pull quotes, explainer boxes, recovery charts) could always use more polish.
- **Archive search** — the homepage is an archive, but it doesn't have search. A small client-side search over published issue titles and tags would make the back catalog actually usable.

If you're not sure what to work on, start by reading an issue in `published/` and looking at how it's built. The HTML is intentionally hand-written and readable — it's supposed to feel like a broadsheet, not a framework.

---

## What's happening right now

The newsletter is in active daily production. A few things currently under way, roughly in order of ambition:

- **The April 2026 executive order series** — a 5-part editorial on the EO regulating college sports (transfer portal, NIL, federal funding). Currently running.
- **The Jimmys and Joes franchise** — a 3-part series on the statistical history of college football's talent-access loopholes, plus a 7-piece Index tracker that will follow four named programs (Notre Dame, Ole Miss, Oregon, Indiana) across the entire 2026–27 season on a seven-dimension scorecard. Kicks off in late June with summer-bridge content; runs through June 2027 with a year-one retrospective. Full planning doc at `planning/jimmys-and-joes-series.md`.
- **The Past Is Cheating** — a standalone "manifesto" piece laying out the describe/predict/control framework and the accountability pledge. Runs as the philosophical groundwork for everything that comes after. Planning doc at `planning/stats-desk-manifesto.md`.
- **Sunday Editions** — built fresh every Sunday, with the prediction accuracy report card.

The back catalog lives in `published/` and the live archive is on the site.

---

## File map

```
.
├── README.md                         <- you are here
├── SKILL.md                          <- the full "how to build an issue" spec
├── CLAUDE.md                         <- editorial rules and workflow for the agent
├── publish.sh                        <- one-command publish script
├── setup-machine.sh                  <- bootstrap a new machine to contribute
├── index.html                        <- homepage + archive
├── published/                        <- live issues (linked from index.html)
├── queue/                            <- ready to publish, dated
├── reserve/                          <- evergreen, no specific date
├── planning/                         <- long-form planning docs for big series
│   ├── jimmys-and-joes-series.md
│   └── stats-desk-manifesto.md
└── assets/                           <- logos, banner, favicon, QR code
```

The two most useful files to read first if you want to understand how the newsletter is built are **SKILL.md** (the full spec for turning a stat into an issue, including the Bayesian recovery model and the broadsheet design system) and **planning/jimmys-and-joes-series.md** (a worked example of what series-level planning looks like in this project).

---

## Editorial rules (the short version)

A few stubborn rules that keep the newsletter from drifting:

- **One statistical question per issue.** No multi-topic pieces.
- **No holiday specials.** Sports only.
- **No basketball.** Not because basketball is bad — because the editorial attention has to live somewhere, and it lives in football, baseball, and hockey.
- **Milestone issues** at #50, #100, #200, etc. — the newsletter looks at itself in the mirror at round numbers.
- **Published predictions stay published**, even the wrong ones. Especially the wrong ones.
- **Team allegiance is implied, never named.** The newsletter covers teams naturally; it never announces who in the household roots for which.
- **Timely beats analytical beats evergreen** — but only when the timely piece is actually timely. A stale "timely" piece is worse than a well-placed evergreen.

The full set of rules (plus the tone-selection matrix and the Sunday Edition checklist) lives in SKILL.md.

---

## The goal, stated plainly

500 issues. Roughly two years. Each one teaches a real piece of statistics through a real story about sports — the kind of story that makes the math feel inevitable rather than homework. When we get to 500, the back catalog should function as an accidental textbook: someone who reads the whole archive should come away knowing what denominators do, why stabilization thresholds matter, how Bayesian updating works, why regression to the mean is the most important idea in sports, and why "the past is cheating" until you test it on the future.

If you want to help get there — whether you're sending stat ideas on a napkin or wiring up a recruiting data pipeline — there's a place for you. The newsletter is better the more people touch it.

See you on the page.
