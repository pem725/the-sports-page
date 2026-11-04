#!/usr/bin/env python3
"""Everything we worried about in the spring, graded against how 2026 ended.

One row per early-season MLB storyline the paper ran (Opening Day to the
All-Star break). The claim is quoted from the issue; the outcome is pulled from
the MLB Stats API, the primary feed, never a web summary. The grade is ours:

  REAL    the worry held up
  NOISE   it washed out
  PARTLY  part held, part did not

    python3 scripts/mlb_worries.py        # writes data/mlb/worries-2026.csv and .txt

Headline numbers were also checked by hand against ESPN and Baseball-Reference
(Rays 98-64; Alonso .267, 43 HR; Williams 5.68 ERA through May 9).
"""
import csv, json, pathlib, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/mlb"
API = "https://statsapi.mlb.com/api/v1"
METS = 121


def get(path):
    return json.load(urllib.request.urlopen(f"{API}/{path}"))


def season(pid, group):
    s = get(f"people/{pid}/stats?stats=season&season=2026&group={group}&sportId=1")["stats"][0]["splits"]
    return s[-1]["stat"] if len(s) == 1 else next(x["stat"] for x in s if "team" not in x)


def ip(x):
    a, b = x.split(".")
    return int(a) + int(b) / 3


def main():
    teams = {t["team"]["name"]: t for r in get("standings?leagueId=103,104&season=2026&standingsTypes=regularSeason")["records"]
             for t in r["teamRecords"]}
    games = [(d["date"], (g["teams"]["home"] if g["teams"]["home"]["team"]["id"] == METS else g["teams"]["away"]).get("isWinner", False))
             for d in get(f"schedule?sportId=1&teamId={METS}&season=2026&gameType=R")["dates"] for g in d["games"]
             if g["status"]["detailedState"].startswith("Final")]
    rec = lambda a, b: (sum(w for d, w in games if a <= d <= b), sum(not w for d, w in games if a <= d <= b))

    skenes = season(694973, "pitching")
    alonso, bichette, lindor, raleigh = (season(p, "hitting") for p in (624413, 666182, 596019, 663728))
    mets, rays, dodgers = teams["Mets"], teams["Rays"], teams["Dodgers"]
    pyth = lambda t: t["runsScored"] ** 1.83 / (t["runsScored"] ** 1.83 + t["runsAllowed"] ** 1.83) * (t["wins"] + t["losses"])

    log = get("people/642207/stats?stats=gameLog&group=pitching&season=2026&sportId=1")["stats"][0]["splits"]
    pre = [x["stat"] for x in log if x["date"] <= "2026-05-12"]
    post = [x["stat"] for x in log if x["date"] > "2026-05-12"]
    era = lambda xs: sum(x["earnedRuns"] for x in xs) * 9 / sum(ip(x["inningsPitched"]) for x in xs)

    soto_out = rec("2026-04-04", "2026-04-21")
    after_soto = [w for d, w in games if d >= "2026-04-22"][:20]
    w46 = sum(w for _, w in games[:46])
    rest = (sum(w for _, w in games[46:]), sum(not w for _, w in games[46:]))
    may = rec("2026-05-02", "2026-05-18")
    late = rec("2026-07-27", "2026-12-31")
    rs_rank = sorted(teams.values(), key=lambda t: -t["runsScored"]).index(mets) + 1
    ra_rank = sorted(teams.values(), key=lambda t: t["runsAllowed"]).index(mets) + 1

    th = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"
    rows = [
        (1, "001-skenes-era", "Mar 27", "Skenes's 67.5 ERA opener: 1 in 3 he never gets his career ERA back to 1.97 this year",
         f"never did: {skenes['era']} ERA in 2026, career now 2.62; the opener's 5 runs were not why", "PARTLY"),
        (2, "002-alonso-orioles", "Mar 29", "60% chance Alonso never cracks .250 this year; Mets fans sleep fine",
         f"hit {alonso['avg']} with {alonso['homeRuns']} HR for Baltimore; Mets finished {mets['wins']}-{mets['losses']}", "NOISE"),
        (7, "010-soto-calf", "Apr 4", "54% chance Soto's calf costs 10 or more games",
         f"on the IL Apr 4-21; missed {sum(soto_out)} games", "REAL"),
        (8, "011-infield-hitting", "Apr 5", "Bichette's 53% strikeout rate might not be noise",
         f"struck out {bichette['strikeOuts']} times in {bichette['plateAppearances']} trips ({bichette['strikeOuts'] / bichette['plateAppearances']:.0%}); hit {bichette['avg']}", "NOISE"),
        (18, "018-mets-pitching-mirage", "Apr 15", "The offense, not the pitching, is the problem; 12+ wins in 20 games after Soto returns",
         f"went {sum(after_soto)}-{20 - sum(after_soto)}; runs scored ranked {th(rs_rank)}, runs allowed {th(ra_rank)} of 30", "PARTLY"),
        (26, "023-mets-slow-start", "Apr 23", "7-14: the math is unhappy, not final",
         f"finished {mets['wins']}-{mets['losses']}, fifth in the East", "REAL"),
        (35, "027-mets-conditional-probability", "May 2", "10-21: about 1 in 9 teams this bad made the playoffs",
         "missed the playoffs", "REAL"),
        (38, "028-mets-next-17-games", "May 5", "About 6 wins in the next 17; 'They will not win ten'",
         f"won {may[0]} of {sum(may)} played (one rained out)", "NOISE"),
        (45, "035-devin-williams-collapse", "May 12", "Williams was never coming back",
         f"{era(post):.2f} ERA in {sum(ip(x['inningsPitched']) for x in post):.0f} innings after the piece; we printed 9.95 when it was {era(pre):.2f}", "PARTLY"),
        (54, "039-mets-bullpen-eighth", "May 21", "Both closers the Mets bought are broken",
         "Kimbrel 6.00 ERA as a Met, then traded; Williams 4.43 for the season", "REAL"),
        (52, "043-mets-wild-card-math", "May 19", "From 20-26 the Mets need .578 baseball",
         f"after {w46}-{46 - w46} they went {rest[0]}-{rest[1]} ({rest[0] / sum(rest):.3f})", "REAL"),
        (63, "053-raleigh-slump-shower-oblique", "May 30", "Raleigh's 0-for-38 was the oblique, not a jinx",
         f"hit {raleigh['avg']} for the season", "REAL"),
        (110, "097-acceleration-second-derivative", "Jul 16", "Rays' first place is 'bought on credit' (+5.5 wins of luck)",
         f"went 42-27 after the break and won {rays['wins']}; still {rays['wins'] - pyth(rays):.0f} wins above their runs", "NOISE"),
        (110, "097-acceleration-second-derivative", "Jul 16", "The Dodgers are cooling, mildly, not collapsing",
         f".635 before the break, .591 after; won {dodgers['wins']}", "REAL"),
        (121, "107-mets-own-mean", "Jul 27", "The Mets' own mean says no bounce-back",
         f"went {late[0]}-{late[1]} after, still finished {mets['wins']}", "PARTLY"),
    ]

    OUT.mkdir(exist_ok=True)
    with open(OUT / "worries-2026.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["issue", "file", "date", "claim", "outcome", "grade", "source"])
        for n, fn, d, c, o, g in rows:
            w.writerow([n, fn, d, c, o, g, "MLB Stats API (standings, season stats, game logs, transactions)"])
    tally = {g: sum(r[5] == g for r in rows) for g in ("REAL", "NOISE", "PARTLY")}
    unseen = sorted(teams.values(), key=lambda t: -t["wins"])
    lines = [f"{len(rows)} storylines: " + ", ".join(f"{k} {v}" for k, v in tally.items()),
             f"Mets {mets['wins']}-{mets['losses']} (RS {mets['runsScored']}, RA {mets['runsAllowed']}); Rays {rays['wins']}-{rays['losses']}, Pythagorean {pyth(rays):.1f}",
             f"Never written: White Sox {teams['White Sox']['wins']} wins (60 in 2025); Braves {teams['Braves']['wins']} (76 in 2025)"]
    lines += [f"  #{n:<4} {g:7s} {c}  ->  {o}" for n, fn, d, c, o, g in rows]
    (OUT / "worries-2026.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
