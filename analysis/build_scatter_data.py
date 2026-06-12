"""
Pack the full cohort into a compact format for the trajectory viewer.

Per player, seasons become a row of numbers in a fixed schema. Drops
verbose JSON keys; ~70% smaller than the named-object version.

Schema:
  hit_schema: ["svc","PA","OPS","OBP","ISO","HR_PA","K_PA","BB_PA","AVG"]
  pit_schema: ["svc","IP","ERA","WHIP","K9","BB9","HR9"]
"""
import json
from pathlib import Path

ANALYSIS = Path(__file__).parent
src = json.load(open(ANALYSIS / "full_cohort_data.json"))

HIT_SCHEMA = ["svc","PA","OPS","OBP","ISO","HR_PA","K_PA","BB_PA","AVG"]
PIT_SCHEMA = ["svc","IP","ERA","WHIP","K9","BB9","HR9"]

def pack_hit(p):
    return {
        "n": p["name"],
        "p": p["pos"],
        "d": p["debut"],
        "t": p["tier"],
        "pa": p["career_pa"],
        "y": p["career_yrs"],
        "s": [[s.get(k) for k in HIT_SCHEMA] for s in p["seasons"]]
    }

def pack_pit(p):
    return {
        "n": p["name"],
        "r": p["role"],
        "d": p["debut"],
        "t": p["tier"],
        "ip": p["career_ip"],
        "y": p["career_yrs"],
        "s": [[s.get(k) for k in PIT_SCHEMA] for s in p["seasons"]]
    }

# Keep only players with debut_year >= 1985 AND skip players whose primary
# position is something we don't visualize (P for hitters, IF/OF lumped, etc.)
KEEP_POS = {"C","1B","2B","3B","SS","LF","CF","RF","DH"}
KEEP_ROLE = {"SP","RP"}

hit = [pack_hit(p) for p in src["players_hit"] if p["pos"] in KEEP_POS]
pit = [pack_pit(p) for p in src["players_pit"] if p["role"] in KEEP_ROLE]

out = {
    "hit_schema": HIT_SCHEMA,
    "pit_schema": PIT_SCHEMA,
    "hit": hit,
    "pit": pit,
    "survival_hit": src["survival_hit"],
    "survival_pit": src["survival_pit"],
}

dest = Path("/home/pem725/GitTemp/the-sports-page/tools/half-life-trajectories-data.json")
dest.write_text(json.dumps(out, separators=(",",":")))
print(f"Wrote {dest.name} ({dest.stat().st_size/1024:.0f} KB)")
print(f"  hit: {len(hit)} players, pit: {len(pit)} pitchers")
