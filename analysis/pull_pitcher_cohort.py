"""
Phase-2 pull for the Half-Life series — pitchers.

Goal: every pitcher who had >= 5 qualified seasons between 1985-2025.
Pitcher "qualified" = innings pitched >= 1.0 per scheduled team game (162 IP since 1962).

We split SP vs RP per-season by games_started / games_pitched ratio:
  SP if GS/G >= 0.5
  RP otherwise

Process:
  1. Per year, query MLB Stats API for qualified pitchers that season.
  2. Accumulate unique player IDs.
  3. Filter to players with >= 5 qualified seasons.
  4. Pull each player's year-by-year career stats.
  5. Save to pitcher_career_data.csv.

Output columns: name, pid, year, mlb_yr, age, role (SP/RP), G, GS, IP, ERA, WHIP, K, BB, HR, K_per_9, BB_per_9, HR_per_9
"""

import requests, csv, sys, time
from pathlib import Path
from collections import defaultdict

HEADERS = {"User-Agent": "curl/8.0"}
SEASON_LEADERS_URL = "https://statsapi.mlb.com/api/v1/stats"
STATS_URL = "https://statsapi.mlb.com/api/v1/people/{pid}/stats?stats=yearByYear&group=pitching"
PERSON_URL = "https://statsapi.mlb.com/api/v1/people/{pid}"

START_YEAR = 1985
END_YEAR = 2025
MIN_QUALIFIED_SEASONS = 5

def to_float(s):
    try: return float(s)
    except (ValueError, TypeError): return None

def to_int(s):
    try: return int(s)
    except (ValueError, TypeError): return None

def ip_decimal(ip_str):
    """Convert MLB-style IP string (e.g. '162.2' = 162 + 2/3) to true decimal."""
    if ip_str in (None, "", "-.--"): return None
    try:
        s = str(ip_str)
        if "." in s:
            whole, frac = s.split(".")
            whole = int(whole); frac = int(frac)
            return whole + frac / 3.0
        return float(s)
    except Exception:
        return None


def get_qualified_pitchers(season):
    """Qualified pitchers that season per MLB API."""
    params = {
        "stats": "season",
        "group": "pitching",
        "season": season,
        "sportIds": 1,
        "playerPool": "qualified",
        "limit": 500,
    }
    r = requests.get(SEASON_LEADERS_URL, params=params, headers=HEADERS, timeout=20)
    if r.status_code != 200:
        print(f"  ! {season}: HTTP {r.status_code}", file=sys.stderr)
        return []
    data = r.json()
    splits = data.get("stats", [{}])[0].get("splits", []) if data.get("stats") else []
    out = []
    for s in splits:
        player = s.get("player", {})
        pid = player.get("id"); name = player.get("fullName")
        if pid: out.append((pid, name))
    return out


def fetch_person(pid):
    r = requests.get(PERSON_URL.format(pid=pid), headers=HEADERS, timeout=15)
    if r.status_code != 200: return None
    return r.json().get("people", [{}])[0]


def fetch_yearly(pid):
    r = requests.get(STATS_URL.format(pid=pid), headers=HEADERS, timeout=20)
    if r.status_code != 200: return []
    return r.json().get("stats", [{}])[0].get("splits", [])


def main():
    print(f"Step 1: scanning qualified pitchers {START_YEAR}-{END_YEAR}")
    appearances = defaultdict(list)
    for season in range(START_YEAR, END_YEAR + 1):
        qps = get_qualified_pitchers(season)
        for pid, name in qps: appearances[pid].append((season, name))
        print(f"  {season}: {len(qps)} qualified pitchers (cumulative unique={len(appearances)})")
        time.sleep(0.25)

    # Qualified pitchers are nearly all SP. Also include any pitcher with 5+ seasons of 30+ G.
    # We'll find those by pulling person info for a broader set: also include the top relief leaders
    # via the "saves" stat. For now, qualified-only gives us the SP backbone; we'll add RPs in a
    # second pass.
    print(f"\nStep 1b: also adding relief leaders (top-30 saves per year)")
    for season in range(START_YEAR, END_YEAR + 1):
        params = {"stats":"season","group":"pitching","season":season,"sportIds":1,
                  "sortStat":"saves","order":"desc","limit":30}
        r = requests.get(SEASON_LEADERS_URL, params=params, headers=HEADERS, timeout=20)
        if r.status_code != 200: continue
        for s in r.json().get("stats",[{}])[0].get("splits",[]):
            p = s.get("player",{})
            pid, name = p.get("id"), p.get("fullName")
            if pid: appearances[pid].append((season, name))
        time.sleep(0.2)
    print(f"  cumulative unique now {len(appearances)}")

    print(f"\nStep 2: filtering to players with >= {MIN_QUALIFIED_SEASONS} season appearances")
    targets = {pid: appearances[pid] for pid in appearances if len(appearances[pid]) >= MIN_QUALIFIED_SEASONS}
    print(f"  → {len(targets)} target pitchers")

    print(f"\nStep 3: pulling career stats per pitcher")
    out_rows = []; failed = []
    for i, (pid, apps) in enumerate(targets.items(), 1):
        name = apps[0][1]
        try:
            person = fetch_person(pid)
            if not person: failed.append(name); continue
            debut = person.get("mlbDebutDate", "")
            debut_year = int(debut[:4]) if debut else None
            splits = fetch_yearly(pid)
            for s in splits:
                yr = int(s.get("season", 0) or 0)
                if yr < 1900 or yr >= 2026: continue
                stat = s.get("stat", {})
                ip = ip_decimal(stat.get("inningsPitched"))
                if ip is None or ip < 10: continue
                g  = to_int(stat.get("gamesPlayed"))
                gs = to_int(stat.get("gamesStarted")) or 0
                role = "SP" if (g and gs/g >= 0.5) else "RP"
                k = to_int(stat.get("strikeOuts")) or 0
                bb = to_int(stat.get("baseOnBalls")) or 0
                hr = to_int(stat.get("homeRuns")) or 0
                er = to_int(stat.get("earnedRuns")) or 0
                era = to_float(stat.get("era"))
                whip = to_float(stat.get("whip"))
                out_rows.append({
                    "name": name, "pid": pid,
                    "year": yr,
                    "mlb_yr": yr - debut_year + 1 if debut_year else None,
                    "age": stat.get("age"),
                    "role": role,
                    "G": g, "GS": gs, "IP": round(ip, 2),
                    "ERA": era, "WHIP": whip,
                    "K": k, "BB": bb, "HR": hr,
                    "K_per_9":  round(9*k/ip, 3)  if ip else None,
                    "BB_per_9": round(9*bb/ip, 3) if ip else None,
                    "HR_per_9": round(9*hr/ip, 3) if ip else None,
                    "ER": er,
                })
            if i % 25 == 0:
                print(f"  pulled {i}/{len(targets)} careers ({len(out_rows)} rows so far)")
            time.sleep(0.2)
        except Exception as e:
            print(f"  ! {name}: {e}", file=sys.stderr); failed.append(name)

    out_path = Path(__file__).parent / "pitcher_career_data.csv"
    if out_rows:
        with open(out_path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader(); w.writerows(out_rows)
    print(f"\nDone. {len(out_rows)} rows, {len(set(r['name'] for r in out_rows))} pitchers → {out_path}")
    if failed: print(f"Failed: {len(failed)} pitchers")


if __name__ == "__main__":
    sys.exit(main() or 0)
