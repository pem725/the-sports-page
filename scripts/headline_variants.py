#!/usr/bin/env python3
"""Twenty headlines from the AI box, scored by check_headline.py. The editor picks.

The house headline rules (CLAUDE.md, "HEADLINES OPEN THE GAP") are specific and
checkable, which makes this a good job for a local model: generate many, let the
existing checker throw out the failures, and show the survivors ranked. The model
only rephrases what the deck already says. Any variant whose numbers are not in
the piece is dropped automatically -- rule 10, juice only from the real number.

LAN-only desk tool (see cold_read.py). Nothing is written to the file; the editor
chooses, and a human edits the <h1>.

Usage:
  python3 scripts/headline_variants.py queue/NNN-slug.html [-n 20]
"""
import argparse, html, json, os, re, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_headline as ch
from cold_read import article_text

HOST = os.environ.get("AIBOX", "http://192.168.0.65:11434")
RULES = """House headline rules:
1. Numbers count people or things, never statistics ("209 of Every 1,000 Never Pitch Again", not "2.98 Times Likelier").
2. Round in the headline ("More Than Five Thousand"), exact in the piece.
3. Admit error when earned ("We Were Wrong About Cleveland").
4. Never headline the method or the model.
5. A question only if a fan would say it out loud ("Where Do They Find These Guys?").
6. Absence is louder than abundance: nobody, never, zero.
7. An unequal comparison needs no number ("One Game Told Us More Than the Whole Summer Did").
8. At most two beats, about ten words; the second beat must add a NEW fact, never explain the first.
9. Do not make every headline "X. Now Y." Vary the shape.
10. Promise only what the article pays. Use only facts in the article.
The headline opens a gap; the deck closes it. Do not give away the whole finding."""


def numbers(t):
    return {re.sub(r"[,%]", "", n) for n in re.findall(r"\d[\d,]*\.?\d*%?", t)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file"); ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--model", default="gpt-oss:20b")
    a = ap.parse_args()
    text = article_text(a.file)
    current = ch.hed_of(a.file)
    prompt = (f"{RULES}\n\nWrite {a.n} different headlines for this article, in Title Case. "
              f'Reply JSON: {{"headlines": ["...", ...]}}\n\nARTICLE:\n{text}')
    payload = {"model": a.model, "stream": False, "format": "json", "think": "low",
               "options": {"temperature": 0.9, "num_ctx": 16384},
               "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(f"{HOST}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        heds = json.loads(json.load(r)["message"]["content"]).get("headlines", [])
    allowed = numbers(text) | {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
    rows = []
    for h in dict.fromkeys(x.strip() for x in heds if isinstance(x, str) and x.strip()):
        extra = numbers(h) - allowed
        if extra:
            rows.append((-99, h, f"DROPPED: number(s) not in the piece: {', '.join(sorted(extra))}")); continue
        out, good, words, nb = ch.check(h)
        fails = [m for lvl, m in out if lvl == "FAIL"]; warns = [m for lvl, m in out if lvl == "WARN"]
        score = 2 * len(good) - 5 * len(fails) - len(warns)
        note = "; ".join(fails and ["FAIL " + f for f in fails] or good or warns)[:110]
        rows.append((score, h, note))
    print(f"CURRENT  {current}\n")
    for score, h, note in sorted(rows, key=lambda r: -r[0]):
        tag = "drop" if score == -99 else f"{score:+d}"
        print(f"  {tag:>5}  {h}\n         {note}")
    print("\nThe editor picks. Survivors used only numbers found in the piece; check every claim anyway.")


if __name__ == "__main__":
    main()
