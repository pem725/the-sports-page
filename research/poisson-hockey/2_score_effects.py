#!/usr/bin/env python3
"""Why the counts are squeezed: a team's scoring rate depends on the score.

Regulation only. For each team-game, walk the goals in time order and add up the seconds the
team spent leading, tied and trailing, and its goals in each state. Empty-net goals are left
out (they are the trailing team's choice, counted separately). Rates are goals per 60 minutes.
"""
import csv, glob, os, collections, json
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "gene-rule", "data", "raw")
games = {}
for fn in sorted(glob.glob(os.path.join(RAW, "nhl-goals-20[12][0-9].csv"))):
    if fn.endswith("2026.csv"): continue  # complete seasons only
    for r in csv.DictReader(open(fn)):
        g = games.setdefault(r["game"], {"home": r["home"], "away": r["away"], "goals": []})
        if r["team"] and int(r["period"]) <= 3:
            g["goals"].append((int(r["t"]), r["team"], r["sit"]))

def en(team, home, sit):
    return len(sit) == 4 and ((sit[3] == "0") if team != home else (sit[0] == "0"))

secs = collections.Counter(); goals = collections.Counter(); engoals = collections.Counter()
for g in games.values():
    gl = sorted(g["goals"])
    for team in (g["home"], g["away"]):
        diff, last = 0, 0
        for t, tm, sit in gl + [(3600, None, "")]:
            st = "lead4+" if diff >= 4 else "lead3" if diff == 3 else "lead2" if diff == 2 else "lead1" if diff == 1 else "tied" if diff == 0 else "trail1" if diff == -1 else "trail2" if diff == -2 else "trail3+"
            secs[st] += t - last; last = t
            if tm is None: break
            if tm == team:
                if en(tm, g["home"], sit): engoals[st] += 1
                else: goals[st] += 1
                diff += 1
            else:
                diff -= 1
out = {}
for st in ("trail3+", "trail2", "trail1", "tied", "lead1", "lead2", "lead3", "lead4+"):
    r = goals[st] / secs[st] * 3600
    out[st] = {"hours": secs[st]/3600, "goals": goals[st], "per60": r, "en_goals": engoals[st]}
    print(f"{st:8} {secs[st]/3600:8.0f} h  {goals[st]:6} goals  {r:.2f}/60   EN {engoals[st]}")
json.dump(out, open(os.path.join(HERE, "score_effects.json"), "w"), indent=1)
