#!/usr/bin/env python3
"""Gene's Rule, baseball analog: every regular-season line score since 1990, from Retrosheet.

One row per game: date, visitor, home, final runs, and each team's runs by inning.
The information used here was obtained free of charge from and is copyrighted by
Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.
Output: data/raw/mlb-lines.csv.
"""
import csv, io, os, re, sys, urllib.request, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "data", "raw")


def innings(s):
    """'01(10)0x' -> [0, 1, 10, 0, None]"""
    return [None if t == "x" else int(t.strip("()")) for t in re.findall(r"\(\d+\)|\d|x", s)]


def main(a, b):
    out = os.path.join(RAW, "mlb-lines.csv")
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "season", "visitor", "home", "v_runs", "h_runs", "v_line", "h_line"])
        for y in range(a, b + 1):
            z = zipfile.ZipFile(io.BytesIO(urllib.request.urlopen(f"https://www.retrosheet.org/gamelogs/gl{y}.zip", timeout=120).read()))
            n = 0
            for r in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="latin-1")):
                if not r[19] or not r[20]:
                    continue
                w.writerow([r[0], y, r[3], r[6], r[9], r[10],
                            " ".join("x" if v is None else str(v) for v in innings(r[19])),
                            " ".join("x" if v is None else str(v) for v in innings(r[20]))])
                n += 1
            print(y, n, flush=True)
    return out


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1990, int(sys.argv[2]) if len(sys.argv) > 2 else 2025)
