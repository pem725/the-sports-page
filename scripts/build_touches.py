#!/usr/bin/env python3
"""One row per chance a player had to gain yards.

    python3 scripts/build_touches.py --from 2015 --to 2024

THE EDITOR'S ASK, 2026-09-23: "I'd really like to have an estimate of median per
touch by each offensive player who touches the ball. Median yards per touch, not
the average."

WHY THIS STORES OPPORTUNITIES AND NOT JUST TOUCHES. He made the argument himself,
in baseball: "sometimes the most likely occurrence for a baseball player is that
he strikes out... if he doesn't hit a home run he strikes out." The strikeout is
the point. It is the outcome that never appears in a batting average and dominates
the distribution.

A receiver has the same hole. Count only the passes he CAUGHT and the incompletions
vanish -- and an incompletion is a play that happened, on which his team gained
nothing. So every row here is a CHANCE: each carry, and each target whether caught
or not. `touched` marks which of them he actually got his hands on.

That one column is the difference between two honest answers to the same question:

  median yards per TOUCH        -- what happens when he gets it
  median yards per OPPORTUNITY  -- what happens when they try to get it to him

For running backs those are nearly the same number. For receivers they are not
remotely the same, and the gap is the story.

WHAT IS DELIBERATELY NOT HERE. Sacks are not charged to anybody: the editor is
right that a blown block leading to zero or negative yards should count against the
line, but public play-by-play cannot tell a blown block from a receiver who never
came open, and inventing an attribution would be worse than admitting the gap.
Fumbles are recorded but not netted out of the yardage, because the yards were
genuinely gained before the ball was lost -- treating them as zero would mix two
different questions.

Two-point conversions are excluded: they are scored in points, not yards, and a
`yards_gained` of 3 on a two-point play does not mean what it means elsewhere.
"""
import argparse
import csv
import gzip
import io
import pathlib
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "nfl" / "touches.csv"
URL = ("https://github.com/nflverse/nflverse-data/releases/download/pbp/"
       "play_by_play_{year}.csv.gz")


def num(s, d=0.0):
    try:
        return float(s)
    except (TypeError, ValueError):
        return d


def season_rows(year):
    raw = urllib.request.urlopen(URL.format(year=year), timeout=300).read()
    rd = csv.DictReader(io.TextIOWrapper(
        gzip.GzipFile(fileobj=io.BytesIO(raw)), encoding="utf-8", errors="replace"))
    out = []
    for r in rd:
        if r.get("season_type") != "REG" or num(r.get("two_point_attempt")) == 1:
            continue
        pt = r.get("play_type")
        if pt == "run":
            pid, name = r.get("rusher_player_id"), r.get("rusher_player_name")
            if not pid:
                continue
            out.append((year, pid, name, "rush", 1,
                        round(num(r.get("rushing_yards")), 1),
                        round(num(r.get("epa")), 4),
                        int(num(r.get("fumble_lost")) == 1)))
        elif pt == "pass":
            pid, name = r.get("receiver_player_id"), r.get("receiver_player_name")
            if not pid:
                continue  # sack, throwaway, or nobody targeted -- see docstring
            caught = num(r.get("complete_pass")) == 1
            out.append((year, pid, name, "target", int(caught),
                        round(num(r.get("receiving_yards")) if caught else 0.0, 1),
                        round(num(r.get("epa")), 4),
                        int(num(r.get("fumble_lost")) == 1)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="lo", type=int, default=2015)
    ap.add_argument("--to", dest="hi", type=int, default=2024)
    a = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["season", "player_id", "player", "kind", "touched",
                    "yards", "epa", "fumble_lost"])
        for yr in range(a.lo, a.hi + 1):
            rows = season_rows(yr)
            w.writerows(rows)
            n += len(rows)
            touched = sum(r[4] for r in rows)
            print(f"  {yr}  {len(rows):>6,} chances  {touched:>6,} touches "
                  f"({touched/len(rows):.1%})", flush=True)
    print(f"\n  {n:,} rows -> {OUT}")

    # A carry is a touch by definition; if that ratio is not 100% something is wrong.
    import collections
    chk = collections.Counter()
    for r in csv.DictReader(open(OUT)):
        chk[(r["kind"], r["touched"])] += 1
    rush_untouched = chk[("rush", "0")]
    print(f"  sanity: carries recorded as not-touched = {rush_untouched} (must be 0)")
    if rush_untouched:
        raise SystemExit("a carry that was never touched -- parser is wrong")
    return 0


if __name__ == "__main__":
    sys.exit(main())
