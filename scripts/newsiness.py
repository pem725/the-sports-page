#!/usr/bin/env python3
"""NEWSINESS — what The Sports Page runs tomorrow, and why.

    python3 scripts/newsiness.py                 # rank the candidate pile
    python3 scripts/newsiness.py --explain SLUG  # show one story's full working
    python3 scripts/newsiness.py --panel         # printable sheet for the review panel

WHY A METRIC AT ALL. There is one slot a day. Every story competes with every
other, and "this feels big" is not a reason anyone can argue with. A number can
be argued with, which is the point: the panel should be able to say the score is
wrong and show where.

THE INVERSION THAT DEFINES THIS PAPER. Most sports desks pick the biggest event
and then look for numbers in it. We do the opposite: we pick the most interesting
NUMBER and then explain the sport around it. So GRIP — the strength of the
underlying statistic — is not one term among five. It MULTIPLIES the rest. A
Super Bowl with a dull number scores near zero. A Tuesday game between two
eliminated clubs with a shocking number can lead the paper.

    NEWSINESS = (GRIP / 10) x (0.35 TWIST + 0.25 CLOCK + 0.15 STACK + 0.25 CARRY)

Five components, each scored 0-10, each with a stated rubric so two people
scoring the same story land close:

  GRIP   the number itself. Did we compute it? Can we defend it? Does it have
         error bars? A number we pulled from a broadcast graphic is a 2. A number
         we computed from primary data, verified three ways, with an interval, is
         a 9. Zero means there is no number, and zero means no story.

  TWIST  distance from what a reasonable person expects. Not "surprising to
         someone who knows nothing" — surprising to someone who follows the sport.
         The best twists have a trap: an obvious answer that is wrong.

  CLOCK  what publishing today buys over publishing in a month. A result that
         decays in three days scores high; a methods piece scores low and that is
         fine, because CLOCK is only a quarter of the weight.

  STACK  audience, on the paper-stack scale already defined in
         corpus/bometer-and-the-stack.md. One page is a thousand plausible
         readers; the Super Bowl is about fourteen trees. Deliberately the
         SMALLEST weight — this paper is not chasing crowds.

  CARRY  does the lesson survive outside sport? "A deficit is a fact and
         superiority is a rate" carries. "The Rays are lucky" does not.

Answerability is a GATE, not a component. If the data cannot settle it, the story
is not ready however well it scores, and gets held rather than ranked.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PILE = os.path.join(REPO, "data", "story-candidates.json")

W = {"twist": 0.35, "clock": 0.25, "stack": 0.15, "carry": 0.25}
RUBRIC = {
    "grip":  {0: "no number", 2: "a number someone else published",
              5: "our number, single source", 8: "computed from primary data, verified",
              10: "computed, verified three ways, with an interval and a stated limit"},
    "twist": {0: "confirms what everyone assumes", 3: "mildly counterintuitive",
              6: "contradicts a reasonable prior", 9: "the obvious answer is wrong and we can show why"},
    "clock": {0: "true forever", 3: "good for a season", 6: "good for a fortnight",
              9: "decays within days"},
    "stack": {0: "under a page", 3: "a few hundred pages", 6: "a ream",
              9: "a tree or more"},
    "carry": {0: "sport only", 4: "transfers to one other domain",
              7: "a general habit of thought", 10: "changes how you read any number"},
}


def score(c):
    grip = c["grip"] / 10.0
    rest = sum(W[k] * c[k] for k in W)
    return round(grip * rest, 2)


def load():
    if not os.path.exists(PILE):
        return {"candidates": []}
    return json.load(open(PILE))


def bar(v, n=10):
    return "#" * int(round(v)) + "." * (n - int(round(v)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--explain", metavar="SLUG")
    ap.add_argument("--panel", action="store_true")
    a = ap.parse_args()
    d = load()
    cands = [c for c in d["candidates"]]
    for c in cands:
        c["score"] = score(c)
    cands.sort(key=lambda c: -c["score"])

    if a.explain:
        c = next((x for x in cands if x["slug"] == a.explain), None)
        if not c:
            print(f"  no candidate '{a.explain}'"); return 1
        print(f"\n  {c['title']}\n  {'-'*len(c['title'])}")
        print(f"  NEWSINESS {c['score']}\n")
        print(f"  GRIP  {c['grip']:>2}/10  {bar(c['grip'])}  (multiplier: x{c['grip']/10:.2f})")
        for k in ("twist", "clock", "stack", "carry"):
            print(f"  {k.upper():<5} {c[k]:>2}/10  {bar(c[k])}  weight {W[k]:.2f}")
        print(f"\n  why: {c.get('why','—')}")
        print(f"  the number: {c.get('number','—')}")
        print(f"  answerable: {'yes' if c.get('answerable') else 'NOT YET — held'}")
        if c.get("held"):
            print(f"  held because: {c['held']}")
        return 0

    if a.panel:
        print("\n  THE SPORTS PAGE — STORY PANEL\n  " + "="*58)
        print("  Score each 0-10. GRIP multiplies everything, so a story with no")
        print("  number scores zero however good it sounds.\n")
        for k, r in RUBRIC.items():
            print(f"  {k.upper()}")
            for v in sorted(r):
                print(f"      {v:>2}  {r[v]}")
            print()
        print("  NEWSINESS = (GRIP/10) x (0.35 TWIST + 0.25 CLOCK + 0.15 STACK + 0.25 CARRY)\n")
        for c in cands:
            print(f"  [ ] {c['title']}")
            print(f"        grip __  twist __  clock __  stack __  carry __      (ours: {c['score']})")
        return 0

    ready = [c for c in cands if c.get("answerable")]
    held = [c for c in cands if not c.get("answerable")]
    print(f"\n  {len(cands)} candidates. NEWSINESS = (GRIP/10) x (.35 twist + .25 clock + .15 stack + .25 carry)\n")
    print(f"  {'':<4}{'score':>6}  {'grip':>4}{'twst':>5}{'clck':>5}{'stck':>5}{'cary':>5}   story")
    for i, c in enumerate(ready, 1):
        print(f"  {i:<4}{c['score']:>6}  {c['grip']:>4}{c['twist']:>5}{c['clock']:>5}"
              f"{c['stack']:>5}{c['carry']:>5}   {c['title'][:52]}")
    if held:
        print(f"\n  HELD — not answerable with data we have:")
        for c in held:
            print(f"    ({c['score']:>5})  {c['title'][:52]}")
            print(f"             {c.get('held','')}")
    print(f"\n  run --explain SLUG for one story's working, or --panel for a review sheet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
