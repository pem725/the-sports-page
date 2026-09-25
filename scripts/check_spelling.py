#!/usr/bin/env python3
"""Catch British spellings. This is an American newspaper.

    python3 scripts/check_spelling.py queue/*.html
    python3 scripts/check_spelling.py --all

WHY THIS EXISTS. On 2026-09-23 the editor read the word "maths" in a draft and
pointed out the obvious: "I'm in the US. We don't say maths. We say math." A
sweep found 102 British spellings across 46 files, including 52 already published
-- favourite, analyse, grey, defence, centred, cancelled. Nobody had noticed
because each one is individually invisible and collectively wrong.

It checks prose only. Script and style blocks are skipped so CSS colour keywords
and JavaScript identifiers are not flagged.

KNOWN LIMIT: a proper noun that is legitimately British will trip this -- Centre
College, the Labour Party, a person named Grey. There are none in the archive
today, checked by hand at the time of the sweep. If one arrives, the right fix is
an exception here, not a rewritten name.
"""
import argparse, glob, pathlib, re, sys

PAIRS = [("maths","math"),("favourite","favorite"),("favour","favor"),("colour","color"),
 ("behaviour","behavior"),("honour","honor"),("neighbour","neighbor"),("labour","labor"),
 ("rumour","rumor"),("organis","organiz"),("recognis","recogniz"),("normalis","normaliz"),
 ("summaris","summariz"),("prioritis","prioritiz"),("centre","center"),
 # ANALYSE, BUT NOT ANALYSES. "Analyses" is the plural of "analysis" and is
 # correct American English. The matcher is a STEM matcher -- it anchors with \b
 # at the START of a word and nothing at the end, which is exactly why
 # ("organis","organiz") correctly catches organise, organising and organisation.
 # The same behaviour made "analyse" fire inside "analyses", flagging a section
 # heading that had been right all along.
 #
 # NOTE THE ENTRIES GO STRAIGHT INTO A REGEX. The first attempt at a fix used
 # ("analyse.","analyze.") meaning "analyse followed by a period" -- but the dot
 # is a wildcard, so it matched "analyses" even harder. Anything added here that
 # contains . ? * + ( ) [ ] is a pattern, not a literal.
 #
 # HONEST LIMIT: "he analyses the data" is British for "analyzes" and the
 # lookahead will miss it. Missing a rare verb beats flagging every correct plural.
 ("analyse(?!s)","analyze"),("analysing","analyzing"),
 ("metre","meter"),("defence","defense"),("offence","offense"),("practise","practice"),
 ("licence","license"),("travelling","traveling"),("cancelled","canceled"),
 ("modelling","modeling"),("learnt","learned"),("amongst","among"),("whilst","while"),
 ("per cent","percent"),("grey","gray"),
 # -ISE VERBS, ADDED 2026-09-23. Note these are spelled out rather than stemmed.
 # The obvious shortcut is a stem like ("criticis","criticiz") and it is a trap:
 # that flags CRITICISM, ("characteris") flags CHARACTERISTIC, ("specialis")
 # flags SPECIALIST, ("realis") flags REALISM and REALIST, and ("agonis") flags
 # AGONIST, which this paper will use the moment it writes about pharmacology.
 # The two stems already here -- organis, recognis -- happen to be safe. Most are
 # not, so each verb below is listed in full.
 ("agonise","agonize"),("agonising","agonizing"),("agonised","agonized"),
 ("realise","realize"),("realising","realizing"),("realised","realized"),
 ("criticise","criticize"),("criticising","criticizing"),("criticised","criticized"),
 ("emphasise","emphasize"),("emphasising","emphasizing"),("emphasised","emphasized"),
 ("apologise","apologize"),("apologising","apologizing"),("apologised","apologized"),
 ("specialise","specialize"),("specialising","specializing"),("specialised","specialized"),
 ("characterise","characterize"),("characterising","characterizing"),("characterised","characterized"),
 ("minimis","minimiz"),("maximis","maximiz"),("utilis","utiliz"),("penalis","penaliz"),
 ("standardis","standardiz"),("randomis","randomiz"),
 # optimis -> optimiz would flag OPTIMISM. Caught by the false-positive test.
 ("optimise","optimize"),("optimising","optimizing"),("optimised","optimized"),
 ("sceptic","skeptic"),("programme","program"),("storey","story"),("draught","draft")]

def prose(path):
    t = pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    return re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", t, flags=re.S | re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    files = [f for p in a.paths for f in glob.glob(p)]
    if a.all or not files:
        files = sorted(glob.glob("published/*.html")) + sorted(glob.glob("queue/*.html")) \
              + ["index.html", "about.html", "ask.html", "feed.xml"]
    bad = 0
    for f in files:
        if not pathlib.Path(f).exists():
            continue
        t = prose(f)
        for br, us in PAIRS:
            for m in re.finditer(r"\b" + br, t, re.I):
                bad += 1
                ctx = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t[max(0, m.start()-45):m.end()+45]))
                print(f"  {pathlib.Path(f).name:<34}{m.group(0):<12}-> {us:<11}...{ctx.strip()[:60]}")
    print(f"\n  {bad} British spelling(s)" + ("" if bad else " -- clean"))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
