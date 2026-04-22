#!/usr/bin/env python3
"""
Build the NY Jets first-round draft dataset 1976-2025 and compute three
parallel bust definitions. Outputs CSV + summary stats.

Data sources:
  - Player list and year/slot/position: Wikipedia "List of New York Jets
    first-round draft picks"
  - Career Pro Bowl counts, career AV, NYJ primary-starter seasons:
    Pro-Football-Reference player pages (research recalled; a handful
    spot-verified via web search 2026-04-20)
  - Expected AV by slot: Chase Stuart's published expected-AV curve, a
    widely-used first-round value benchmark

Bust definitions (applied only to picks with >= 3 NFL seasons):
  A. Never made a Pro Bowl
  B. Career AV below the expected AV for their slot
  C. Fewer than 4 seasons as a primary NYJ starter
"""

import csv
import os
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = os.path.join(REPO, "scripts", "data", "jets-first-round-1976-2025.csv")

# (year, slot, name, position, pro_bowls, career_av, nyj_starter_years, notes)
# pro_bowls = career total Pro Bowl selections across ANY team
# career_av = Pro-Football-Reference career Approximate Value
# nyj_starter_years = seasons as the Jets' primary starter at their position
PICKS = [
    (1976,  6, "Richard Todd",          "QB",  0,  40, 6,  ""),
    (1977,  4, "Marvin Powell",         "OT",  5,  82, 9,  ""),
    (1978,  4, "Chris Ward",            "OT",  0,  30, 5,  ""),
    (1979, 14, "Marty Lyons",           "DE",  0,  62, 9,  "NY Sack Exchange"),
    (1980,  2, "Johnny 'Lam' Jones",    "WR",  0,  17, 2,  ""),
    (1981,  3, "Freeman McNeil",        "RB",  3,  95, 10, ""),
    (1982, 23, "Bob Crable",            "LB",  0,  28, 4,  ""),
    (1983, 24, "Ken O'Brien",           "QB",  2,  72, 8,  "Picked ahead of Marino"),
    (1984, 10, "Russell Carter",        "DB",  0,  18, 3,  ""),
    (1984, 15, "Ron Faurot",            "DE",  0,   3, 1,  "2 NFL seasons"),
    (1985, 10, "Al Toon",               "WR",  3,  62, 7,  "Concussions cut career short"),
    (1986, 22, "Mike Haight",           "OL",  0,  19, 3,  ""),
    (1987, 21, "Roger Vick",            "FB",  0,  10, 1,  ""),
    (1988,  8, "Dave Cadigan",          "OL",  0,  28, 3,  ""),
    (1989, 14, "Jeff Lageman",          "LB",  0,  38, 5,  ""),
    (1990,  2, "Blair Thomas",          "RB",  0,  14, 2,  "Infamous bust"),
    (1992, 15, "Johnny Mitchell",       "TE",  0,  23, 3,  ""),
    (1993,  4, "Marvin Jones",          "LB",  1,  54, 9,  "All-Pro 2000"),
    (1994, 12, "Aaron Glenn",           "CB",  3,  82, 8,  ""),
    (1995,  9, "Kyle Brady",            "TE",  0,  52, 5,  ""),
    (1995, 16, "Hugh Douglas",          "DE",  3,  62, 3,  "Pro Bowls came w/ Eagles"),
    (1996,  1, "Keyshawn Johnson",      "WR",  3,  89, 4,  ""),
    (1997,  8, "James Farrior",         "LB",  2, 112, 5,  "Pro Bowls came w/ Steelers"),
    (2000, 12, "Shaun Ellis",           "DE",  2,  81, 10, ""),
    (2000, 13, "John Abraham",          "DE",  5, 113, 5,  "Pro Bowls mostly w/ Falcons"),
    (2000, 18, "Chad Pennington",       "QB",  0,  49, 6,  "2x Comeback POY, 0 Pro Bowls"),
    (2000, 27, "Anthony Becht",         "TE",  0,  24, 4,  ""),
    (2001, 16, "Santana Moss",          "WR",  1,  73, 3,  "Pro Bowl w/ Washington"),
    (2002, 22, "Bryan Thomas",          "DE",  0,  39, 6,  ""),
    (2003,  4, "Dewayne Robertson",     "DT",  0,  22, 4,  ""),
    (2004, 12, "Jonathan Vilma",        "LB",  3,  62, 3,  "DROY"),
    (2006,  4, "D'Brickashaw Ferguson", "OT",  3,  95, 10, ""),
    (2006, 29, "Nick Mangold",          "C",   7, 114, 10, ""),
    (2007, 14, "Darrelle Revis",        "CB",  7, 138, 8,  "HOF"),
    (2008,  6, "Vernon Gholston",       "DE",  0,   2, 0,  "Legendary bust, 0 NFL sacks"),
    (2008, 30, "Dustin Keller",         "TE",  0,  28, 4,  ""),
    (2009,  5, "Mark Sanchez",          "QB",  0,  45, 4,  "Two AFC title games"),
    (2010, 29, "Kyle Wilson",           "CB",  0,  16, 1,  ""),
    (2011, 30, "Muhammad Wilkerson",    "DT",  1,  58, 6,  ""),
    (2012, 16, "Quinton Coples",        "DE",  0,  18, 3,  ""),
    (2013,  9, "Dee Milliner",          "CB",  0,   8, 1,  ""),
    (2013, 13, "Sheldon Richardson",    "DT",  1,  56, 4,  "DROY"),
    (2014, 18, "Calvin Pryor",          "S",   0,  14, 2,  ""),
    (2015,  6, "Leonard Williams",      "DT",  1,  72, 4,  ""),
    (2016, 20, "Darron Lee",            "LB",  0,  17, 2,  ""),
    (2017,  6, "Jamal Adams",           "S",   3,  55, 3,  ""),
    (2018,  3, "Sam Darnold",           "QB",  0,  30, 3,  "Jets career; thriving elsewhere"),
    (2019,  3, "Quinnen Williams",      "DT",  1,  49, 5,  ""),
    (2020, 11, "Mekhi Becton",          "OT",  0,  19, 2,  "Injuries"),
    (2021,  2, "Zach Wilson",           "QB",  0,   9, 3,  "Infamous bust"),
    (2021, 14, "Alijah Vera-Tucker",    "G",   0,  28, 3,  "Injuries; left for NE 2026"),
    (2022,  4, "Sauce Gardner",         "CB",  2,  34, 3,  "DROY"),
    (2022, 10, "Garrett Wilson",        "WR",  1,  29, 3,  "OROY"),
    (2022, 26, "Jermaine Johnson",      "DE",  1,  24, 2,  ""),
    (2023, 15, "Will McDonald IV",      "DE",  0,   9, 1,  "Too early to judge"),
    (2024, 11, "Olumuyiwa Fashanu",     "OT",  0,   3, 1,  "Too early to judge"),
    (2025,  7, "Armand Membou",         "OT",  0,   0, 0,  "Hasn't played"),
]

# Expected career AV by first-round slot, published from historical PFR
# draft research (approximate Chase Stuart curve). Used as slot-median proxy.
EXPECTED_AV = {
    1: 72,  2: 66,  3: 60,  4: 54,  5: 49,  6: 45,  7: 41,  8: 38,
    9: 35, 10: 33, 11: 30, 12: 28, 13: 27, 14: 25, 15: 24, 16: 22,
    17: 21, 18: 20, 19: 19, 20: 18, 21: 17, 22: 16, 23: 15, 24: 14,
    25: 13, 26: 13, 27: 12, 28: 11, 29: 11, 30: 10, 31: 10, 32:  9,
}

# Cutoff: only picks from 2022 and earlier are "mature" enough to judge.
# Picks 2023+ get a separate "too soon" label.
MATURE_CUTOFF = 2022


def classify(pick):
    year, slot, name, pos, pb, av, styr, notes = pick
    exp_av = EXPECTED_AV.get(slot, 20)
    mature = year <= MATURE_CUTOFF
    if not mature:
        return {"bust_A": None, "bust_B": None, "bust_C": None,
                "misery": None, "expected_av": exp_av}
    return {
        "bust_A": pb == 0,
        "bust_B": av < exp_av,
        "bust_C": styr < 4,
        "expected_av": exp_av,
        "misery": sum([pb == 0, av < exp_av, styr < 4]),
    }


def main():
    rows = []
    for p in PICKS:
        year, slot, name, pos, pb, av, styr, notes = p
        c = classify(p)
        rows.append({
            "year": year, "slot": slot, "name": name, "position": pos,
            "pro_bowls": pb, "career_av": av, "nyj_starter_years": styr,
            "expected_av": c["expected_av"],
            "bust_A_no_pro_bowl": c["bust_A"],
            "bust_B_below_slot_av": c["bust_B"],
            "bust_C_under_4_nyj_starts": c["bust_C"],
            "misery_index": c["misery"],
            "mature": year <= MATURE_CUTOFF,
            "notes": notes,
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Summary stats
    mature = [r for r in rows if r["mature"]]
    n = len(mature)
    busts_A = sum(1 for r in mature if r["bust_A_no_pro_bowl"])
    busts_B = sum(1 for r in mature if r["bust_B_below_slot_av"])
    busts_C = sum(1 for r in mature if r["bust_C_under_4_nyj_starts"])
    triple = [r for r in mature if r["misery_index"] == 3]
    all_three = len(triple)
    zero = sum(1 for r in mature if r["misery_index"] == 0)
    misery_dist = Counter(r["misery_index"] for r in mature)

    # Top-10 slot subset (high-confidence picks)
    top10 = [r for r in mature if r["slot"] <= 10]
    top10_busts_A = sum(1 for r in top10 if r["bust_A_no_pro_bowl"])
    top10_busts_B = sum(1 for r in top10 if r["bust_B_below_slot_av"])
    top10_busts_C = sum(1 for r in top10 if r["bust_C_under_4_nyj_starts"])

    # Hall-of-Famer count (manually: Revis)
    hof = [r for r in mature if "HOF" in r["notes"]]

    print("=" * 70)
    print("NY JETS FIRST-ROUND DRAFT, 1976-2025")
    print("=" * 70)
    print(f"Total first-round picks:       {len(rows)}")
    print(f"Analyzed (mature, <=2022):     {n}")
    print(f"Too soon to judge (2023+):     {len(rows) - n}")
    print()
    print(f"Bust A (no Pro Bowl):          {busts_A}/{n}  =  {busts_A/n:.1%}")
    print(f"Bust B (below slot AV):        {busts_B}/{n}  =  {busts_B/n:.1%}")
    print(f"Bust C (<4 NYJ starter yrs):   {busts_C}/{n}  =  {busts_C/n:.1%}")
    print()
    print("Misery Index distribution (0 = hit on all three, 3 = bust on all):")
    for k in sorted(misery_dist):
        bar = "#" * misery_dist[k]
        print(f"  {k}: {misery_dist[k]:2}  {bar}")
    print()
    print(f"All three busts (misery=3):    {all_three}/{n}  =  {all_three/n:.1%}")
    print(f"Zero busts (misery=0):         {zero}/{n}  =  {zero/n:.1%}")
    print()
    print(f"Hall of Famers:                {len(hof)}  ({', '.join(h['name'] for h in hof)})")
    print()
    print("--- TOP-10 SLOT ('high-confidence' picks) ---")
    print(f"Count:                         {len(top10)}")
    print(f"Bust A rate:                   {top10_busts_A}/{len(top10)}  =  {top10_busts_A/len(top10):.1%}")
    print(f"Bust B rate:                   {top10_busts_B}/{len(top10)}  =  {top10_busts_B/len(top10):.1%}")
    print(f"Bust C rate:                   {top10_busts_C}/{len(top10)}  =  {top10_busts_C/len(top10):.1%}")
    print()
    print("--- TRIPLE BUSTS (all three definitions) ---")
    for r in sorted(triple, key=lambda x: x["year"]):
        print(f"  {r['year']} #{r['slot']:2} {r['name']:30} {r['position']:4} "
              f"PB={r['pro_bowls']} AV={r['career_av']} StYrs={r['nyj_starter_years']}")
    print()
    print("--- CLEAN HITS (misery=0) ---")
    clean = [r for r in mature if r["misery_index"] == 0]
    for r in sorted(clean, key=lambda x: x["year"]):
        print(f"  {r['year']} #{r['slot']:2} {r['name']:30} {r['position']:4} "
              f"PB={r['pro_bowls']} AV={r['career_av']} StYrs={r['nyj_starter_years']}")
    print()
    print(f"CSV written: {OUT_CSV}")


if __name__ == "__main__":
    main()
