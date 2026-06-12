"""
Consumes broader_career_data.csv and produces:
  1. half_life_by_position.json — per-(position × service-year bucket) distribution
     of key indicators: OPS, OBP, ISO, HR_per_PA, BB_per_PA, K_per_PA, G.
  2. player_career_buckets.json — per-player career rolled into the same buckets.

The metric (per user 2026-06-11):
  Half-life by position by MLB years of service, measured from career start.
  Buckets: 1-3, 4-6, 7-9, 10-12, 13-15, 16+.
  "Half-life" reported as: first bucket where median OPS at that position
  drops below the position's career-start (yrs 1-3) median.

Positions are simplified to: C, 1B, 2B, 3B, SS, LF, CF, RF, OF (lumped), DH.
Primary position from MLB API. Players who changed positions stay under their
modal-by-PA primary listing.
"""

import csv
import json
import statistics
from pathlib import Path
from collections import defaultdict

ANALYSIS_DIR = Path(__file__).parent
CSV_PATH = ANALYSIS_DIR / "broader_career_data.csv"

BUCKETS = [(1, 3), (4, 6), (7, 9), (10, 12), (13, 15), (16, 99)]
BUCKET_LABELS = ["1-3", "4-6", "7-9", "10-12", "13-15", "16+"]

POS_KEEP = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "OF", "DH"}


def bucket_label(mlb_yr):
    if mlb_yr is None or mlb_yr < 1: return None
    for (lo, hi), lab in zip(BUCKETS, BUCKET_LABELS):
        if lo <= mlb_yr <= hi: return lab
    return None


def safe_div(a, b):
    try: return a / b if b else None
    except (TypeError, ZeroDivisionError): return None


def to_int(x):
    try: return int(x)
    except (TypeError, ValueError): return None


def to_float(x):
    try: return float(x) if x not in ("", None) else None
    except (TypeError, ValueError): return None


def percentile(sorted_vals, q):
    if not sorted_vals: return None
    if len(sorted_vals) == 1: return sorted_vals[0]
    idx = (len(sorted_vals) - 1) * q
    lo = int(idx); hi = min(lo + 1, len(sorted_vals) - 1)
    frac = idx - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def main():
    rows = list(csv.DictReader(open(CSV_PATH)))
    print(f"Loaded {len(rows)} player-seasons")

    # Build (position, bucket) → list of indicator values per player-season
    # AND per-player career: name → list of (bucket, indicators)
    pos_bucket = defaultdict(lambda: defaultdict(list))  # (pos, bucket) → indicator → values
    player_seasons = defaultdict(list)                    # name → rows with bucket

    for r in rows:
        pos = r.get("primary_position")
        if pos not in POS_KEEP: continue
        mlb_yr = to_int(r.get("mlb_yr"))
        b = bucket_label(mlb_yr)
        if not b: continue
        pa = to_int(r.get("PA")) or 0
        if pa < 50: continue  # keep low-PA seasons so we can measure survival, not just production
        ops = to_float(r.get("OPS"))
        obp = to_float(r.get("OBP"))
        slg = to_float(r.get("SLG"))
        avg = to_float(r.get("AVG"))
        hr  = to_int(r.get("HR")) or 0
        bb  = to_int(r.get("BB")) or 0
        so  = to_int(r.get("SO")) or 0
        g   = to_int(r.get("G")) or 0

        iso = (slg - avg) if (slg is not None and avg is not None) else None
        hr_pa = safe_div(hr, pa)
        bb_pa = safe_div(bb, pa)
        k_pa  = safe_div(so, pa)

        for k, v in (("OPS", ops), ("OBP", obp), ("ISO", iso),
                     ("HR_per_PA", hr_pa), ("BB_per_PA", bb_pa),
                     ("K_per_PA", k_pa), ("G", g), ("PA", pa)):
            if v is not None: pos_bucket[(pos, b)][k].append(v)

        player_seasons[r["name"]].append({
            "pos": pos, "bucket": b, "year": to_int(r["year"]), "mlb_yr": mlb_yr,
            "OPS": ops, "OBP": obp, "ISO": iso,
            "HR_per_PA": hr_pa, "BB_per_PA": bb_pa, "K_per_PA": k_pa,
            "G": g, "PA": pa,
        })

    # Build position × bucket aggregates
    pos_bucket_summary = {}
    for (pos, b), inds in pos_bucket.items():
        summary = {"n_player_seasons": len(inds.get("OPS", []))}
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
        pos_bucket_summary[f"{pos}|{b}"] = summary

    # Survival curve: of each position's debut cohort (yrs 1-3 regulars), what
    # fraction is still putting up 300+ PA at each later bucket?
    # "Debut cohort" = unique players with at least one 300+ PA season in yrs 1-3 at this primary position.
    # Survivors at bucket B = unique players from the cohort with at least one 300+ PA season in bucket B.
    debut_cohort = defaultdict(set)
    survivors = defaultdict(lambda: defaultdict(set))
    for name, seasons in player_seasons.items():
        # primary position by PA-weight
        pos_pa = defaultdict(int)
        for s in seasons: pos_pa[s["pos"]] += s["PA"]
        if not pos_pa: continue
        primary = max(pos_pa, key=pos_pa.get)
        # add to debut cohort if regular in yrs 1-3 at primary position
        early = [s for s in seasons if s["bucket"] == "1-3" and s["pos"] == primary and s["PA"] >= 300]
        if not early: continue
        debut_cohort[primary].add(name)
        for b in BUCKET_LABELS:
            if any(s["bucket"] == b and s["PA"] >= 300 for s in seasons):
                survivors[primary][b].add(name)

    survival_curve = {}
    for pos in POS_KEEP:
        cohort = debut_cohort.get(pos, set())
        if not cohort: continue
        survival_curve[pos] = {
            "cohort_size": len(cohort),
            "survival_rate": {
                b: round(len(survivors[pos].get(b, set())) / len(cohort), 4)
                for b in BUCKET_LABELS
            }
        }

    # Half-life: first service-year bucket where < 50% of the debut cohort is
    # still putting up 300+ PA. This is the actuarial-style "half-life."
    # Also compute: first bucket where median OPS (among survivors) drops
    # ≥7.5% below the yrs-1-3 baseline — a "production half-life" complement.
    half_life = {}
    for pos in POS_KEEP:
        sc = survival_curve.get(pos)
        survival_half = None
        if sc:
            for b in BUCKET_LABELS[1:]:
                if sc["survival_rate"].get(b, 0) < 0.5:
                    survival_half = b
                    break

        b0 = pos_bucket_summary.get(f"{pos}|1-3", {})
        baseline = b0.get("OPS", {}).get("median")
        production_half = None
        if baseline is not None:
            thresh = baseline * 0.925
            for b in BUCKET_LABELS[1:]:
                s = pos_bucket_summary.get(f"{pos}|{b}", {})
                med = s.get("OPS", {}).get("median")
                if med is not None and med <= thresh:
                    production_half = b
                    break

        half_life[pos] = {
            "cohort_size": sc["cohort_size"] if sc else 0,
            "baseline_ops": baseline,
            "survival_half_life": survival_half,
            "production_half_life": production_half,
            "decline_threshold_ops": round(baseline * 0.925, 4) if baseline else None,
        }

    # Per-player career bucket roll-up (sortable table fodder)
    player_summary = []
    for name, seasons in player_seasons.items():
        # primary position = modal pos in player_seasons
        pos_counts = defaultdict(int)
        for s in seasons: pos_counts[s["pos"]] += s["PA"]
        primary_pos = max(pos_counts, key=pos_counts.get) if pos_counts else None
        if not primary_pos: continue

        career_pa = sum(s["PA"] for s in seasons)
        career_g  = sum(s["G"]  for s in seasons)
        career_yrs = max(s["mlb_yr"] for s in seasons if s["mlb_yr"] is not None) or 0

        # PA-weighted indicators for whole career
        def w_avg(field):
            num = sum((s[field] or 0) * s["PA"] for s in seasons if s.get(field) is not None)
            den = sum(s["PA"] for s in seasons if s.get(field) is not None)
            return round(num/den, 4) if den else None

        # Bucket-level OPS (PA-weighted)
        bucket_ops = {}
        for b in BUCKET_LABELS:
            bs = [s for s in seasons if s["bucket"] == b]
            if not bs: continue
            num = sum((s["OPS"] or 0) * s["PA"] for s in bs if s["OPS"] is not None)
            den = sum(s["PA"] for s in bs if s["OPS"] is not None)
            if den: bucket_ops[b] = round(num/den, 4)

        player_summary.append({
            "name": name,
            "pos": primary_pos,
            "career_yrs": career_yrs,
            "career_pa": career_pa,
            "career_g":  career_g,
            "career_ops": w_avg("OPS"),
            "career_obp": w_avg("OBP"),
            "career_iso": w_avg("ISO"),
            "career_hr_pa": w_avg("HR_per_PA"),
            "bucket_ops": bucket_ops,
        })

    player_summary.sort(key=lambda p: p["career_pa"], reverse=True)

    # Write outputs
    out1 = ANALYSIS_DIR / "half_life_by_position.json"
    out2 = ANALYSIS_DIR / "player_career_buckets.json"
    json.dump({
        "buckets": BUCKET_LABELS,
        "positions": sorted(POS_KEEP),
        "pos_bucket_summary": pos_bucket_summary,
        "survival_curve": survival_curve,
        "half_life": half_life,
    }, open(out1, "w"), indent=2)
    json.dump({
        "buckets": BUCKET_LABELS,
        "players": player_summary,
    }, open(out2, "w"), indent=2)

    print(f"\nWrote {out1.name} ({len(pos_bucket_summary)} pos×bucket cells)")
    print(f"Wrote {out2.name} ({len(player_summary)} players)")
    print("\nHalf-life by position:")
    print(f"  {'POS':<5} {'cohort':<7} {'baseOPS':<8} {'surv_half':<10} {'prod_half':<10}")
    for pos, hl in sorted(half_life.items()):
        bops = f"{hl['baseline_ops']:.3f}" if hl['baseline_ops'] else "—"
        print(f"  {pos:<5} {hl['cohort_size']:<7} {bops:<8} {str(hl['survival_half_life'] or '—'):<10} {str(hl['production_half_life'] or '—'):<10}")

    print("\nSurvival curve (% of debut cohort still putting up 300+ PA seasons):")
    print(f"  {'POS':<5} {'1-3':<6} {'4-6':<6} {'7-9':<6} {'10-12':<7} {'13-15':<7} {'16+':<6}")
    for pos in sorted(POS_KEEP):
        sc = survival_curve.get(pos)
        if not sc: continue
        sr = sc["survival_rate"]
        print(f"  {pos:<5} {sr.get('1-3', 0):.0%}   {sr.get('4-6', 0):.0%}   {sr.get('7-9', 0):.0%}   {sr.get('10-12', 0):.0%}    {sr.get('13-15', 0):.0%}    {sr.get('16+', 0):.0%}")


if __name__ == "__main__":
    main()
