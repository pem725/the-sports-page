#!/usr/bin/env python3
"""Two feeds rule: rebuild the 2026 answer counts for the CFP top 12 from ESPN's drive
charts and compare them, game by game, with the CFBD counts from 5_cfb.py.

ESPN drives carry no score at the start of a drive, so the score after the last play of the
previous drive stands in for it. Same definitions as 5_cfb.py. ESPN summary feeds are cached
in data/raw/espn-cfb-summary/ (no CFBD quota is used here).
Writes data/cfb-2026-verify.json.
"""
import gzip, importlib.util, json, os, time, urllib.request
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cfb", os.path.join(HERE, "5_cfb.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
CACHE = os.path.join(HERE, "data", "raw", "espn-cfb-summary")
URL = "https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={}"


def summary(gid):
    p = os.path.join(CACHE, f"{gid}.json.gz")
    if not os.path.exists(p):
        data = urllib.request.urlopen(urllib.request.Request(URL.format(gid), headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read()
        with gzip.open(p, "wb") as f:
            f.write(data)
        time.sleep(0.3)
    return json.load(gzip.open(p, "rt"))


def clock(s):
    mm, ss = s.split(":")
    return int(mm) * 60 + int(ss)


def espn_counts(S, home_id, away_id):
    """{team_id: [chances, answered]} and final score from ESPN's drive chart."""
    drives = S["drives"]["previous"]
    hs = as_ = 0
    rows = []
    for d in drives:
        plays = d.get("plays") or []
        per = d["start"]["period"]["number"]
        rows.append(dict(team=d["team"]["id"], per=per, secs=clock((d["start"].get("clock") or (plays[0].get("clock") if plays else None) or {"displayValue": "15:00"})["displayValue"]) + (900 if per in (1, 3) else 0),
                         hs=hs, as_=as_, result=d.get("result", "")))
        if plays:
            hs, as_ = plays[-1]["homeScore"], plays[-1]["awayScore"]
        rows[-1]["he"], rows[-1]["ae"] = hs, as_
    out = defaultdict(lambda: [0, 0])
    reg = [r for r in rows if r["per"] <= 4]
    for i, d in enumerate(reg):
        if i == 0 or d["secs"] < 120:
            continue
        p = reg[i - 1]
        if (p["per"] <= 2) != (d["per"] <= 2):
            continue
        home = d["team"] == home_id
        gh, ga = d["hs"] - p["hs"], d["as_"] - p["as_"]
        them, us = (ga, gh) if home else (gh, ga)
        if them >= 6 and us == 0:
            gain = (d["he"] - d["hs"]) if home else (d["ae"] - d["as_"])
            out[d["team"]][0] += 1
            out[d["team"]][1] += int(d["result"] in ("TD", "FG") or gain >= 3)
    comp = S["header"]["competitions"][0]["competitors"]
    final = {c["team"]["id"]: int(c["score"]) for c in comp}
    return out, final


def main():
    os.makedirs(CACHE, exist_ok=True)
    games, _ = m.load(range(2026, 2027))
    ev = m.events(games)
    top = json.load(open(os.path.join(HERE, "data", "cfb-cfp-2026-11-17.json")))["ranks"][:12]
    gm = {g["id"]: g for g in json.load(gzip.open(os.path.join(HERE, "data", "raw", "cfb-games-2026-regular.json.gz"), "rt"))}
    cf = defaultdict(lambda: [0, 0])
    for e in ev:
        if e["kind"] == "answer":
            cf[(e["game"], e["team"])][0] += 1; cf[(e["game"], e["team"])][1] += int(e["scored"])
    report, n_tg, n_diff, n_score_bad = [], 0, 0, 0
    for t in top:
        name, tid = t["team"], t["espn_id"]
        tot_c, tot_e = [0, 0], [0, 0]
        for gid, G in games.items():
            if name not in (G["home"], G["away"]):
                continue
            g = gm[gid]
            S = summary(gid)
            if "drives" not in S:
                continue
            ec, final = espn_counts(S, str(g["homeId"]), str(g["awayId"]))
            c = cf[(gid, name)]; e = ec.get(str(tid), [0, 0])
            n_tg += 1
            if c != e:
                n_diff += 1
                report.append(f"{name} game {gid} vs {G['away'] if name == G['home'] else G['home']}: CFBD {c} ESPN {e}")
            if final.get(str(g["homeId"])) != G["hp"] or final.get(str(g["awayId"])) != G["ap"]:
                n_score_bad += 1
                report.append(f"final score differs, game {gid}")
            for k in (0, 1):
                tot_c[k] += c[k]; tot_e[k] += e[k]
        print(f"{name:12s} CFBD answered {tot_c[1]:2d} of {tot_c[0]:2d}   ESPN {tot_e[1]:2d} of {tot_e[0]:2d}")
        t["cfbd"], t["espn"] = tot_c, tot_e
    print(f"\n{n_tg} team-games; {n_diff} differ on chances or answers; {n_score_bad} final-score mismatches")
    for r in report:
        print("  " + r)
    json.dump(dict(top=top, team_games=n_tg, differ=n_diff, score_bad=n_score_bad, notes=report),
              open(os.path.join(HERE, "data", "cfb-2026-verify.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
