# Patrick's Pool — the competing methods

Not a leaderboard. A comparison of *approaches*, which is the only reason the
pool is interesting to this paper. Every entrant is asked for their reasoning
once picks lock — dictated, informal, whatever they like. The reasons are the
data; the record is just the outcome.

## The entries

| method | what it is | why it is in the study |
|---|---|---|
| **The Sports Page** | SP+ frozen before kickoff, priced against the closing line, confidence by size of disagreement | The number. Measured at 51.0% over 2,140 games — no edge claimed |
| **The eye test** | Watching teams, reading situations, coaching, grudges, travel | Sees things no rating represents. The Franklin/Maryland pick is the worked example |
| **Whimsy** | Mascots, colours, paw prints, whatever the picker likes | **The control.** This is the important one |

## Why the whimsy entry matters most

A picker choosing on mascots is approximately random, and random is the null
hypothesis. Without it, a model at 53% and a fan at 55% look like two competing
skills. With it, we find out whether either is skill at all.

State the expectation in advance, as always: **the whimsy entry should finish
near 50% and near the middle of the standings.** If it wins the season, that is
not a charming story about beginner's luck — it is evidence that nobody in this
pool is doing anything, and we will print it that way.

## On naming

This repository is public. Use **method labels** rather than the names of
children — "the paw-print method" — which is better writing anyway and costs
nothing. Adults who want their first name on their reasoning can have it; that is
their call to make, not ours to assume.

## The cadence

1. Picks lock.
2. Everyone sends their reasoning. No length requirement; a sentence is fine.
3. The Sports Page's reasoning is sealed before kickoff (`scripts/seal.py`) and
   revealed after, so it cannot be quietly improved in hindsight.
4. Sunday: grade the picks, the reasons, and the advice separately.

## What this becomes

By November there is a real piece here: a season of forecasts from a model, from
people who watch the games, and from a child picking dogs — all graded against
the same closing lines. Very few outlets will publish the version where the dogs
win.
