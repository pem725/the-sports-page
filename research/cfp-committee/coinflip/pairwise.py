#!/usr/bin/env python3
"""Head-to-head neutral-site odds among the committee's top 12 (2026-11-17)."""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sim
sp, games, rank = sim.load()
top = sorted(rank, key=rank.get)[:12]
print("by SP+:", [(t, rank[t], sp[t]) for t in sorted(top, key=lambda t: -sp[t])])
others = [t for t in top if t != "Georgia"]
ps = [max(sim.pwin(a, b, sp), 1 - sim.pwin(a, b, sp)) for a, b in itertools.combinations(others, 2)]
print("pairs among 11 non-Georgia:", len(ps), "max fav", round(max(ps), 3), "within 60-40:", sum(p <= .6 for p in ps), "median", sorted(ps)[len(ps)//2])
print("Georgia vs each:", {t: round(sim.pwin("Georgia", t, sp), 2) for t in others})
s512 = [t for t in top if 5 <= rank[t] <= 12]
print("seeds5-12 SP+ range", min(sp[t] for t in s512), max(sp[t] for t in s512))
print("R1 home odds:", {f"{a}-{b}": round(sim.pwin(a, b, sp, 2.5), 2) for a, b in [(top[k-1], top[16-k]) for k in (5, 6, 7, 8)]})
