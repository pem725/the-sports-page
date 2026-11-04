#!/usr/bin/env python3
"""How often does a player listed QUESTIONABLE actually play?

The NFL's final injury report, matched to that week's snap counts (nflverse,
2013 on). A player "played" if he logged any snap -- offense, defense or
special teams -- in that week's game for that team.

College football has no comparable public archive, so the NFL is the
measured case and the college game is the one we are asking about.

The 2016 rule change matters: the league dropped PROBABLE, so from 2016
QUESTIONABLE also holds the players who would once have been probable.
Results are split at that line.

Inputs cached under ~/.cache/sports-page/nflverse (injuries_YYYY.csv,
snaps_YYYY.csv.gz, players.csv). Output: data/questionable_plays.txt
"""
import collections, csv, gzip, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path.home() / ".cache/sports-page/nflverse"
OUT = ROOT / "data/questionable_plays.txt"


def main():
    lines = []
    say = lambda s="": (print(s), lines.append(s))

    pfr = {r["gsis_id"]: r["pfr_id"] for r in csv.DictReader(open(CACHE / "players.csv")) if r.get("pfr_id")}

    tally = collections.defaultdict(lambda: [0, 0])  # key -> [played, listed]
    for y in range(2013, 2026):
        snapped = set()
        try:
            for r in csv.DictReader(gzip.open(CACHE / f"snaps_{y}.csv.gz", "rt")):
                if r["game_type"] == "REG" and any(float(r[k] or 0) > 0 for k in ("offense_snaps", "defense_snaps", "st_snaps")):
                    snapped.add((r["pfr_player_id"], int(r["week"])))
        except EOFError:  # a truncated upstream file is skipped, not half-read
            continue
        if not snapped:
            continue
        era = "2013-15" if y < 2016 else "2016-25"
        for r in csv.DictReader(open(CACHE / f"injuries_{y}.csv")):
            st, pid = r["report_status"], pfr.get(r["gsis_id"])
            if r["game_type"] != "REG" or not st or not pid:
                continue
            played = (pid, int(r["week"])) in snapped
            dnp = r["practice_status"].startswith("Did Not")
            ankle = "ankle" in (r["report_primary_injury"] or "").lower()
            for key in [(era, st), (era, st, "WR" if r["position"] == "WR" else None),
                        (era, st, "ankle" if ankle else None), (era, st, "DNP final day" if dnp else None),
                        (era, st, "full or limited final day" if not dnp else None)]:
                if None in key:
                    continue
                tally[key][0] += played
                tally[key][1] += 1

    say("NFL final injury report vs. that week's snap counts, regular season")
    for era in ("2013-15", "2016-25"):
        say(f"\n{era}")
        for k in sorted(k for k in tally if k[0] == era):
            p, n = tally[k]
            say(f"  {' / '.join(k[1:]):42s} played {p:6d} of {n:6d} = {p / n:.0%}")
    OUT.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
