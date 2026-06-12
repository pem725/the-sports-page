"""
Pull 2026 season hitting stats per team to compute within-team OPS spread.

For each of the 30 MLB teams, fetch every player who batted in 2026,
filter to those with >= 50 PA (in-season threshold), compute:
  mean OPS (PA-weighted), std dev of OPS, top OPS, median OPS,
  gap between top hitter and roster median.

Output: team_clustering_2026.csv plus a sorted summary print.
"""
import requests, csv, sys, time
from pathlib import Path
import statistics
from collections import defaultdict

HEADERS = {"User-Agent": "curl/8.0"}
TEAMS_URL = "https://statsapi.mlb.com/api/v1/teams"
STATS_URL = "https://statsapi.mlb.com/api/v1/stats"

YEAR = 2026
MIN_PA = 50

def to_float(x):
    try: return float(x) if x not in (None, "", "-.--") else None
    except: return None

def to_int(x):
    try: return int(x)
    except: return None

def fetch_teams(year):
    r = requests.get(TEAMS_URL, params={"season": year, "sportId": 1}, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return [(t["id"], t["name"], t.get("abbreviation", "")) for t in r.json().get("teams", [])
            if t.get("active", True) and t.get("sport", {}).get("id") == 1]

def fetch_team_hitters(team_id, year):
    """Return list of {name, PA, OPS, ...} for every batter on this team in {year}."""
    params = {"stats":"season","group":"hitting","season":year,"sportIds":1,
              "teamId":team_id,"playerPool":"all","limit":200}
    r = requests.get(STATS_URL, params=params, headers=HEADERS, timeout=20)
    if r.status_code != 200: return []
    splits = r.json().get("stats", [{}])[0].get("splits", [])
    out = []
    for s in splits:
        p = s.get("player", {}); st = s.get("stat", {})
        pa = to_int(st.get("plateAppearances")) or 0
        if pa < 1: continue
        ops = to_float(st.get("ops"))
        if ops is None: continue
        out.append({
            "name": p.get("fullName"),
            "pid": p.get("id"),
            "position": (s.get("position") or {}).get("abbreviation",""),
            "PA": pa,
            "OPS": ops,
            "AVG": to_float(st.get("avg")),
            "OBP": to_float(st.get("obp")),
            "SLG": to_float(st.get("slg")),
            "HR": to_int(st.get("homeRuns")),
        })
    return out

def pa_weighted_mean(rows, field):
    num = sum(r[field]*r["PA"] for r in rows if r[field] is not None)
    den = sum(r["PA"] for r in rows if r[field] is not None)
    return num/den if den else None

def pa_weighted_std(rows, field):
    mu = pa_weighted_mean(rows, field)
    if mu is None: return None
    num = sum(r["PA"]*(r[field]-mu)**2 for r in rows if r[field] is not None)
    den = sum(r["PA"] for r in rows if r[field] is not None)
    return (num/den)**0.5 if den else None

def main():
    print(f"Fetching {YEAR} MLB teams …")
    teams = fetch_teams(YEAR)
    teams = [t for t in teams if t[2]]  # filter to teams with abbreviations
    print(f"  → {len(teams)} teams")

    all_player_rows = []
    summary = []
    for tid, name, abbr in teams:
        hitters = fetch_team_hitters(tid, YEAR)
        if not hitters:
            print(f"  ! {name}: no data"); continue
        # Use the regulars-ish bar
        regs = [h for h in hitters if h["PA"] >= MIN_PA]
        if len(regs) < 5:
            print(f"  ! {name}: only {len(regs)} hitters >= {MIN_PA} PA (skipping)"); continue
        regs.sort(key=lambda h: h["OPS"], reverse=True)
        ops_vals = [h["OPS"] for h in regs]
        ops_pas = [h["PA"] for h in regs]
        mean_ops = pa_weighted_mean(regs, "OPS")
        std_ops = pa_weighted_std(regs, "OPS")
        median_ops = statistics.median(ops_vals)
        top_ops = ops_vals[0]
        top_name = regs[0]["name"]
        second_ops = ops_vals[1] if len(ops_vals) > 1 else None
        top_minus_median = top_ops - median_ops
        top_minus_second = (top_ops - second_ops) if second_ops is not None else None
        summary.append({
            "team": name, "abbr": abbr,
            "n_hitters": len(regs),
            "mean_ops_paw":  round(mean_ops, 4),
            "std_ops_paw":   round(std_ops, 4),
            "median_ops":    round(median_ops, 4),
            "top_ops":       round(top_ops, 4),
            "top_name":      top_name,
            "top_minus_median": round(top_minus_median, 4),
            "top_minus_second": round(top_minus_second, 4) if top_minus_second else None,
        })
        for h in regs: all_player_rows.append({**{"team": name, "abbr": abbr}, **h})
        time.sleep(0.2)

    ANALYSIS = Path(__file__).parent
    with open(ANALYSIS / "team_clustering_2026.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader(); w.writerows(summary)
    with open(ANALYSIS / "team_clustering_2026_players.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(all_player_rows[0].keys()))
        w.writeheader(); w.writerows(all_player_rows)

    # Print key rankings
    print(f"\n{YEAR} — TOP-MINUS-MEDIAN OPS GAP (how alone is the star?)")
    print(f"  {'team':<22} {'top':<6} {'med':<6} {'gap':<6} {'star':<25}")
    for s in sorted(summary, key=lambda x: x["top_minus_median"], reverse=True)[:12]:
        print(f"  {s['team']:<22} {s['top_ops']:.3f} {s['median_ops']:.3f} {s['top_minus_median']:+.3f} {s['top_name']:<25}")

    print(f"\n{YEAR} — WITHIN-TEAM OPS STD DEV (most spread to most clustered)")
    print(f"  {'team':<22} {'mean':<6} {'std':<6} {'n':<4} {'profile':<25}")
    for s in sorted(summary, key=lambda x: x["std_ops_paw"], reverse=True):
        mean_q = "low" if s["mean_ops_paw"] < 0.71 else ("mid" if s["mean_ops_paw"] < 0.76 else "hi")
        std_q  = "tight" if s["std_ops_paw"] < 0.08 else ("mid" if s["std_ops_paw"] < 0.12 else "spread")
        profile = f"{std_q}/{mean_q}"
        print(f"  {s['team']:<22} {s['mean_ops_paw']:.3f} {s['std_ops_paw']:.3f} {s['n_hitters']:<4} {profile:<25}")

    # Mets specifically
    mets = next((s for s in summary if "Mets" in s["team"]), None)
    if mets:
        print(f"\n🔎 NEW YORK METS DEEP READ:")
        for k, v in mets.items():
            print(f"    {k}: {v}")
        mets_players = [r for r in all_player_rows if "Mets" in r["team"]]
        mets_players.sort(key=lambda r: r["OPS"], reverse=True)
        print(f"\n  Top 12 by OPS:")
        for h in mets_players[:12]:
            print(f"    {h['name']:<25} {h['position']:<3} PA={h['PA']:<4} OPS={h['OPS']:.3f}")


if __name__ == "__main__":
    main()
