#!/usr/bin/env python3
"""Does this headline have any juice? Checks the house rules, one file or many.

    python3 scripts/check_headline.py queue/151-slug.html
    python3 scripts/check_headline.py queue/*.html
    python3 scripts/check_headline.py --corpus        # tic frequency across published/

WHERE THESE RULES CAME FROM. Not from a style guide -- from watching which
headlines the editor actually reacted to on 2026-09-01, and which he threw out.
Each rule below names the case that produced it, because a rule whose origin is
forgotten gets argued with forever.

THE ONE THING THAT WAS ACTUALLY WRONG. Our headlines were not badly written;
they were finished. "Home Field Is Worth Thirteen Ranks. Most of It Is the Road
Team Losing Them." states the finding, the mechanism and the size. There is
nothing left to learn, so there is no reason to open it. The BLUF rule says the
finding goes in the first breath -- and we were obeying it one step too early,
in the headline, where the job is to open the gap rather than close it. The DECK
closes it.
"""
import argparse
import glob
import html
import re
import sys

# Verbs and phrases about our own apparatus. Nobody opens a newspaper to read
# about the newspaper's method. ("We Built a Schedule Rating That Cannot Know
# Who the SEC Is" -- rejected outright, and rightly.)
METHOD = re.compile(r"\b(we built|we ran|our model|our rating|we computed|"
                    r"a rating that|our method|we simulated|we fit)\b", re.I)

# A second beat that EXPLAINS the first, rather than landing a new fact.
EXPLAINER = re.compile(r"\b(because|which is why|the reason|so that|meaning that|"
                       r"in other words|that is why)\b", re.I)

# A bare decimal with no noun attached to it. "2.98 Does Not Mean Three Times
# Likelier" was rejected: 2.98 is a statistic about a statistic and means
# nothing to a person. "209 of Every 1,000" was loved, because 209 are people.
BARE_DECIMAL = re.compile(r"(?<![\w.])\d+\.\d+(?!\s*(%|points?|per|seconds?|"
                          r"million|billion|ranks?))", re.I)

HEDGE = re.compile(r"\b(may|might|could|reportedly|seems|appears|possibly)\b", re.I)


def hed_of(path):
    t = open(path, encoding="utf-8").read()
    m = re.search(r'<h2 class="hed">(.*?)</h2>', t, re.S)
    if not m:
        return None
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))).strip()


def beats(h):
    """Sentence-ish chunks. A question mark ends a beat too."""
    return [b for b in re.split(r"(?<=[.?!])\s+", h.strip()) if b.strip()]


def check(h):
    out, words = [], len(h.split())
    b = beats(h)

    if words > 14:
        out.append(("FAIL", f"{words} words. Two beats max, and this is a paragraph."))
    elif words > 10 and len(b) < 2:
        out.append(("WARN", f"{words} words in a single beat -- can it be cut to ten?"))

    if len(b) > 2:
        out.append(("FAIL", f"{len(b)} beats. Two is the ceiling."))

    if len(b) == 2 and EXPLAINER.search(b[1]):
        out.append(("FAIL", "the second beat explains the first. It must land a NEW fact."))

    if METHOD.search(h):
        out.append(("FAIL", "headlines our own apparatus. Report the finding, not the rig."))

    if BARE_DECIMAL.search(h) and not re.search(r"\b\d+\s*(of|in)\s", h, re.I):
        out.append(("WARN", "a bare decimal with nothing human attached. 209 pitchers beats 2.98."))

    if HEDGE.search(h):
        out.append(("WARN", "hedged. Hedge in the piece, never in the headline."))

    # positives, reported so a thin headline is visibly thin
    good = []
    if re.search(r"\b(we were wrong|we got it wrong|our mistake|we called it)\b", h, re.I):
        good.append("admits error -- the strongest headline we own")
    if re.search(r"\b(nobody|none|never|no one|not one|zero)\b", h, re.I):
        good.append("uses absence; a zero is louder than a count")
    if "?" in h:
        good.append("asks a question")
    if re.search(r"\b\d", h):
        good.append("carries a number")
    if re.search(r"\b(you|your)\b", h, re.I):
        good.append("second person")
    # The unequal comparison: a small thing beating a large one. This is why
    # "One Game Told Us More Than the Whole Summer Did" works with no number,
    # no question and no absence -- the pull is the disproportion itself.
    if re.search(r"\b(more than|less than|twice|half as|outweighs|beats|worth more|"
                 r"bigger than|smaller than|cheaper than|longer than)\b", h, re.I):
        good.append("unequal comparison -- a small thing beating a large one")
    # The paradox: the same noun on both sides of a negation.
    if re.search(r"\bnot\b", h, re.I):
        low = re.findall(r"[a-z]{4,}", h.lower())
        if len(low) != len(set(low)):
            good.append("paradox -- the same thing on both sides of a 'not'")
    if not good:
        out.append(("WARN", "no number, no question, no absence, no admission. Where is the pull?"))
    return out, good, words, len(b)


def corpus_tic(paths):
    """The 'X. Y.' antithesis is our worst habit. Cap it at one in four."""
    heds = [h for h in (hed_of(p) for p in paths) if h]
    two = [h for h in heds if len(beats(h)) == 2 and "?" not in h]
    print(f"\n  {len(heds)} headlines; {len(two)} are the two-beat antithesis "
          f"({len(two)/max(len(heds),1)*100:.0f}%, ceiling 25%)")
    if len(two) / max(len(heds), 1) > 0.25:
        print("  OVER THE CAP. Vary the rhythm -- it has become a tic, the way it did in body copy.")
    return heds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--corpus", action="store_true")
    a = ap.parse_args()
    paths = a.paths or sorted(glob.glob("published/*.html"))
    if a.corpus:
        corpus_tic(paths)
        return 0
    bad = 0
    for p in paths:
        h = hed_of(p)
        if not h:
            continue
        issues, good, w, nb = check(h)
        worst = "FAIL" if any(k == "FAIL" for k, _ in issues) else ("WARN" if issues else "PASS")
        bad += worst == "FAIL"
        print(f"\n  {p.split('/')[-1]}   [{worst}]  {w} words, {nb} beat(s)")
        print(f"    {h}")
        for k, m in issues:
            print(f"      {k}: {m}")
        for g in good:
            print(f"      + {g}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
