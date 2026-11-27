# Judges' Scorecard No. 3 (Wed Dec 2): Tuesday-night runbook

The CFP ranking comes out Tuesday Dec 1, about 9pm ET. Nothing in this piece may cite it before then.

1. `set -a; . ~/.config/secrets/tokens.env; set +a`
2. `python3 weekly.py --refresh`: 2 CFBD calls; writes weekly-2026-12-02.json (results + new ranking).
3. `python3 grade_rivalry.py`: grades the predictions frozen in commit 4cd49e7 (Thursday 11/26,
   before the first game). It refuses to run until a weekly file newer than the predictions exists.
4. `python3 tables3.py > /tmp/tables3.html`: the two tables, house style.
5. Write the piece from queue/213-judges-scorecard-2.html's shell (head, CSS, footer, ASK block,
   WATCH_BLOCK marker); queue file 221-judges-scorecard-3.html; PUBLISH-META topic CFB, decay dated.

**The angle: we grade ourselves first.** On Thursday we said what each result should do to each
team's playoff and bye chances. Did the committee move the way the math said?
- Upsets: expected (sum of underdog chances) vs actual. A weekend of 67 games should produce ~18.
- Brier score of our win chances vs a coin flip (.25) AND the crowd's spread:
  `python3 scripts/brier_scorecard.py --refresh --week 13` (season: ours .19, crowd .18).
- Team by team: our chance of the field given the actual result vs the committee's new rank
  (top 12 as the proxy for "in": champion bids aren't settled until Selection Day; say so).
- The big four from the frozen file: USC-UCLA (leverage 1.14), Washington-Oregon (.91),
  Cincinnati-BYU (.91); Notre Dame's bye (61 now, 65 with a win, 0 with a loss).
- Then the usual: the committee's top 12 vs our math, movers, the season tally of who picked winners.

**Checks before queueing:** check_readability, check_voice, check_headline, check_scores (with
--date for Saturday), check_poll_claims, link_targets --check; render the OG card; queue_health.
Add 221 to QUEUE_ORDER for Wed Dec 2 only after all pass.
