# Trade projects — seed datasets

Two growing reference datasets for future Sports Page issues, seeded 2026-07-31.
Both feed off the same verified research, so a newly-confirmed trade usually adds
a row to each.

**The rule: verified entries only.** Every row with `verified = yes` has been
checked against reputable sources (SABR, the Baseball Hall of Fame, MLB.com,
Baseball-Reference, contemporaneous reporting). Rows marked `no` / `TBD` are
placeholders — do the research and triple-verify (per CLAUDE.md) before flipping
them to `yes`. Never publish an unverified date, score, or return.

---

## 1. `one-that-got-away.csv` — each team's worst "one that got away"

The companion to Issue #123 ("Every Team Has Its Babe Ruth"). Keyed by the team
that **gave the player away** (their blunder), with the beneficiary in `to_team`.
Skeleton has all 30 franchises; fill one canonical entry per team.

Columns: `team_gave_away, player, to_team, year, date_iso, got_back,
player_career_bwar_approx, hall_of_famer, notable_alternates, verified, source`.

Seeded (7 of 30 verified): Red Sox (Babe Ruth), Mets (Nolan Ryan), Cubs (Lou
Brock), Tigers (John Smoltz), Reds (Frank Robinson), Dodgers (Pedro Martinez),
Phillies (Ryne Sandberg). Some teams have two famous ones (Red Sox: Ruth +
Bagwell; Mets: Ryan + Crow-Armstrong) — the second lives in `notable_alternates`.
The 23 `TBD` rows are the research queue.

Eventual issue: a full 30-team accounting / reference table (the user's ask).

## 2. `bad-trade-calendar.csv` — a bad trade for (eventually) every day

The "every day of the year has a historically bad baseball trade" idea. One row
per verified, **dated** deal. Baseball-only by design — its long control windows
and trade culture make lopsided deals uniquely possible (football/basketball have
too much free agency). Could eventually feed the repo's almanac
(`scripts/almanac.py`).

Columns: `month, day, year, player, from_team, to_team, got_back, note, verified,
source`. Sorted by calendar date (month, day).

Seeded (9 dated entries): Jan 5 (Ruth), Jan 27 (Sandberg), Jun 15 (Brock), Jul 30
(Crow-Armstrong), Aug 12 (Smoltz), Aug 30 (Bagwell), Nov 19 (Pedro), Dec 9 (Frank
Robinson), Dec 10 (Nolan Ryan). Goal: broaden toward full-calendar coverage,
adding a verified dated trade per session.

Eventual build: an interactive "on this day" bad-trade calendar (XKCD-style toy
or almanac page).

---

### How to grow (each future session)
1. Pick a target team (`TBD` in file 1) or an empty stretch of the calendar.
2. Research its canonical worst trade; verify date + return + outcome against 2-3
   sources.
3. Add the row(s) to both files where applicable; set `verified = yes` with the
   source. Round career WAR to two significant figures.
4. When file 1 nears 30 and file 2 is broad enough, draft the reference pieces.
