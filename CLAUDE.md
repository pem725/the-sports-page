# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**The Sports Page** — a daily sports statistics newsletter at https://pem725.github.io/the-sports-page/. Each issue takes one strange, extreme, or counterintuitive stat and explains what it actually means. Goal: 500 issues over ~2 years. Current state is tracked at the bottom of this file.

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

### Step 0 — CHECK THE DAY OF WEEK FIRST (before anything else)

**STOP. Before touching the queue, before picking any file, before making any decisions: check what day it is today.**

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

6. **Cross-reference check**: Grep the file for "Issue #", "Issue No.", and "See Issue" — verify every reference points to an ALREADY PUBLISHED issue. If referencing an unpublished piece, change to "coming soon."

7. **Add the entry to index.html**: Insert a new `<div class="issue">` block at the TOP of `<div class="issues">`, BEFORE all existing issues. Follow the exact HTML pattern of existing entries. Include: issue-num, issue-date, issue-hed (with link to `published/FILENAME`), issue-deck, and issue-tags.

8. **Move the file**: `git mv queue/FILENAME.html published/FILENAME.html`

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

A GitHub Actions workflow (`.github/workflows/autopublish.yml`) runs at 4:30am ET Monday–Saturday. It calls `scripts/autopublish.py` which handles the full Regular Publishing Workflow deterministically. **Sunday Editions remain manual** — they require live data, prediction scoring, and editorial prose that a script cannot provide.

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

5. **Replace every example value in the working file** (`queue/sunday-NNN.html`):
   - Title and masthead: set correct Sunday Edition number, date, and reader-facing issue number (count published non-sunday issues + count of published sunday issues + 1)
   - Stat cards: current issue count, predictions-hit ratio, issues remaining to 500
   - Issue list: the 5–7 issues published in the past 7 days, with correct links
   - Prediction scorecard table: one row per prediction rerun, with fresh outcomes and grades
   - "What we got right" / "What we got wrong" sections: write fresh based on this week's actual outcomes
   - Over-reactions / under-reactions: fresh honest self-assessment
   - Road ahead: preview next week's planned content from the queue
   - Footer: update Sunday Edition number and "predictions tracked from" range

6. **Cross-reference check**: Grep the working file for "Issue #", "Issue No.", and "See Issue" — verify every reference points to an ALREADY PUBLISHED issue.

7. **Move the file**:
   ```
   git mv queue/sunday-NNN.html published/sunday-NNN.html
   ```

8. **Add entry to `index.html`**: Insert a new `<div class="issue">` block at the top, with the correct reader-facing issue number, link, headline, and tags (use `.tag` for "Sunday Edition").

9. **Commit and push**:
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

### Content Tiers:
- **Timely**: Breaking news, injuries, game results. Publish immediately. Goes stale fast.
- **Analytical**: Trade analyses, historical comparisons, series pieces. Publish to fill gaps.
- **Evergreen**: Off-season analyses, methodology explainers. Publish anytime.

## Editorial Rules

- **Single question per issue**: Every issue focuses on ONE statistical question.
- **No holiday specials**: Sports content only, no seasonal gimmicks.
- **No name-dropping**: Do NOT label who in the family roots for which team. Cover the teams naturally. They know who they are.
- **Milestone issues**: Special treatment at #50, #100, etc.
- **Issue numbering**: Reader-facing numbers assigned at PUBLISH TIME, not creation time. Internal filenames keep their creation-order numbers.
- **Topic variety — no back-to-back**: NEVER publish two articles in a row on the same topic, sport, or series. If yesterday's issue was college football, today's must be something else. Three in a row on the same topic is forbidden unless a genuinely extraordinary event demands it (think: "sports as we know it ends" level). When selecting from queue/, check what was published yesterday and pick a DIFFERENT sport or topic. The EO series, for example, should be interleaved with MLB, NFL, NHL, or other content — never run consecutive EO parts on consecutive days.
- **NEVER auto-publish as Sal**: Sal is a guest columnist with a rare cadence (once every 2-3 weeks max). The scheduled agent must NEVER write in Sal's voice, publish a file bylined "By Sal", or generate Sal's Column content. Sal only writes when the human user explicitly invokes him ("let Sal take this one"). If a queued file is bylined as Sal, SKIP it and pick a different file. See SKILL.md "Sal's Column" section for the full persona/rules.

## Team & Sport Priorities (in order)

1. Notre Dame Fighting Irish football — always, year-round
2. College football — during season; off-season only when ND is involved
3. NY Mets (MLB) — during season
4. NY Rangers (NHL) — when doing well
5. NY Jets (NFL) — plus Raiders, Bills, Seahawks for the extended family
6. Any player with an amazingly great or horrible performance
7. No NBA — but WNBA is welcome on occasion when an interesting stat surfaces

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

Published: 20 issues (#1-20)
Queue: 4 articles ready (014, 015, 017, eo-006)
Reserve: 1 evergreen piece
Goal: 480 issues remaining of 500
Last published: Issue #20 — "WNBA Players Make 116x Less Than NBA Players. That Number Is True. It's Also the Wrong Comparison." (016-wnba-pay-maturity.html) on April 17, 2026
