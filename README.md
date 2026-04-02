# The Sports Page

A daily sports statistics newsletter for friends and family. Each issue takes one strange, extreme, or counterintuitive stat and explains what it actually means — the history, the math, and the forecast — in a broadsheet newspaper format.

## Live site

**https://pem725.github.io/the-sports-page/**

## Structure

```
published/          <- Live on the site, linked from index.html
queue/              <- Ready to publish on a specific date
reserve/            <- Evergreen content, no specific date
index.html          <- Homepage with archive of published issues
publish.sh          <- Script to move queue/reserve -> published and push
```

## Publishing workflow

1. Write a new issue (or ask Claude to build one)
2. Save it to `queue/` (if dated) or `reserve/` (if evergreen)
3. When ready to publish, add the entry to `index.html`
4. Run: `./publish.sh queue/005-draft-combinatorics.html`

Or just ask Claude: "publish Issue #5"

## Published issues

| # | Date | Topic | File |
|---|------|-------|------|
| 1 | Mar 27, 2026 | Paul Skenes' 67.5 ERA Opening Day | [001-skenes-era.html](published/001-skenes-era.html) |
| 2 | Mar 29, 2026 | Pete Alonso's Orioles Debut | [002-alonso-orioles.html](published/002-alonso-orioles.html) |
| 3 | Apr 1, 2026 | The Misery Index: Down 14% | [003-misery-index.html](published/003-misery-index.html) |
| 4 | Apr 2, 2026 | Mets 3-3: 50% Extra Innings | [004-mets-500.html](published/004-mets-500.html) |

## Queued (ready to publish)

| # | Target Date | Topic | File |
|---|-------------|-------|------|
| 5 | Apr 3 | NFL Draft Combinatorics | [005-draft-combinatorics.html](queue/005-draft-combinatorics.html) |
| 6 | Apr 4 | Jets Draft Misery | [006-jets-draft.html](queue/006-jets-draft.html) |
| 7 | Apr 5 | Mets Alumni All-Stars | [007-mets-alumni.html](queue/007-mets-alumni.html) |

## Reserve (evergreen, no date)

(empty — add pre-season college football, coaching analyses, etc.)
