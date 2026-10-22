import json, glob, csv, pathlib
D = pathlib.Path(__file__).resolve().parent
rows = {}; coaches = {}
for f in glob.glob(str(D/"cache/coaches_*.json")):
    for c in json.load(open(f)):
        cid = c["id"]
        coaches[cid] = (c["firstName"], c["lastName"], c.get("hireDate"))
        for s in c["seasons"]:
            rows[(cid, s["school"], s["year"])] = dict(cid=cid, first=c["firstName"], last=c["lastName"], school=s["school"], year=s["year"], games=s["games"], w=s["wins"], l=s["losses"], t=s["ties"])
out = sorted(rows.values(), key=lambda r: (r["school"], r["year"], r["cid"]))
with open(D/"seasons.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
print(len(out), "coach-seasons;", len(coaches), "coach ids")
ids70 = {r["cid"] for r in out if r["year"] >= 1970}
print("coaches with a season >=1970:", len(ids70))
# duplicate name check
from collections import Counter
nm = Counter((coaches[i][0], coaches[i][1]) for i in coaches)
print("dup names:", [k for k,v in nm.items() if v>1][:20])
# school-years with multiple coaches
sy = Counter((r["school"], r["year"]) for r in out)
print("school-years w/ >1 coach:", sum(1 for v in sy.values() if v>1))
