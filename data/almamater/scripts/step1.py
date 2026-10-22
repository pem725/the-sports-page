import csv, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from wiki import fetch
D = pathlib.Path(__file__).resolve().parent
names = {}
for r in csv.DictReader(open(D/"seasons.csv")):
    names[(r["first"], r["last"])] = 1
titles = []
for f,l in names:
    n = f"{f} {l}".strip()
    titles += [n, f"{n} (American football)", f"{n} (American football coach)"]
print(len(titles))
fetch(titles)
