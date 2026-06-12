"""
Full-cohort analysis. Uses all_hitters_seasons.csv and all_pitchers_seasons.csv
which include flameouts (anyone with >=1 PA / >=0.1 IP), not just qualifiers.

Outputs:
  full_cohort_data.json  — for scatter view and survival curves
                            { players_hit: [...], players_pit: [...],
                              survival_hit: {pos: {bar: {svc_yr: rate}}},
                              survival_pit: {role: {bar: {svc_yr: rate}}} }

Key change from prior analysis:
  - Cohort = EVERY player who debuted in/after 1985 (debut_year >= 1985).
    This excludes mid-career-only data for players who debuted earlier
    (their service-year clock is wrong if we only see them from 1985 on).
  - Survival measured at three bars:
      "active"   = >=1 PA / >=0.1 IP (still in the league at all)
      "regular"  = >=300 PA / (>=80 IP SP or >=40 IP RP)
      "qualifier"= >=502 PA / >=162 IP
  - Per-player record carries [svc_yr, year, PA, OPS, AVG, OBP, SLG, HR_per_PA]
    (and the pitcher equivalent) — light enough to ship as JSON for scatter.
"""

import csv, json, sys
from collections import defaultdict
from pathlib import Path

ANALYSIS = Path(__file__).parent

def to_int(x):
    try: return int(x)
    except: return None

def to_float(x):
    try: return float(x) if x not in ("", None) else None
    except: return None

# ---------- Hitters ----------
def load_hitters():
    rows = list(csv.DictReader(open(ANALYSIS / "all_hitters_seasons.csv")))
    # Group by player
    by_pid = defaultdict(list)
    for r in rows:
        by_pid[r["pid"]].append(r)

    players = []
    for pid, seasons in by_pid.items():
        seasons.sort(key=lambda s: int(s["year"]))
        debut_year = int(seasons[0]["year"])
        if debut_year < 1985: continue  # truncated career — skip
        # Primary position: modal by PA across career (require some PA)
        pos_pa = defaultdict(int)
        for s in seasons:
            pos_pa[s["position"]] += int(s["PA"] or 0)
        primary_pos = max(pos_pa, key=pos_pa.get) if pos_pa else None
        debut_pa = int(seasons[0]["PA"] or 0)
        # Debut-PA tier: a key dimension for the user
        if debut_pa < 100:   debut_tier = "cup"          # cup of coffee
        elif debut_pa < 300: debut_tier = "partial"      # partial year, sub-regular
        elif debut_pa < 502: debut_tier = "regular"
        else:                debut_tier = "qualifier"
        # Per-season array (compact)
        s_arr = []
        for s in seasons:
            yr = int(s["year"]); svc = yr - debut_year + 1
            pa = int(s["PA"] or 0)
            ops = to_float(s["OPS"])
            avg = to_float(s["AVG"])
            obp = to_float(s["OBP"])
            slg = to_float(s["SLG"])
            iso = (slg - avg) if (slg is not None and avg is not None) else None
            hr = int(s["HR"] or 0)
            hr_pa = round(hr/pa, 4) if pa else None
            so = int(s["SO"] or 0)
            bb = int(s["BB"] or 0)
            s_arr.append({
                "svc": svc, "yr": yr, "PA": pa, "G": int(s["G"] or 0),
                "OPS": ops, "AVG": avg, "OBP": obp, "SLG": slg, "ISO": iso,
                "HR_PA": hr_pa,
                "BB_PA": round(bb/pa, 4) if pa else None,
                "K_PA":  round(so/pa, 4) if pa else None,
            })
        players.append({
            "name": seasons[0]["name"],
            "pid": int(pid),
            "pos": primary_pos,
            "debut": debut_year,
            "tier": debut_tier,
            "career_pa": sum(s["PA"] for s in s_arr),
            "career_yrs": s_arr[-1]["svc"],
            "seasons": s_arr,
        })
    return players


def load_pitchers():
    rows = list(csv.DictReader(open(ANALYSIS / "all_pitchers_seasons.csv")))
    by_pid = defaultdict(list)
    for r in rows:
        by_pid[r["pid"]].append(r)
    players = []
    for pid, seasons in by_pid.items():
        seasons.sort(key=lambda s: int(s["year"]))
        debut_year = int(seasons[0]["year"])
        if debut_year < 1985: continue
        # Primary role: weight by IP
        role_ip = defaultdict(float)
        for s in seasons: role_ip[s["role"]] += float(s["IP"] or 0)
        primary_role = max(role_ip, key=role_ip.get) if role_ip else None
        debut_ip = float(seasons[0]["IP"] or 0)
        # Tier: rough role-aware
        if debut_ip < 30:    debut_tier = "cup"
        elif debut_ip < 80:  debut_tier = "partial"
        elif debut_ip < 162: debut_tier = "regular"
        else:                debut_tier = "qualifier"
        s_arr = []
        for s in seasons:
            yr = int(s["year"]); svc = yr - debut_year + 1
            ip = float(s["IP"] or 0)
            s_arr.append({
                "svc": svc, "yr": yr, "role": s["role"], "IP": round(ip, 1),
                "G": int(s["G"] or 0), "GS": int(s["GS"] or 0),
                "ERA":  to_float(s["ERA"]),
                "WHIP": to_float(s["WHIP"]),
                "K9":   to_float(s["K_per_9"]),
                "BB9":  to_float(s["BB_per_9"]),
                "HR9":  to_float(s["HR_per_9"]),
            })
        players.append({
            "name": seasons[0]["name"],
            "pid": int(pid),
            "role": primary_role,
            "debut": debut_year,
            "tier": debut_tier,
            "career_ip": round(sum(s["IP"] for s in s_arr), 1),
            "career_yrs": s_arr[-1]["svc"],
            "seasons": s_arr,
        })
    return players


# ---------- Survival ----------
HIT_BARS = {"active": 1, "regular": 300, "qualifier": 502}
PIT_BARS_SP = {"active": 0.1, "regular": 80, "qualifier": 162}
PIT_BARS_RP = {"active": 0.1, "regular": 40, "qualifier": 80}  # 80 IP RP is elite long-relief
POS_KEEP = {"C","1B","2B","3B","SS","LF","CF","RF","DH"}
ROLE_KEEP = {"SP","RP"}

def survival_curves_hit(players, max_svc=20):
    # For each position × debut tier × survival bar, % of cohort alive at each svc year
    cohorts = defaultdict(set)        # (pos, tier) -> {pid}
    alive   = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    # alive[(pos,tier)][bar][svc] = {pid}
    for p in players:
        if p["pos"] not in POS_KEEP: continue
        key = (p["pos"], p["tier"])
        cohorts[key].add(p["pid"])
        for bar_name, bar_pa in HIT_BARS.items():
            for s in p["seasons"]:
                if s["svc"] > max_svc: continue
                if s["PA"] >= bar_pa: alive[key][bar_name][s["svc"]].add(p["pid"])
    out = {}
    for key, pids in cohorts.items():
        n = len(pids)
        if n < 5: continue
        pos, tier = key
        out[f"{pos}|{tier}"] = {
            "n": n,
            "bars": {bar: {svc: round(len(alive[key][bar][svc])/n, 4) for svc in range(1, max_svc+1)}
                     for bar in HIT_BARS}
        }
    return out


def survival_curves_pit(players, max_svc=20):
    cohorts = defaultdict(set)
    alive = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    for p in players:
        if p["role"] not in ROLE_KEEP: continue
        bars = PIT_BARS_SP if p["role"] == "SP" else PIT_BARS_RP
        key = (p["role"], p["tier"])
        cohorts[key].add(p["pid"])
        for bar_name, bar_ip in bars.items():
            for s in p["seasons"]:
                if s["svc"] > max_svc: continue
                if s["IP"] >= bar_ip: alive[key][bar_name][s["svc"]].add(p["pid"])
    out = {}
    for key, pids in cohorts.items():
        n = len(pids)
        if n < 5: continue
        role, tier = key
        bars = PIT_BARS_SP if role == "SP" else PIT_BARS_RP
        out[f"{role}|{tier}"] = {
            "n": n,
            "bars": {bar: {svc: round(len(alive[key][bar][svc])/n, 4) for svc in range(1, max_svc+1)}
                     for bar in bars}
        }
    return out


def main():
    print("Loading hitters …")
    hit = load_hitters()
    print(f"  → {len(hit)} hitters (debut >= 1985)")

    print("Loading pitchers …")
    pit = load_pitchers()
    print(f"  → {len(pit)} pitchers (debut >= 1985)")

    print("Computing survival curves …")
    surv_hit = survival_curves_hit(hit)
    surv_pit = survival_curves_pit(pit)
    print(f"  hit cohorts: {len(surv_hit)} cells; pit cohorts: {len(surv_pit)} cells")

    # Quick population check: survival at svc=1 by debut tier (should be 100% by construction at active bar)
    print("\nSpot-check — % active at svc year 5, by position × debut tier:")
    for k, v in sorted(surv_hit.items())[:12]:
        rate = v["bars"]["active"].get(5, 0)
        print(f"  {k:<14} n={v['n']:<4} active@5={rate:.0%}")

    print("\nSpot-check — % qualifier at svc year 5, by position × debut tier:")
    for k, v in sorted(surv_hit.items())[:12]:
        rate = v["bars"]["qualifier"].get(5, 0)
        print(f"  {k:<14} n={v['n']:<4} qual@5={rate:.0%}")

    # Save
    out = {
        "players_hit": hit,
        "players_pit": pit,
        "survival_hit": surv_hit,
        "survival_pit": surv_pit,
    }
    json.dump(out, open(ANALYSIS / "full_cohort_data.json", "w"), separators=(",",":"))
    size = (ANALYSIS / "full_cohort_data.json").stat().st_size
    print(f"\nWrote full_cohort_data.json ({size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
