# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**The Sports Page** — a daily sports statistics newsletter at https://thesportspage.net/. Each issue takes one strange, extreme, or counterintuitive stat and explains what it actually means. Goal: 346 issues remaining of 500

## Repository Structure

```
index.html              <- Homepage with issue archive (GitHub Pages serves this)
publish.sh              <- One-command publish script
setup-machine.sh        <- Cross-platform setup for new machines
assets/                 <- Logo, banner, favicon, QR code
published/              <- LIVE issues (linked from index.html)
  001-skenes-era.html
  002-alonso-orioles.html
  ...
queue/                  <- Ready to publish (not linked from index.html)
  008-mentor-myth.html
  009-eo-transfer-freeze.html
  ...
reserve/                <- Evergreen content, no specific date
  cfb-coaching-stabilization.html
```

## Publishing Workflow (CRITICAL — follow exactly)

### Step 0 — SYNC WITH GITHUB FIRST (always, before anything else)

**STOP. Before reading anything in this repo, before counting issues, before drafting, before checking the day of week: sync the local clone with GitHub.**

```bash
cd /home/pem725/GitTemp/the-sports-page  # or wherever the repo lives on this machine
git fetch origin main
git status -sb                            # confirm not ahead/behind in unexpected ways
git pull origin main --ff-only            # fast-forward only — never silent merge
```

This is non-negotiable and applies to **every** invocation of this skill on **every** machine — drafting, publishing, queueing, Sunday Editions, even just "let me check what's in the queue." The repo is shared across machines and the GitHub Actions autopublish bot pushes commits Monday–Saturday at 4:30am ET. Your local clone is *probably* stale, even if you worked here yesterday.

**Why this rule exists**: On 2026-05-10, a Sunday Edition was drafted from a stale local clone that was missing four autopublish commits (Issues #39–42). The recap claimed a "four-day publishing pipeline silence" that had not occurred. The bad Sunday Edition was caught only because `git push` was rejected with a non-fast-forward error. The right fix is upstream: never start work from a stale clone.

**If `git pull --ff-only` fails** (because you have uncommitted local work, or local commits that diverge): stop and reconcile *before* doing anything else. Do not force-pull, do not stash blindly. Inspect with `git log HEAD..origin/main` and `git status` first, then decide.

**If you are not in the repo directory**: find it. The skill directory and the repo are the same physical location on the machine that owns the repo (typically via a symlink). On a fresh machine, see `setup-machine.sh`.

### Step 1 — CHECK THE DAY OF WEEK (after the GitHub sync)

**Before touching the queue, before picking any file, before making any decisions: check what day it is today.**

- **If today is SUNDAY**: Jump immediately to the **Sunday Edition Workflow** below. Do NOT pick from `queue/`. Do NOT publish any regular article today. Sundays are permanently reserved for the Sunday Edition. This is not negotiable. If the Sunday Edition cannot be built for any reason (template missing, data fetch failed), stop and alert the human — do NOT publish a non-Sunday piece on a Sunday as a fallback.

- **If today is MONDAY–SATURDAY**: proceed to the Regular Publishing Workflow below.

### Regular Publishing Workflow (Monday–Saturday only)

1. **Read the publish order** from `QUEUE_ORDER.txt` in the repo root. This file lists queue filenames, one per line, in the order they should be published. Take the FIRST line that matches a file still in `queue/`. If QUEUE_ORDER.txt is empty or missing, fall back to picking the most timely non-CFB/non-repeat piece from `queue/`. **Skip any file whose name starts with `sunday-`**.

2. **Derive current state from git** (do NOT rely on the "Current State" section at the bottom of this file — it may be stale):
   ```bash
   # Count published issues (the reader-facing number for the next issue)
   grep -c 'class="issue-num"' index.html
   # See what published most recently (for the variety rule)
   git log --oneline -1
   ```
   The next reader issue number = the count from grep + 1.

3. **Variety check**: Compare today's piece against what `git log --oneline -1` shows. If it's the same topic/sport as yesterday, skip it and take the NEXT line from QUEUE_ORDER.txt instead. Never publish back-to-back same topic.

4. **Update the issue number inside the HTML file**: Search for "Issue No." and replace with the correct reader number. There are usually 2 occurrences (datebar and footer). Also update the `<title>` tag.

5. **Update the date**: Replace any placeholder or old date with today's date.

7. **Cross-reference check**: Grep the file for "Issue #", "Issue No.", and "See Issue" — verify every reference points to an ALREADY PUBLISHED issue. If referencing an unpublished piece, change to "coming soon."

7. **Add the entry to index.html**: Insert a new `<div class="issue">` block at the TOP of `<div class="issues">`, BEFORE all existing issues. Follow the exact HTML pattern of existing entries. Include: issue-num, issue-date, issue-hed (with link to `published/FILENAME`), issue-deck, and issue-tags.

9. **Move the file**: `git mv queue/FILENAME.html published/FILENAME.html`

9. **Remove the published file from QUEUE_ORDER.txt**: Delete the line you just published so the next run picks the next file. This keeps the queue order accurate.

10. **Update the Current State section** at the bottom of this file. Update ALL fields atomically — do not update the count without also updating "Last published." The fields are:
    - Published count
    - Queue contents (list remaining files)
    - Goal (500 minus published count)
    - Last published (issue number, title, filename, today's date)

11. **Commit and push**:
    ```
    git add index.html published/FILENAME.html QUEUE_ORDER.txt CLAUDE.md
    git commit -m "Publish Issue #N: brief description"
    git push origin main
    ```

12. **If ANY step fails**: Do NOT silently exit. Create a GitHub issue on this repo with the label `publish-failure` describing what went wrong, what step failed, and the error message. Use: `gh issue create --title "Publish failure: [date]" --label "publish-failure" --body "[error details]"`. Then exit. Never publish a broken or incomplete issue.

### Autopublish (GitHub Actions — Mon-Sat)

**Known problem: GitHub's cron is unreliable, and it is not our bug.** From
2026-08-27 the scheduled runs began firing **11–12½ hours late**, with one slot
dropped entirely on 08-28. Issues #152 and #153 went out at ~1:52pm and ~2:57pm
ET instead of before dawn.

Ruled out, with evidence, so nobody re-diagnoses this:
- **Not our config** — the workflow file had not changed since 2026-08-08.
- **Not Actions volume** — 08-21 had 69 workflow runs and 22 commits and
  published 54 minutes late; 08-28 had 5 runs and 1 commit and published 12h26m
  late. The relationship runs backwards.
- **Not the script** — every run that fired succeeded, and the double-publish
  guard held when four delayed runs landed together.

It matches [community discussion #201738](https://github.com/orgs/community/discussions/201738)
("delayed 8-14 hours, one day dropped entirely") and follows two GitHub Actions
incidents declared on 2026-08-26.

**Mitigations applied 2026-08-28:** crons moved off the congested `:00`/`:30`
minutes to odd ones, a fifth slot added, and a *Report scheduling lateness* step
added that prints the firing slot against the wall clock and raises a workflow
warning past two hours. Editing the workflow file also re-registers the schedule,
which is GitHub's own advice for a stuck one.

**If it persists, cron is not fixable from inside the repo.** The reliable
answer is an external nudge — `gh workflow run autopublish.yml -R pem725/the-sports-page`
from a machine that is actually awake — because a `workflow_dispatch` fires
immediately while a `schedule` does not.

**Reader-facing impact:** Buttondown polls the RSS feed, so a late publish is a
late *email*. That is the part subscribers notice.



A GitHub Actions workflow (`.github/workflows/autopublish.yml`) runs at 4:30am ET Monday–Saturday. It calls `scripts/autopublish.py` which handles the full Regular Publishing Workflow deterministically. **Sunday Editions remain manual** — they require live data, prediction scoring, and editorial prose that a script cannot provide.

**Every issue carries a "What to Watch" block.** `scripts/daily_watch.py` runs
*before* the publish and writes `data/daily-watch.html`; `autopublish.py` swaps it
in for the `<!-- WATCH_BLOCK -->` marker that every queue file now carries.

**There is a quality bar, and enforcing it is the point.** A league whose best
game is below it is dropped and named in one quiet line instead: baseball under
**4 points** of swing, college past **80/20**. A section that prints something
every day regardless of whether it matters teaches the reader to skip it, which
costs more than an empty day. When nothing clears the bar the block says so —
that is real information.

**The block ranks games by measured importance, not by vibe.** For each game on
the card it reports *championship leverage*: how much playoff probability changes
hands depending on who wins. One simulation of the remaining season is run, then
each game's outcome splits those seasons in two and the gap is the swing.
Conditioning inside a single run is exact — games are independent given team
strength — and about 30x cheaper than re-simulating each game twice. Verified
2026-08-29: conditional gave +7.0/-7.9 for Mariners-Blue Jays, brute force gave
+7.1/-7.6.

The result is reliably counterintuitive, which is the point: **the biggest game is
rarely the one with the best teams.** It is the one where both clubs sit nearest a
coin flip, because that is where a single win moves the most probability.

**Fail-safe by design.** Generation is `continue-on-error`, and if the block is
missing the publisher deletes the marker and ships the issue without it. A
leverage table is never worth blocking an issue. Injection keys on an explicit
marker rather than inferring a position from the markup — a regex aimed at a
`<div>` destroyed two figures in this repo once already.

New queue files must include `<!-- WATCH_BLOCK -->` immediately before
`<div class="footer">`, plus the `.watch` styles in the `<style>` block. The
template has both. Preview any day's block with
`python3 scripts/daily_watch.py --print`.

**The Odds Board refreshes on the same run.** `scripts/refresh_odds.py` runs
after the publish step, recomputes every club's playoff and division odds from
the live standings, and rebuilds `odds.html` via `scripts/build_odds_page.py`.
It piggybacks on this workflow on purpose: a second schedule would inherit the
same GitHub cron delays *and* race this job for the push. It is
`continue-on-error` and runs last, so a failed refresh can never stop an issue
going out — the previous board simply stays up.

Two things about it worth knowing:

- **The stored trajectory is a WEEKLY grid, and must stay one.** The page's
  smoother uses a bandwidth counted in points, not days, so mixing weekly
  points with daily ones would silently change how much time it averages over.
  The script therefore recomputes today's numbers every day but only *appends*
  a point once seven days have passed; otherwise it overwrites the most recent
  point in place. Current numbers are always live; the curve stays evenly spaced.
- **It refuses rather than guesses.** If any club's games played plus games
  remaining does not equal 162, or a club in the file is missing from the API,
  it exits without touching the data.

It runs Monday–Saturday with the publish, so the board does not refresh on
Sundays. Manual refresh: `python3 scripts/refresh_odds.py` (add `--dry-run` to
compute and report without writing).

**PUBLISH-META requirement**: Every queue file MUST include a metadata comment block at the very top (before `<!DOCTYPE html>`). The autopublish script uses this for variety checking and index.html tag generation. Format:

```html
<!-- PUBLISH-META
topic: MLB
tags: MLB:mlb, Mets, Small Sample
-->
```

- `topic`: The primary topic/sport (used for the variety rule — no back-to-back same topic)
- `tags`: Comma-separated, for the index.html entry. Use `Text:cssclass` to apply a color class (mlb, nfl, cfb, nhl), or plain `Text` for default styling.

**When creating new queue files**, always include PUBLISH-META. Claude should add this automatically when generating new issues.

To manually trigger: go to GitHub → Actions tab → "Autopublish Daily Issue" → "Run workflow."

To dry-run locally: `python3 scripts/autopublish.py --dry-run`

### Sunday Edition Workflow (Sundays ONLY — runs every Sunday at 4:30am ET)

This workflow runs instead of the Regular Workflow every Sunday. It uses a copy-from-template pattern so the template itself is never modified or consumed.

**The canonical template lives at `reserve/sunday-recap-template.html` and must NEVER be modified in place.** Copy it, edit the copy, publish the copy, leave the original alone.

1. **Compute the Sunday Edition number NNN**: Count existing `published/sunday-*.html` files and add 1. First Sunday = 001, second = 002, etc. Pad with leading zeros.

2. **Copy the template to a working file**:
   ```
   cp reserve/sunday-recap-template.html queue/sunday-NNN.html
   ```
   Do NOT use `git mv` — the template must stay in reserve/.

3. **Pull fresh data with web_search** (REQUIRED before writing anything):
   - Current MLB standings and team records
   - Current NHL standings and playoff picture
   - Injury updates (especially players the newsletter has been tracking)
   - Game results from Saturday and any completed Sunday-morning games
   - Player stats for any player we've written about in the past 7 days
   - Any relevant NFL, CFB, or other sport news from the past week
   - **Never use stale data.** Every number in the final piece must come from Sunday morning's fetch.

4. **Rerun every prediction model from the past week's issues** with the fresh data. For each prediction:
   - Pull the actual current outcome
   - Rerun the relevant Bayesian model (Gamma-Poisson for ERA, Beta-Binomial for BA/FG%/win-rate) with updated data
   - Score the prediction: **HIT** (model matched outcome within a reasonable margin), **MISS** (materially wrong, explain why), **PARTIALLY HIT** (direction right, magnitude off), or **PENDING** (not enough data to judge yet)
   - Be honest about misses. Do not hide them. Misses are the point of the Sunday Edition.

5. **Fill the READER'S CONTRACT block first.** The template carries four
   slotted lines above "The Week in Review" — `{{N_ISSUES}}`, `{{N_GRADED}}`,
   `{{N_HIT}}`, `{{N_MISS}}`, `{{N_PENDING}}`, `{{N_NOFORECAST}}` and
   `{{THE_MISS}}`. They must be filled with the week's real numbers and must stay
   **above the first section**: the checker reads the first 130 words, and the
   week-in-review list alone eats that budget.

   `{{THE_MISS}}` is the important one. Name the week's most interesting wrong
   call plainly and say what it cost. **If the misses were dull, say so** — do not
   manufacture drama. A Sunday Edition that cannot find anything it got wrong is
   usually a Sunday Edition that did not look.

   Then run both checks before publishing:
   ```
   python3 scripts/check_readability.py queue/sunday-NNN.html
   python3 scripts/check_voice.py queue/sunday-NNN.html
   ```

   **The template passes the frame check but is deliberately THIN on voice** —
   its example prose is scaffolding, not writing. A filled template scores
   `thin: you, imperative`, and that is a reminder, not a bug: the recap sections
   are yours to write, in the second person, with the imperatives. If the finished
   edition still reads thin, the sections were filled in rather than written.

6. **Replace every example value in the working file** (`queue/sunday-NNN.html`):
   - Title and masthead: set correct Sunday Edition number, date, and reader-facing issue number (count published non-sunday issues + count of published sunday issues + 1)
   - Stat cards: current issue count, predictions-hit ratio, issues remaining to 500
   - Issue list: the 5–7 issues published in the past 7 days, with correct links
   - Prediction scorecard table: one row per prediction rerun, with fresh outcomes and grades
   - "What we got right" / "What we got wrong" sections: write fresh based on this week's actual outcomes
   - Over-reactions / under-reactions: fresh honest self-assessment
   - Road ahead: preview next week's planned content from the queue
   - Footer: update Sunday Edition number and "predictions tracked from" range

6. **Cross-reference check**: Grep the working file for "Issue #", "Issue No.", and "See Issue" — verify every reference points to an ALREADY PUBLISHED issue.

8. **Inject the readership block** (auto-populated from GoatCounter):
   ```
   python3 scripts/fetch_readership.py --inject queue/sunday-NNN.html
   ```
   This replaces the `<!-- READERSHIP_BLOCK -->` marker in the template with the top-5 most-read issues of the prior week. Requires `$GOATCOUNTER_TOKEN` in the environment (set in `~/.zshrc`). If the API is unreachable or returns no data, the script writes a graceful "data pending" message and still exits 0 — do not skip this step.

8. **Move the file**:
   ```
   git mv queue/sunday-NNN.html published/sunday-NNN.html
   ```

10. **Add entry to `index.html`**: Insert a new `<div class="issue">` block at the top, with the correct reader-facing issue number, link, headline, and tags (use `.tag` for "Sunday Edition").

11. **Commit and push**:
    ```
    git add index.html published/sunday-NNN.html
    git commit -m "Publish Sunday Edition No. NNN: week N recap"
    git push
    ```

**CRITICAL rules for the Sunday Edition:**
- The template at `reserve/sunday-recap-template.html` is READ-ONLY. If you find yourself editing it, STOP — you should be editing the copy in `queue/`, not the template itself.
- Sunday editions are LONGER than regular issues (~1000 words vs ~500). They earn the extra length.
- Never publish stale numbers. If the data fetch fails, stop and alert — do not fall back to the template's example values.
- The whole point of the Sunday Edition is public accountability. Misses are not embarrassing; hiding misses is.

### A Reader Asks (the question pipeline)

Reader questions are the highest-value input the newsletter has, because a real
question is *evidence of a gap*. Two of the last fifteen issues came from
readers; the goal is to raise that ratio.

The front door is `ask.html`, linked from a block on `index.html` directly under
the subscribe box. Two channels: **`ideas@thesportspage.net`** and a GitHub issue
with the `reader-question` label.

**Use the domain address, never a personal one.** On 2026-08-24 all 23 public
`mailto:` links were moved off `pem725@gmail.com` and onto
`ideas@thesportspage.net`, matching the `license@thesportspage.net` already in
use. `feed.xml` embeds full article bodies, so it carries these links too and
must be regenerated after any such sweep — verify GUIDs, pubDates and item
titles are unchanged before pushing, or Buttondown will treat items as new and
re-send them to the list.

**When a question arrives:**

1. **Log it** in `tracking/reader-questions.md` — date, first name, the question
   compressed to one line, status `new`. **Never record an email address, phone
   number, or any other contact detail** in the repo. First name and team
   allegiance is the ceiling. The message itself stays in the inbox.

2. **Vet it against the archive before writing anything.** Grep `published/` and
   `concepts/`. Most questions are already answered, and replying with a link the
   same day is a *good* outcome — mark it `answered-by-link`. Do not manufacture
   a new issue for a question the corpus already covers.

3. **Apply the three-part test** (also stated publicly on `ask.html`): is there a
   number in it or could there be; could it not be settled at the table; could a
   reasonable person be wrong about it. All three → it earns a piece.

4. **Decide the tier.** A question about a *fact* becomes an issue. A question
   about a *concept* — Gene's was — earns a concept primer as well, because the
   gap it exposes is in the curriculum, not the archive. Check
   `concepts/registry.json` for whether the concept already exists.

5. **Name the reader** in the byline or the deck, first name only, unless they
   asked not to be. Follow the existing pattern: "answering Gene", "answers Tim".
   This is a deliberate exception to the no-name-dropping rule, which is about
   family team allegiances, not readers who wrote in.

6. **Answer honestly when the data cannot.** `ask.html` promises this in public.
   A piece that says "we looked and the data will not support an answer" is a
   legitimate outcome and often a better one.

**Never** use a reader question as cover for a piece you wanted to write anyway.
The vetting step in (2) exists to stop exactly that.

### NEWSINESS — the metric that picks the story

`scripts/newsiness.py`, rubric in `SKILL.md` Step 0.5, candidates in
`data/story-candidates.json`.

```
NEWSINESS = (GRIP / 10) x (0.35 TWIST + 0.25 CLOCK + 0.15 STACK + 0.25 CARRY)
```

**GRIP multiplies rather than adds, and that is the whole editorial position.**
This paper is stats driven by sports, not sports driven by stats. A Super Bowl
with a dull number scores near nothing; a Tuesday game between two eliminated
clubs with a shocking number can lead. Audience (STACK) carries the smallest
weight on purpose.

Three things to keep doing with it:

- **Score before writing.** It costs two minutes and it has already caught the
  difference between a story we wanted to be true and one the data supports.
- **Log the rejects too.** What we passed over, and why, is a future issue and
  eventually a published ranking — readers should be able to see the selection,
  not just the selected.
- **Let the panel overrule it.** Tim, Sean and Patrick jr score independently
  with `--panel`. A metric nobody can argue with is a metric nobody is using; the
  disagreements are where the rubric gets tuned.

### One slot a day — so newsworthiness and decay decide the order

There is exactly one issue per day. Every piece therefore competes with every
other piece, and two things settle the order. Neither should live in anyone's
head.

**1. How fast it rots.** Every queue file declares `decay:` in its PUBLISH-META,
directly under `topic:`:

| decay | meaning | must publish within |
|---|---|---|
| `hot` | numbers move daily | ~3 days, or rewrite it |
| `dated` | tied to a fixed event | before that event |
| `slow` | season-bound, stable for weeks | ~3 weeks |
| `keeps` | methods or history | any time |

**2. Whether the rotation holds.** No two consecutive issues share a topic.

Check both with **`python3 scripts/queue_health.py`**, which walks the real
calendar and flags a clash, a piece that will be stale by its slot, or a thin
buffer. Run it after any reorder — reordering by list index has already produced
three back-to-back clashes in one go, because eyeballing a list is not the same
as walking the dates.

**The buffer is not padding, it is capacity.** Keep **at least two** `keeps`
pieces in the queue at all times. They are what lets a breaking story jump the
line without leaving a hole behind it. A queue of nothing but hot pieces cannot
absorb news; a queue of nothing but evergreen ones is never about anything.

**When news breaks, it wins.** A timely, stats-backed piece displaces a `keeps`
piece, never the reverse. The displaced piece goes to the back, not the bin.

**But the standard does not move.** Newsworthy is necessary, not sufficient —
every issue is still built on a number we computed and can defend, still passes
`check_readability.py` and `check_voice.py`, and still states its limits. A piece
that is timely and thin costs more than an empty day, because it is the day's
only slot.

### Content Tiers:
- **Timely**: Breaking news, injuries, game results. Publish immediately. Goes stale fast.
- **Analytical**: Trade analyses, historical comparisons, series pieces. Publish to fill gaps.
- **Evergreen**: Off-season analyses, methodology explainers. Publish anytime.

## Secrets — non-negotiable

**Never expand a secret in a shell command. Ever.** Not to check it, not to
confirm it exists, not "just this once."

This rule exists because the same mistake leaked a live token into a chat
transcript **twice in one week**, both times from a check that looked safe:

```bash
echo "TOKEN: ${TOKEN:+SET}${TOKEN:-unset}"     # LEAKS THE VALUE
```

`${VAR:-default}` substitutes the **value** when the variable is set. The
`${VAR:+SET}` half is harmless; the `:-` half prints the secret, and the pair
reads as a safe presence check. Being careful is not the fix — careful failed
twice.

**Where secrets live:** `~/.config/secrets/tokens.env`, mode 600, in a 700
directory, sourced from `~/.zshrc`. Not in `~/.zshrc` itself, not in the repo,
not in any file git can see. Reference them by name only: `$CFBD_KEY`.

**Setting one requires a real terminal.** `set_secret.py` now refuses to run
without a TTY. This is not fussiness: `getpass` silently falls back to a mode
that ECHOES the input (`Warning: Password input may be echoed`), so running it
through an agent, a pipe, or Claude Code's `!` prefix would print the live
secret into the transcript. Discovered 2026-08-24 attempting to store the
Porkbun keys; nothing leaked only because stdin happened to be empty.

```bash
# in a real terminal window:
python3 scripts/set_secret.py PORKBUN_API_KEY

# or, if the value is already in a file (file is shredded afterwards):
python3 scripts/set_secret.py PORKBUN_API_KEY --from-file /path/to/keyfile
```

**To check one, use the tool, which has no code path that can print a value:**
```bash
python3 scripts/check_env.py                # all of them
python3 scripts/check_env.py CFBD_KEY       # one
```
It reports SET/unset, length, and a salted SHA-256 fingerprint. The fingerprint
is stable, so it confirms a rotation actually changed the token while revealing
nothing about it.

**Banned outright:**
```bash
echo $TOKEN            env | grep TOKEN         printenv TOKEN
echo "${TOKEN:-x}"     set | grep TOKEN         curl -v -H "Authorization: $TOKEN"
```
Passing a secret to `curl -H` is fine. Adding `-v` or `--trace` to that same
command is not — it echoes the header.

**Porkbun** (the registrar) issues a *pair*: `PORKBUN_API_KEY` and
`PORKBUN_SECRET_KEY`. Both are stored the same way as everything else and are
used together. Talk to it via `scripts/porkbun.py`, which passes them as
`X-API-Key` / `X-Secret-API-Key` headers straight from `os.environ` and has no
code path that prints either one:
```bash
python3 scripts/porkbun.py --ping                    # do the keys work?
python3 scripts/porkbun.py --mx thesportspage.net    # is mail routable?
```
Two things worth knowing before reaching for it. **Email forwarding is not in
the v3 API** — of 68 endpoints the only `/email` one is `setPassword`, for the
paid mailbox product, and `addUrlForward` is *web* redirects. Forwarding is
dashboard-only. And **API access must be enabled per-domain** in the Porkbun
control panel, so a valid key pair can still return an error for a domain.

**For CI**, use `gh secret set NAME` and paste at the prompt, or
`gh secret set NAME < file`. Both read the value without echoing it. Never put a
token in a workflow file.

**If a secret is ever exposed, rotating it is the only remedy.** Moving it
somewhere safer afterwards does nothing for the value that already leaked.

## Editorial Rules

- **WRITE IN PATRICK'S TEACHING VOICE.** Added 2026-08-20. The house voice is not
  a generic "newsletter" voice; it is the voice of `GradStats-Book`. The full
  comparison lives in `corpus/house-style.md` and every target is measured, not
  asserted: 52,069 words of his teaching prose against 203,522 words of the
  newsletter.

  **The gap is person, not punctuation.** He writes *to* a reader; the newsletter
  wrote *about* sport.

  | | newsletter | his book |
  |---|---|---|
  | you / your | 5.91/1k | **15.67/1k** |
  | we / us / our | 3.34/1k | **8.44/1k** |
  | imperatives (Notice, Watch, Hold onto) | 0.23/1k | **1.20/1k** |
  | semicolons | 1.94/1k | **4.51/1k** |

  **Do NOT scrub em dashes.** The first pass measured a 200x "overuse" against the
  book and it was an artifact: he uses the dash aside *more* than the newsletter
  does (15.94 vs 12.25 per 1k), he simply types it as a spaced hyphen. Removing
  them deletes his voice and replaces it with nothing.

  **The classic AI tells are already at zero** across all 175 works: "it is worth
  noting", "underscores", "testament to", "pivotal", "delve", "tapestry". Keep
  them there, but do not go hunting for them. The real problem is a handful of
  moves repeated into invisibility — the antithesis *"X is not A. It is B."*
  appears in **78 of 175 pieces**, "exactly" 188 times. A tic is a frequency
  problem, not a banned word.

  **Moves to borrow from him:** name the misconception before correcting it;
  address the reader constantly; state what they will be able to do; **admit your
  own past error by name** ("including an old version of mine"); bold the term and
  italicise the pivot; ask a question and answer it immediately; use homely
  physical analogies; name stakes concretely; deadpan humour, never a joke for its
  own sake; say the hard part plainly ("That 20% should bother you").

  **Check it:** `python3 scripts/check_voice.py queue/NNN-slug.html`

- **THE READER'S CONTRACT — say what the piece is FOR.** Added 2026-08-17 after
  Issue #142 scored a Flesch-Kincaid grade of **5.0** and was still opaque. Simple
  words, invisible purpose. A sixth-grader could read every sentence and still not
  know why the piece existed.

  So four things must be findable in the first ~130 words, plainly labelled:

  1. **The question.** Written as an actual question, with a question mark.
     *"Why does an upset feel so much better than an ordinary win?"*
  2. **The answer, with its number.** *"A team that wins 29 of 100 over a season
     wins 48 of 100 in one sudden-death game."*
  3. **Why it is surprising.** Name what a reasonable person would have expected,
     then say how the answer differs. *"Most people assume a one-game playoff
     merely fails to protect the better team. It does something stronger."*
  4. **What the reader gets.** What they will be able to see or do afterwards.

  Then close with a **titled takeaway section** — "What to take home: …".

  **The measured baseline, so the gap is not in doubt.** Across 146 published
  issues: only **7%** had a takeaway section, only **12%** asked a question in the
  opening, only **28%** ever named an expectation contrast. The frame was not
  slipping; it was mostly absent.

  `scripts/check_readability.py` now reports a READER'S CONTRACT verdict alongside
  the grade, and the worse of the two decides PASS/WARN/FAIL. Two missing elements
  is a fail on its own. **Honest limit, stated in the code too:** it detects
  whether those signals are *present*, not whether they are *good*. It cannot tell
  a real question from a rhetorical one. It catches the piece that never tries; a
  human still has to read it.

- **BOTTOM LINE UP FRONT, AND WRITE IT PLAIN.** This is the second rule because a
  reader told us on 2026-08-16 that the newsletter had become too opaque, and the
  archive agreed: median Flesch-Kincaid grade **7.8**, consensus grade **9**, only
  13 of 167 works at grade 6 or below. It had also drifted — the first twenty
  issues ran grade **6.8** and ~1,000 words, the last twenty ran **7.9** and
  ~1,270. Harder and longer, gradually, without anyone choosing it.

  Two requirements, both checkable:

  1. **The finding goes in the first breath.** The deck and the opening sentences
     state what happened and the number it rests on. Do not build to it. Do not
     set the scene. A reader who stops after two sentences should still have the
     point. *"A weak team wins 29 games out of 100 over a full season. In one
     sudden-death game it wins 48."* — that is an opening. *"Yesterday's piece
     found that a fan's deepest wound is always the identical injury…"* is a
     throat-clear.
  2. **Target a sixth-grade reading level.** Flesch-Kincaid **≤ 6.0**;
     6.0–7.0 is a warning; above 7.0 the draft is not ready. Practically: average
     sentence under ~14 words, few sentences over 25, plain words over Latinate
     ones (*about* not *approximately*, *shows* not *demonstrates*, *so* not
     *consequently*), one idea per sentence.

  **Run the check before queueing anything:**
  ```
  python3 scripts/check_readability.py queue/NNN-slug.html
  ```
  It reports the grade, flags long sentences, lists long words with short
  replacements, names AI/opacity tells drawn from the `humanizer` skill, and says
  whether a number appears in the opening. Autopublish runs it too, as a warning
  rather than a block.

  **Plain is not dumb, and plain is not soulless.** The `humanizer` skill
  (`~/.claude/skills/humanizer/SKILL.md`) is the reference for voice: vary
  sentence rhythm, have opinions, admit uncertainty, cut the promotional
  adjectives. Short sentences with nothing behind them are worse than long ones.
  The depth belongs in the concept primer and the methods box — the issue itself
  should be readable at a bus stop.

- **Refresh any live-standings piece the day before it publishes.** A queued issue
  freezes its numbers on the day it was written, and a headline built on a live
  standing can go false while it sits in the queue. This has now happened twice:
  #141 was written 2026-08-25 on "Boston has the best run differential in the AL
  East" and New York passed them two days later, +104 to +101, before it went
  out. Before a date-sensitive piece publishes, re-pull and check that the
  headline claim still holds. **Prefer a headline built on a gap that cannot flip
  overnight** (Tampa Bay is 50+ runs behind both chasers) over one built on a
  narrow lead (+101 vs +100).

- **Triple-verify every number**: Every statistic, record, score, streak, or standing published in an issue MUST be verified against at least 3 independent sources (e.g., ESPN, Baseball-Reference, MLB.com). If sources disagree, resolve the discrepancy before publishing. Never infer a number from another number (e.g., don't assume a losing streak grew by 1 because the record changed — check the actual game-by-game results). A newsletter built on statistical credibility cannot publish wrong numbers.
- **Single question per issue**: Every issue focuses on ONE statistical question.
- **No holiday specials**: Sports content only, no seasonal gimmicks. The ONE exception is MLB Opening Day — see below.
- **Opening Day is our New Year**: MLB Opening Day is the newsletter's annual anniversary. The Sports Page launched on Opening Day 2026 (March 27 — the Skenes 67.5 ERA issue). Every future Opening Day gets a special retrospective issue: the year in review, prediction accuracy across the full "Sports Page Year," milestones hit, lessons learned. Plan this in advance. The "Sports Page Year" runs from Opening Day to Opening Day — some years will be 365 days, others may gain or lose a week as MLB's schedule shifts. That's fine. No other holidays are observed, but Opening Day is not a holiday — it's the new year.
- **No name-dropping**: Do NOT label who in the family roots for which team. Cover the teams naturally. They know who they are.
- **Milestone issues**: Special treatment at #50, #100, etc.
- **Issue numbering**: Reader-facing numbers assigned at PUBLISH TIME, not creation time. Internal filenames keep their creation-order numbers.
- **Topic variety — no back-to-back**: NEVER publish two articles in a row on the same topic, sport, or series. If yesterday's issue was college football, today's must be something else. Three in a row on the same topic is forbidden unless a genuinely extraordinary event demands it (think: "sports as we know it ends" level). When selecting from queue/, check what was published yesterday and pick a DIFFERENT sport or topic. The EO series, for example, should be interleaved with MLB, NFL, NHL, or other content — never run consecutive EO parts on consecutive days.
- **Benched pieces have documented revival triggers.** A file kept in `queue/`
  but left out of `QUEUE_ORDER.txt` is benched on purpose. Before restoring one,
  read `tracking/back-burner.md` — it records *why* each is held and *what brings
  it back*. Never delete a benched file, and never tidy one into the order
  without checking its trigger. `088-sorsby` in particular is held for a
  one-year follow-up in 2027 **and** is Sal's Column, so it can never be
  autopublished under any circumstances.
- **NEVER auto-publish as Sal**: Sal is a guest columnist with a rare cadence (once every 2-3 weeks max). The scheduled agent must NEVER write in Sal's voice, publish a file bylined "By Sal", or generate Sal's Column content. Sal only writes when the human user explicitly invokes him ("let Sal take this one"). If a queued file is bylined as Sal, SKIP it and pick a different file. See SKILL.md "Sal's Column" section for the full persona/rules.

### The family picks ledger

`data/picks-ledger.json` records every confidence-pool pick with the model's
probability, the spread it came from, and the public split. `tracking/picks-ledger.md`
is the human-readable version. Update with `python3 scripts/picks_ledger.py --update`
and read it with `--report`.

**The point is calibration, not the score.** One 71% pick losing means nothing;
71% picks lose 29% of the time by construction. The question is whether the whole
band of 71% calls wins about 71% across a season, and that needs 25+ resolved
games before it says anything. The report prints that warning itself so nobody
reads a five-game sample as a verdict.

By November this becomes an issue: a calibration curve of our own published
forecasts. We ask other people for error bars constantly; this is the one place
we can be held to the same standard.

## Team & Sport Priorities (in order)

1. Notre Dame Fighting Irish football — always, year-round
2. College football — during season; off-season only when ND is involved
3. NY Mets (MLB) — during season
4. NY Rangers (NHL) — when doing well
5. NY Jets (NFL) — plus Raiders, Bills, Seahawks for the extended family
6. Any player with an amazingly great or horrible performance
7. No NBA — but WNBA is welcome on occasion when an interesting stat surfaces

## Sport-Season Calendar (topical relevance)

The newsletter exists in time. Each month has a different mix of what is actually happening in the sports world, and good editorial judgment matches today's issue to today's news cycle. This calendar tells Claude what is "live" and what is dormant in any given month, plus which annual events warrant pre-planned special treatment.

### Monthly mix — what is in season

| Month | Active cycles |
|---|---|
| **January** | NFL playoffs / Super Bowl buildup; CFP National Championship (early Jan); NHL/NBA mid-season; MLB hot stove finishes; CFB recruiting Signing Day (early-Jan/Feb) |
| **February** | Super Bowl (1st or 2nd Sunday); NHL/NBA all-star; MLB spring training opens (mid-month); CFB National Signing Day (1st Wed of Feb) |
| **March** | MLB spring training; March Madness Selection Sunday + tournament; **MLB Opening Day late March** (newsletter anniversary) |
| **April** | MLB Opening Week; NBA/NHL playoffs begin; The Masters (early April); NFL Draft (last week) |
| **May** | MLB regular season; Kentucky Derby (1st Saturday); Preakness (3rd Saturday); Indy 500 (Memorial Day weekend); NBA/NHL conference finals |
| **June** | Stanley Cup Final; NBA Finals; US Open golf; Belmont Stakes (early June); College World Series; MLB regular |
| **July** | MLB All-Star Break (mid-July); Wimbledon; Open Championship golf; MLB trade deadline (end of month) |
| **August** | NFL preseason; CFB season opens (last week); MLB pennant races; US Open tennis begins |
| **September** | NFL Week 1; CFB conference play; MLB final stretch; US Open tennis finals; WNBA playoffs |
| **October** | MLB playoffs / World Series; NFL mid-season; CFB mid-season; NHL/NBA seasons open |
| **November** | NFL stretch run; CFB rivalry games (Thanksgiving week); MLB awards season; CFP rankings begin; NBA early season |
| **December** | NFL playoff picture; CFB bowl games / CFP first round; NHL/NBA mid-season; MLB Winter Meetings |

### Tentpole annual events worth pre-planned issues

These are the days the calendar bends around. Each warrants its own issue, planned in advance when possible. The Opening Day anniversary is the only one whose framing was set when the newsletter launched; the rest are open formats.

- **MLB Opening Day** — newsletter anniversary. The "Sports Page Year" begins. Year-in-review issue: prediction accuracy across the full year, milestones hit, lessons learned. (Rule already in "Editorial Rules" above; this entry is the cross-reference.)
- **MLB First Day of Spring Training** (mid-February) — pitchers and catchers report; the year's first baseball issue.
- **Super Bowl Sunday** — eve-of preview + morning-after retrospective. Two issues, one weekend.
- **March Madness Selection Sunday** — bracket math piece (seed-vs-seed historical win rates, Cinderella conditions).
- **The Masters Sunday** — winner-takes-Augusta retrospective, with field-quality stats.
- **NFL Draft Round 1** — pick-by-pick statistical analysis, focus on AFC family teams (Jets, Bills, Raiders, Seahawks).
- **MLB All-Star Break** — first-half review issue; predictions reset; second-half projections.
- **MLB Trade Deadline** (end of July) — what the contenders did, with log5 swings.
- **World Series Game 1** — series preview with log5/Bayesian projection.
- **CFB Rivalry Week** (Thanksgiving) — Notre Dame's most-watched stretch; statistical retrospective on the rivalries the Irish play (USC, Stanford, Navy, plus current ACC/SEC matchups).
- **CFP National Championship** — annual title piece.
- **Pre-Season Simulation (recurring genre, one per sport per year)** — drops the week before each sport's regular season starts. Takes consensus pre-season expectations (Vegas win totals or equivalent) as the prior, applies a just-noticeable-difference threshold, and forecasts every regular-season game deterministically (or as a coin flip if the gap is within JND). Outputs: expected standings, playoff seeds, championship pick. The forecast is *intentionally* honest about uncertainty — most games near the JND threshold are explicit coin flips, not forced predictions. Sunday Editions grade weekly against this baseline. Schedule:
  - **NFL Pre-Season Sim** — last weekend of August (before Week 1 kickoff)
  - **CFB Pre-Season Sim** — last weekend of August (before Week 0/1)
  - **MLB Pre-Season Sim** — MLB Opening Day (bundles with newsletter-anniversary issue)
  - Methodology established in the "Pre-Season Simulation Framework" Methods piece. Use that as the recipe each time.

### Editorial guidance on topical relevance

- **Stay in season.** A January Mets piece is allowed but must justify its timing — hot-stove move, free agency, prospect news. Off-season Mets pieces about regular-season game logs are dead on arrival.
- **When multiple sports are simultaneously live**, prefer the one with the most recent extreme/counterintuitive stat. The newsletter's identity is THE stat, not THE league.
- **Date-sensitive pieces decay fast.** A "Mets are 20–26 through 46 games" piece must publish within ~7 days of the underlying data. Drafts that miss their window go to reserve/ for archive, not the front of QUEUE_ORDER.
- **The calendar interacts with the variety rule.** When choosing from the queue, prefer pieces whose sport is in active season. If two pieces are otherwise equivalent, the in-season one wins.
- **Sundays remain Sunday Edition only** — see the Sunday Edition Workflow in the Publishing section above. The seasonal calendar does not override this.

## Design System

Editorial broadsheet aesthetic (aged newsprint, NOT tech blog):

- **Fonts**: Playfair Display (headlines), Libre Baskerville (body), Roboto Mono (stats) — Google Fonts
- **Palette**: `--ink: #1a1208`, `--cream: #f5f0e8`, `--aged: #e0d8c5`, `--rust: #b83a1e`, `--steel: #2c4a6e`, `--gold: #c9962a`
- **Copy CSS from existing published issues** — do not invent new styles

## Statistical Models

| Context | Model | Prior |
|---|---|---|
| Pitching ERA | Gamma-Poisson | `alpha = 0.1 + career_ER, beta = 0.1 + career_IP` |
| Batting/FG%/completion | Beta-Binomial | `alpha = career_successes + prior_alpha, beta = career_failures + prior_beta` |
| Win percentage projection | Beta-Binomial | Prior from preseason + observed W/L |

## Current State (update this when publishing)

Published: 155 issues (#1-155, incl. Sunday Edition No. 021)
Queue: 9 articles ready (088-sorsby-supplemental-bet, 104-payroll-explosion-arms-race, 123-one-that-got-away, 124-how-many-stars, 137-schedule-leverage, 139-overfit-grid, 140-one-kick, 142-hope-curve, _TEMPLATE)
Concept primers: 27 published (latest: concepts/nomothetic-vs-idiographic.html, Concept No. 27)
Reserve: 2 evergreen pieces (incl. sunday-recap-template.html)
Goal: 345 issues remaining of 500
Last published: Issue #155 — "Five Structural Pieces and a Forecast That Landed." (sunday-021.html) on August 30, 2026
