# Momentum: is there such a thing as a hot team? (spec, 2026-11-18)

The editor's question (with Gene and Tim): "At this point of the season you have no idea what's
going to happen. It happens in December when a team just clicks." Does a hot November make a hot
December and January? Is there win momentum? When can you see it? Do we see it now?

Every sport answers the SAME three tests, so the piece can lay them side by side.

## Test A: the streak test (game level)
Does a team that has won its last 3 (and last 5) win its NEXT game more often than its strength
says it should? Same for losing streaks.
- "Should" must come from information available BEFORE the game. Prefer the betting market
  (vig-free moneyline, or spread through a normal curve) where the data has it. Otherwise use a
  pregame rating (e.g. CFBD pregame Elo) or log5 of both teams' season win% EXCLUDING the game
  being predicted (state which).
- Report, per streak bucket (W5+, W3+, none, L3+, L5+): number of games, actual wins per 100,
  expected wins per 100, gap, and a standard error. Regular season only for the streak count;
  streaks reset at season start.
- Why the expected-probability benchmark matters: teams on streaks are better teams. Comparing to
  .500 or to season win% (including the game) manufactures momentum or kills it.

## Test B: the "clicks in December" test (team-season level)
Among postseason teams, does LATE form predict postseason success beyond full-season strength?
- Late form: the last ~quarter of the regular season (NFL: last 5 games; CFB: November games;
  MLB: final 30 games; NHL: final 20 games). Measure it as point/run/goal differential per game
  in that window (and win% as a second version).
- Season strength: differential per game over the WHOLE regular season (or the season minus the
  late window; report both if cheap).
- Outcome: postseason wins (or series won), and/or win rate in postseason games versus the
  pregame expectation (market where available).
- Report: correlation of late form with the outcome, and what late form ADDS once season
  strength is known (partial correlation, or change in R^2, or a simple matched comparison:
  hot vs cold teams with similar season strength). Bootstrap or standard errors.
- Also the forward version for football specifically: does November form predict
  December regular-season results beyond season strength?

## Test C: now (2026)
Who is hot right now, by the same definitions, and what Tests A and B say that is worth.

## Rules (binding)
- Never expand a secret. Load keys with `set -a; . ~/.config/secrets/tokens.env; set +a` and read
  them only via os.environ inside Python. Never echo/printenv/${VAR:-}.
- CFBD quota: hard cap 60 calls; check X-CallLimit-Remaining; cache everything.
- A web-search summary is never a source of a number. Primary feeds only.
- At most 2 significant digits in what you report as headline numbers; rates as counts per 100.
- Write code + results to research/momentum/<your-folder>/ only. Do NOT edit queue/, published/,
  QUEUE_ORDER.txt, scripts/, or anything else. Do NOT commit or push.
- Small samples: say how many games/team-seasons sit behind every number. If the data cannot
  separate momentum from nothing, that IS the finding; say so plainly.
