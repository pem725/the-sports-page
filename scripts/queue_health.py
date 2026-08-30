#!/usr/bin/env python3
"""Report the queue's health: how long it lasts, and what is about to rot.

    python3 scripts/queue_health.py

One issue a day means every slot competes with every other. Two things should
decide the order, and neither of them should live in somebody's head:

  HOW FAST IT ROTS. Each queue file declares `decay:` in its PUBLISH-META:
      hot    numbers move daily; publish within ~3 days or rewrite it
      dated  tied to a fixed event; has a real deadline
      slow   season-bound but stable for weeks
      keeps  methods or history; good any time, and therefore the buffer

  WHETHER THE ROTATION HOLDS. No two consecutive issues share a topic.

The buffer matters as much as the freshness. A queue of nothing but hot pieces
cannot absorb a day when the news breaks; a queue of nothing but evergreen ones
is never about anything. This prints both so the balance is visible.
"""
import datetime
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORDER = os.path.join(REPO, "QUEUE_ORDER.txt")
LIMIT = {"hot": 3, "dated": None, "slow": 21, "keeps": None}


def meta(path):
    t = open(path, encoding="utf-8").read()
    g = lambda k: (re.search(rf"{k}:\s*([^\n#]+)", t) or [None, ""])[1].strip()
    return g("topic"), (g("decay") or "untagged")


def main():
    files = [l.strip() for l in open(ORDER) if l.strip()]
    d = datetime.date.today() + datetime.timedelta(days=1)
    if d.weekday() == 6:
        d += datetime.timedelta(days=1)
    rows, prev, clashes, risks = [], None, 0, []
    for f in files:
        p = os.path.join(REPO, "queue", f)
        if not os.path.exists(p):
            print(f"  MISSING: {f} is in QUEUE_ORDER but not in queue/")
            continue
        topic, decay = meta(p)
        clash = topic == prev
        clashes += clash
        wait = (d - datetime.date.today()).days
        lim = LIMIT.get(decay)
        risky = lim is not None and wait > lim
        if risky:
            risks.append((f, decay, wait, lim))
        rows.append((d, topic, decay, f, clash, risky))
        prev = topic
        d += datetime.timedelta(days=1)
        if d.weekday() == 6:
            d += datetime.timedelta(days=1)
    print(f"  {len(rows)} issues queued, running through {rows[-1][0]:%a %b %d}\n" if rows else "  queue empty\n")
    print(f"  {'date':<12}{'topic':<9}{'decay':<8}{'file'}")
    for dt, topic, decay, f, clash, risky in rows:
        flag = "  <-- BACK-TO-BACK" if clash else ("  <-- may be stale by then" if risky else "")
        print(f"  {dt:%a %b %d}  {topic:<9}{decay:<8}{f}{flag}")
    mix = {}
    for *_, decay, _f, _c, _r in [(r[0], r[1], r[2], r[3], r[4], r[5]) for r in rows]:
        mix[decay] = mix.get(decay, 0) + 1
    print(f"\n  mix: " + ", ".join(f"{k} {v}" for k, v in sorted(mix.items())))
    buf = mix.get("keeps", 0)
    print(f"  buffer (pieces that keep): {buf}")
    if buf < 2:
        print("  WARNING: fewer than two evergreen pieces. A breaking story would leave a hole.")
    if clashes:
        print(f"  WARNING: {clashes} back-to-back topic clash(es).")
    for f, decay, wait, lim in risks:
        print(f"  WARNING: {f} is '{decay}' but waits {wait} days (limit {lim}).")
    if not clashes and not risks and buf >= 2:
        print("  healthy: rotation clean, nothing rotting, buffer intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
