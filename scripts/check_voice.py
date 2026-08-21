#!/usr/bin/env python3
"""Check a draft against the house voice, which is Patrick's teaching voice.

The targets are not opinions. They were measured on 2026-08-20 from 52,069 words
of GradStats-Book against 203,522 words of the newsletter. See
corpus/house-style.md for the full comparison and the reasoning.

Two things this looks for:

1. PERSON. The biggest measured gap by far. His prose talks *to* a reader --
   "you" at 15.67 per thousand words, "we" at 8.44 -- while the newsletter talks
   *about* sport at 5.91 and 3.34. Fixing this does more for the voice than every
   word-level change combined.

2. TICS. Not chatbot slop -- the classic AI tells ("testament to", "underscores",
   "it is worth noting") measured ZERO across all 175 works. The real problem is a
   handful of rhetorical moves repeated into invisibility. The antithesis
   "X is not A. It is B." appears in 77 of 175 pieces.

A tic is a FREQUENCY problem, not a banned-word problem. "Exactly" is a fine word.
It is not a fine word 182 times.

Deliberately NOT flagged: em dashes. The first pass "found" a 200x overuse against
the book and it was an artifact of the measurement -- he uses the dash aside more
often than the newsletter does (15.94 vs 12.25 per 1k), he just types it as a
spaced hyphen. Scrubbing them would have deleted his voice, not a model's.

Usage:
    python3 scripts/check_voice.py queue/123-foo.html
    python3 scripts/check_voice.py --corpus published/
"""
import os, re, sys, glob, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from check_readability import article_text
except ImportError:
    sys.exit("check_voice.py must sit beside check_readability.py")

# per 1,000 words, measured from GradStats-Book
TARGETS = {
    "you / your":      (r"\byou\b|\byour\b",                15.67, 6.0),
    "we / us / our":   (r"\bwe\b|\bus\b|\bour\b",            8.44, 3.0),
    "imperative open": (r"(?m)(^|\.\s+)(Ask|Notice|Watch|Look|Consider|Try|Remember|Hold)\b",
                                                             1.20, 0.4),
    "semicolon":       (r";",                                4.51, 1.5),
}

TICS = {
    "antithesis 'X is not A. It is B.'": r"\bis not [^.]{3,40}\.\s+It is\b",
    "'exactly'":                          r"\bexactly\b",
    "'quietly'":                          r"\bquietly\b",
    "'genuinely'":                        r"\bgenuinely\b",
    "'precisely'":                        r"\bprecisely\b",
    "'Here is the…' opener":              r"(?m)(^|\.\s+)Here is (the|what|why|how)",
    "'the shape of' / 'same shape'":       r"\bthe shape of\b|\bsame shape\b",
    "'engineered/built to'":              r"\bengineered to\b|\bbuilt to\b",
    "rule of three":                      r"\b\w+, \w+,? and \w+\.",
}

# These measured zero across the whole corpus. Kept so they stay at zero.
SLOP = {
    "'it is worth noting'":  r"it('s| is) worth noting|important to note",
    "'underscores'":         r"\bunderscor\w+|highlights the importance",
    "'testament / pivotal'": r"\btestament\b|\bpivotal\b|\bvital role\b",
    "'delve / tapestry'":    r"\bdelv\w+|\btapestry\b|\bmultifaceted\b|\bplethora\b",
}


def per1k(rx, text, words):
    return len(re.findall(rx, text, re.I)) / max(words, 1) * 1000


def report(path):
    text = article_text(path)
    words = len(text.split())
    if words < 80:
        return None
    print(f"\n{'='*72}\n{os.path.basename(path)}   ({words} words)")

    print("\n  PERSON  (is this written TO a reader, or ABOUT a subject?)")
    thin = []
    for name, (rx, target, floor) in TARGETS.items():
        v = per1k(rx, text, words)
        flag = "ok" if v >= floor else "THIN"
        if v < floor:
            thin.append(name)
        print(f"    {name:<18}{v:6.2f}/1k   (book {target:5.2f}, floor {floor:4.1f})  {flag}")

    hits = [(n, len(re.findall(r, text, re.I))) for n, r in TICS.items()]
    hits = [(n, c) for n, c in hits if c]
    if hits:
        print("\n  TICS  (frequency problems, not banned words)")
        for n, c in sorted(hits, key=lambda x: -x[1]):
            print(f"    {c:>3}x  {n}")

    slop = [(n, len(re.findall(r, text, re.I))) for n, r in SLOP.items()]
    slop = [(n, c) for n, c in slop if c]
    if slop:
        print("\n  CLASSIC AI SLOP -- these measured ZERO corpus-wide; keep it that way")
        for n, c in slop:
            print(f"    {c:>3}x  {n}")

    verdict = "THIN VOICE" if len(thin) >= 3 else ("ok" if not thin else "watch")
    print(f"\n  verdict: {verdict}" + (f"  (thin: {', '.join(thin)})" if thin else ""))
    return verdict


def corpus(paths):
    files = []
    for p in paths:
        files += sorted(glob.glob(os.path.join(p, "*.html"))) if os.path.isdir(p) else [p]
    blob, total = [], 0
    for f in files:
        t = article_text(f)
        if len(t.split()) >= 80:
            blob.append(t)
            total += len(t.split())
    all_text = " ".join(blob)
    print(f"\n{len(blob)} works, {total:,} words\n")
    print(f"  {'feature':<38}{'/1k':>8}{'book':>8}")
    for name, (rx, target, floor) in TARGETS.items():
        print(f"  {name:<38}{per1k(rx, all_text, total):>8.2f}{target:>8.2f}")
    print()
    for name, rx in sorted(TICS.items(), key=lambda kv: -len(re.findall(kv[1], all_text, re.I))):
        c = len(re.findall(rx, all_text, re.I))
        n = sum(1 for t in blob if re.search(rx, t, re.I))
        if c:
            print(f"  {name:<38}{c:>8}   in {n} files")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--corpus", action="store_true", help="aggregate instead of per-file")
    a = ap.parse_args()
    if a.corpus:
        corpus(a.paths)
        return
    files = []
    for p in a.paths:
        files += sorted(glob.glob(os.path.join(p, "*.html"))) if os.path.isdir(p) else [p]
    bad = sum(1 for f in files if report(f) == "THIN VOICE")
    print(f"\n{'='*72}\n{len(files)} checked, {bad} with thin voice")


if __name__ == "__main__":
    main()
