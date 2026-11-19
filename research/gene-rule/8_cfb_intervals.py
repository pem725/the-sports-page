#!/usr/bin/env python3
"""95% intervals for the per-season college rates in data/cfb-results.json (by_season), by a
game-level bootstrap: whole games are resampled, because drives in one game share an
offense, a defense and a scoreboard. Writes data/cfb-intervals.json. Must be rerun whenever
5_cfb.py is (refresh.sh), or the dots and their fuzz will disagree."""
import importlib.util, json, os
from collections import defaultdict
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("cfb", os.path.join(HERE, "5_cfb.py"))
cfb = importlib.util.module_from_spec(spec); spec.loader.exec_module(cfb)
B, rng = 2000, np.random.default_rng(20261119)

games, _ = cfb.load()
ev = cfb.events(games)
out = {}
for y in cfb.YEARS:
    # per game: [answer scored, answer n, other scored, other n]
    g = defaultdict(lambda: np.zeros(4))
    for e in ev:
        if e["season"] != y or e["kind"] not in ("answer", "other"):
            continue
        j = 0 if e["kind"] == "answer" else 2
        g[e["game"]][j] += e["scored"]; g[e["game"]][j + 1] += 1
    if not g:
        continue
    M = np.array(list(g.values()))
    idx = rng.integers(0, len(M), size=(B, len(M)))
    S = M[idx].sum(axis=1)                      # B x 4
    a, o = S[:, 0] / S[:, 1], S[:, 2] / S[:, 3]
    pt = M.sum(axis=0)
    out[str(y)] = dict(games=len(M),
                       answer=[pt[0] / pt[1], *np.percentile(a, [2.5, 97.5])],
                       other=[pt[2] / pt[3], *np.percentile(o, [2.5, 97.5])])
    print(y, len(M), " ".join(f"{k} {100*v[0]:.1f} ({100*v[1]:.1f}-{100*v[2]:.1f})" for k, v in out[str(y)].items() if k != "games"))
json.dump(out, open(os.path.join(HERE, "data", "cfb-intervals.json"), "w"), indent=1, default=float)
