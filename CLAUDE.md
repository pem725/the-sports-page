# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

**The Sports Page** — a daily sports statistics newsletter at https://pem725.github.io/the-sports-page/. Each issue takes one strange, extreme, or counterintuitive stat and explains what it actually means. Goal: 500 issues over ~2 years. Currently at Issue #10 published (reader-facing numbering).

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

### To publish the next queued article:

1. **Pick the next file** from `queue/` — choose the most timely piece, or the next in sequence if nothing is urgent.

2. **Determine the reader issue number**: Count the published issues in `index.html` and add 1. The reader number is SEQUENTIAL based on publication order, NOT the internal filename number.

3. **Update the issue number inside the HTML file**: Search for "Issue No." and replace with the correct reader number (e.g., "Issue No. 14"). There are usually 2 occurrences (datebar and footer).

4. **Update the date**: If the article has a placeholder or old date, update it to today's date.

5. **Add the entry to index.html**: Insert a new `<div class="issue">` block at the TOP of the issues list (before the previous highest issue). Follow the exact HTML pattern of existing entries. Include: issue-num, issue-date, issue-hed (with link to `published/FILENAME`), issue-deck, and issue-tags.

6. **Move the file**: `git mv queue/FILENAME.html published/FILENAME.html`

7. **Cross-reference check**: Grep the file for "Issue #", "Issue No.", and "See Issue" — verify every reference points to an ALREADY PUBLISHED issue. If referencing an unpublished piece, change to "coming soon."

8. **Commit and push**:
   ```
   git add index.html published/FILENAME.html
   git commit -m "Publish Issue #N: brief description"
   git push
   ```

### Sunday Edition (special):
- Every Sunday, publish a recap issue that lists the week's posts and grades prediction accuracy.
- Sunday editions should be finalized with FRESH data (current standings, injury updates, etc.) — not pre-built days in advance.
- Grade predictions: HIT, MISS, PARTIALLY HIT, or PENDING.

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

## Team & Sport Priorities (in order)

1. Notre Dame Fighting Irish football — always, year-round
2. College football — during season; off-season only when ND is involved
3. NY Mets (MLB) — during season
4. NY Rangers (NHL) — when doing well
5. NY Jets (NFL) — plus Raiders, Bills, Seahawks for the extended family
6. Any player with an amazingly great or horrible performance
7. No basketball

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

Published: 10 issues (#1-10)
Queue: 8 articles ready
Reserve: 1 evergreen piece
Goal: 490 issues remaining of 500
