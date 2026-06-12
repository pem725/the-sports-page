"""
Pitcher half-life analysis. Service-year buckets just like the hitter version.

Role assignment is per-season (SP if GS/G >= 0.5, else RP). For the survival
cohort we use a player's MODAL role across his career (a Smoltz-type is
counted toward the role he played in years 1-3 — early career anchor).

Indicators:
  ERA, WHIP, K_per_9, BB_per_9, HR_per_9, IP_per_season
Cohorts (debut role):
  SP — debut cohort = pitchers whose role is SP in years 1-3 with IP >= 80
       (a "regular starter" bar; full-qualified is 162 but plenty of valuable
       starters fall short. 80 IP = ~4 starts per month over 5 months)
  RP — debut cohort = pitchers whose role is RP in years 1-3 with IP >= 40
       (a "regular reliever" bar)

Survival = still putting up an at-or-above debut-role IP threshold in any
role at later bucket (a starter who converts to closer still counts as alive).
"""
import csv, json, statistics
from pathlib import Path
from collections import defaultdict

ANALYSIS_DIR = Path(__file__).parent
CSV_PATH = ANALYSIS_DIR / "pitcher_career_data.csv"

BUCKETS = [(1, 3), (4, 6), (7, 9), (10, 12), (13, 15), (16, 99)]
BUCKET_LABELS = ["1-3", "4-6", "7-9", "10-12", "13-15", "16+"]

ROLES = ["SP", "RP"]
SP_IP_FLOOR = 80     # season-floor for "regular starter"
RP_IP_FLOOR = 40     # season-floor for "regular reliever"

def bucket_label(yr):
    if yr is None or yr < 1: return None
    for (lo, hi), lab in zip(BUCKETS, BUCKET_LABELS):
        if lo <= yr <= hi: return lab
    return None

def to_int(x):
    try: return int(x)
    except (TypeError, ValueError): return None

def to_float(x):
    try: return float(x) if x not in ("", None) else None
    except (TypeError, ValueError): return None

def percentile(s, q):
    if not s: return None
    if len(s) == 1: return s[0]
    idx = (len(s)-1)*q
    lo = int(idx); hi = min(lo+1, len(s)-1)
    frac = idx - lo
    return s[lo]*(1-frac) + s[hi]*frac

def main():
    rows = list(csv.DictReader(open(CSV_PATH)))
    print(f"Loaded {len(rows)} pitcher-seasons")

    # Group rows by pitcher
    by_pitcher = defaultdict(list)
    for r in rows:
        yr = to_int(r["mlb_yr"])
        ip = to_float(r["IP"])
        if not yr or ip is None: continue
        b = bucket_label(yr)
        if not b: continue
        by_pitcher[r["name"]].append({
            "year": to_int(r["year"]),
            "mlb_yr": yr,
            "bucket": b,
            "role": r["role"],
            "IP":  ip,
            "G":   to_int(r["G"]),
            "GS":  to_int(r["GS"]),
            "ERA": to_float(r["ERA"]),
            "WHIP": to_float(r["WHIP"]),
            "K_per_9":  to_float(r["K_per_9"]),
            "BB_per_9": to_float(r["BB_per_9"]),
            "HR_per_9": to_float(r["HR_per_9"]),
        })

    # Determine each pitcher's "debut role" = role in years 1-3 (modal by IP)
    pitcher_meta = {}
    for name, seasons in by_pitcher.items():
        early = [s for s in seasons if s["bucket"] == "1-3"]
        if not early: continue
        ip_by_role = defaultdict(float)
        for s in early: ip_by_role[s["role"]] += s["IP"]
        debut_role = max(ip_by_role, key=ip_by_role.get) if ip_by_role else None
        # Did they meet the bar?
        floor = SP_IP_FLOOR if debut_role == "SP" else RP_IP_FLOOR
        # passed = any season in 1-3 with >= floor IP in debut role
        passed = any(s["bucket"]=="1-3" and s["role"]==debut_role and s["IP"]>=floor for s in early)
        pitcher_meta[name] = {"debut_role": debut_role, "in_cohort": passed}

    # Build role × bucket aggregates (pooling by season-role, not pitcher-role)
    # This shows: of all SP-role seasons in bucket X, what's the median ERA?
    role_bucket = defaultdict(lambda: defaultdict(list))
    for name, seasons in by_pitcher.items():
        for s in seasons:
            role = s["role"]; b = s["bucket"]
            for k in ("ERA","WHIP","K_per_9","BB_per_9","HR_per_9","IP"):
                if s[k] is not None: role_bucket[(role,b)][k].append(s[k])

    role_bucket_summary = {}
    for (role, b), inds in role_bucket.items():
        summary = {"n_pitcher_seasons": len(inds.get("ERA", []))}
        for ind, vals in inds.items():
            sv = sorted([v for v in vals if v is not None])
            if not sv: continue
            summary[ind] = {
                "median": round(percentile(sv, 0.5), 4),
                "p25":    round(percentile(sv, 0.25), 4),
                "p75":    round(percentile(sv, 0.75), 4),
                "mean":   round(statistics.mean(sv), 4),
                "n":      len(sv),
            }
        role_bucket_summary[f"{role}|{b}"] = summary

    # Survival curve per debut-role cohort.
    # "Alive" at bucket B = any season in that bucket with IP >= role floor (using debut role's floor).
    cohort = defaultdict(set)
    survivors = defaultdict(lambda: defaultdict(set))
    for name, meta in pitcher_meta.items():
        if not meta["in_cohort"]: continue
        role = meta["debut_role"]
        floor = SP_IP_FLOOR if role == "SP" else RP_IP_FLOOR
        cohort[role].add(name)
        for b in BUCKET_LABELS:
            if any(s["bucket"]==b and s["IP"]>=floor for s in by_pitcher[name]):
                survivors[role][b].add(name)

    survival_curve = {}
    for role in ROLES:
        c = cohort[role]
        if not c: continue
        survival_curve[role] = {
            "cohort_size": len(c),
            "survival_rate": {b: round(len(survivors[role].get(b,set()))/len(c), 4) for b in BUCKET_LABELS},
        }

    # Half-life
    half_life = {}
    for role in ROLES:
        sc = survival_curve.get(role)
        survival_half = None
        if sc:
            for b in BUCKET_LABELS[1:]:
                if sc["survival_rate"].get(b, 0) < 0.5:
                    survival_half = b; break
        b0 = role_bucket_summary.get(f"{role}|1-3", {})
        baseline_era = (b0.get("ERA") or {}).get("median")
        # "production half-life" for pitchers: first bucket where median ERA rises >= 7.5% above baseline
        prod_half = None
        if baseline_era is not None:
            thresh = baseline_era * 1.075
            for b in BUCKET_LABELS[1:]:
                s = role_bucket_summary.get(f"{role}|{b}", {})
                med = (s.get("ERA") or {}).get("median")
                if med is not None and med >= thresh:
                    prod_half = b; break
        half_life[role] = {
            "cohort_size": sc["cohort_size"] if sc else 0,
            "baseline_era": baseline_era,
            "survival_half_life": survival_half,
            "production_half_life": prod_half,
        }

    # Per-pitcher rollup for the sortable table
    pitcher_summary = []
    for name, seasons in by_pitcher.items():
        if name not in pitcher_meta: continue
        meta = pitcher_meta[name]
        career_ip = sum(s["IP"] for s in seasons)
        if career_ip < 200: continue  # exclude very short careers
        career_g  = sum(s["G"]  for s in seasons if s["G"])
        career_yrs = max(s["mlb_yr"] for s in seasons)
        # IP-weighted indicators
        def w(field, weight="IP"):
            num = sum((s[field] or 0)*(s[weight] or 0) for s in seasons if s.get(field) is not None)
            den = sum((s[weight] or 0) for s in seasons if s.get(field) is not None)
            return round(num/den, 4) if den else None
        bucket_era = {}
        for b in BUCKET_LABELS:
            bs = [s for s in seasons if s["bucket"]==b and s["ERA"] is not None]
            if not bs: continue
            num = sum(s["ERA"]*s["IP"] for s in bs)
            den = sum(s["IP"] for s in bs)
            if den: bucket_era[b] = round(num/den, 3)
        pitcher_summary.append({
            "name": name,
            "role": meta["debut_role"],
            "career_yrs": career_yrs,
            "career_ip": round(career_ip, 1),
            "career_g":  career_g,
            "career_era": w("ERA"),
            "career_whip": w("WHIP"),
            "career_k9": w("K_per_9"),
            "career_bb9": w("BB_per_9"),
            "career_hr9": w("HR_per_9"),
            "bucket_era": bucket_era,
        })
    pitcher_summary.sort(key=lambda p: p["career_ip"], reverse=True)

    out1 = ANALYSIS_DIR / "pitcher_half_life.json"
    out2 = ANALYSIS_DIR / "pitcher_career_buckets.json"
    json.dump({
        "buckets": BUCKET_LABELS,
        "roles": ROLES,
        "role_bucket_summary": role_bucket_summary,
        "survival_curve": survival_curve,
        "half_life": half_life,
    }, open(out1, "w"), indent=2)
    json.dump({"buckets": BUCKET_LABELS, "pitchers": pitcher_summary}, open(out2, "w"), indent=2)

    print(f"\nWrote {out1.name} and {out2.name}")
    print(f"  pitchers in table: {len(pitcher_summary)}")
    print(f"\nHalf-life by role:")
    print(f"  {'ROLE':<5} {'cohort':<7} {'baseERA':<8} {'surv_half':<10} {'prod_half':<10}")
    for role, hl in half_life.items():
        bera = f"{hl['baseline_era']:.2f}" if hl['baseline_era'] else "—"
        print(f"  {role:<5} {hl['cohort_size']:<7} {bera:<8} {str(hl['survival_half_life'] or '—'):<10} {str(hl['production_half_life'] or '—'):<10}")
    print(f"\nSurvival curve:")
    print(f"  {'ROLE':<5} {'1-3':<6} {'4-6':<6} {'7-9':<6} {'10-12':<7} {'13-15':<7} {'16+':<6}")
    for role in ROLES:
        sc = survival_curve.get(role)
        if not sc: continue
        sr = sc["survival_rate"]
        print(f"  {role:<5} {sr['1-3']:.0%}   {sr['4-6']:.0%}   {sr['7-9']:.0%}   {sr['10-12']:.0%}    {sr['13-15']:.0%}    {sr['16+']:.0%}")
    print(f"\nERA median across buckets (by per-season role):")
    print(f"  {'ROLE':<5}", *[f'{b:>9}' for b in BUCKET_LABELS])
    for role in ROLES:
        row = [role]
        for b in BUCKET_LABELS:
            cell = role_bucket_summary.get(f"{role}|{b}", {})
            era = (cell.get("ERA") or {}).get("median")
            n = (cell.get("ERA") or {}).get("n", 0)
            row.append(f"{era:.2f}(n={n})" if era else "  —")
        print(f"  {row[0]:<5}", *[f'{c:>9}' for c in row[1:]])


if __name__ == "__main__":
    main()
