#!/usr/bin/env python3
"""Score a draft for plainness. Bottom line up front, sixth-grade language.

Why this exists: a reader told us the newsletter is too opaque, and the numbers
agreed. Across 141 published issues the median Flesch-Kincaid grade was 7.8 and
the consensus grade was 9. Only 13 of 167 works came in at grade 6 or below. It
had also drifted -- the first twenty issues ran grade 6.8 and about 1,000 words,
the last twenty ran 7.9 and 1,270. Harder and longer, gradually, without anyone
deciding to make it so.

That last part is the reason for a script instead of a resolution. Drift is
invisible one issue at a time and obvious over a hundred. So measure every draft.

Usage:
    python3 scripts/check_readability.py queue/123-foo.html
    python3 scripts/check_readability.py --all published/
    python3 scripts/check_readability.py --quiet queue/*.html   # CI mode
"""
import os, re, sys, glob, html, argparse

try:
    import textstat
except ImportError:
    sys.exit("needs textstat:  pip install textstat")
try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("needs beautifulsoup4:  pip install beautifulsoup4")

TARGET_GRADE = 6.0      # what we are aiming for
WARN_GRADE   = 7.0      # acceptable but drifting
LONG_SENTENCE = 25      # words

# From the humanizer skill (Wikipedia's "Signs of AI writing"), trimmed to the
# ones that actually show up in sports-stats prose. These are not banned words --
# they are tells worth a second look.
AI_TELLS = [
    "it is worth noting", "it's worth noting", "it is important to note",
    "serves as a", "stands as a", "is a testament", "a testament to",
    "underscores", "underscoring", "highlights the importance",
    "plays a crucial role", "plays a key role", "pivotal", "vital role",
    "reflects a broader", "speaks to a broader", "broader trend",
    "in the realm of", "when it comes to", "at the end of the day",
    "navigate the", "delve into", "delving into", "tapestry", "landscape of",
    "not only", "but also", "moreover", "furthermore", "consequently",
    "leverage", "utilize", "myriad", "plethora", "robust", "nuanced",
    "multifaceted", "paradigm", "holistic", "intricate", "profound",
]

# Long Latinate words with short plain equivalents. Proper nouns are excluded
# elsewhere; these are the ones we actually reach for by habit.
HARD_WORDS = {
    "approximately": "about", "additionally": "also", "subsequently": "then",
    "demonstrates": "shows", "indicates": "shows", "illustrates": "shows",
    "utilize": "use", "utilizes": "uses", "sufficient": "enough",
    "numerous": "many", "obtain": "get", "purchase": "buy", "attempt": "try",
    "initiate": "start", "terminate": "end", "facilitate": "help",
    "regarding": "about", "concerning": "about", "prior to": "before",
    "subsequent to": "after", "in order to": "to", "due to the fact that": "because",
    "despite the fact that": "although", "a significant number of": "many",
    "consequently": "so", "nevertheless": "still", "furthermore": "also",
    "substantial": "big", "considerable": "big", "commence": "start",
    "ascertain": "find out", "endeavour": "try", "endeavor": "try",
    "component": "part", "methodology": "method", "conceptualize": "imagine",
}


def article_text(path):
    """The prose a reader actually reads -- no nav, no footer, no chart labels."""
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    body = soup.find(id="main-content") or soup.body or soup
    body = BeautifulSoup(str(body), "html.parser")
    # Tables are scanned, not read. Flattening one into running text produces a
    # nonsense "sentence" -- the reference card in Issue #026 came out as a
    # single 181-word sentence and dragged the whole piece two grades. Excluding
    # them scores the prose, which is the thing a reader actually reads through.
    # The trade-off is real and worth stating: an argument buried in table cells
    # is not measured. Keep arguments in paragraphs.
    for sel in ("script", "style", "nav", "svg", "figcaption", "table"):
        for t in body.find_all(sel):
            t.decompose()
    # Furniture, not prose. The byline and the stat cards are scanned like a
    # dashboard, and flattening them produced two distinct measurement errors:
    # they were reported as one enormous run-on "sentence" ("The Sports Page -
    # The Professor - part two ... 29% an underdog's chance ..."), and they ate
    # most of the 130-word window the reader's-contract check uses, so a piece
    # that opened with a clearly stated question was scored as having none.
    for cls in ("footer", "skip-link", "methods", "datebar", "masthead",
                "byline", "stat-row", "sc", "chart-label", "chart-note"):
        for t in body.find_all(class_=cls):
            t.decompose()
    # Sourcing boxes are citations, not argument, and a different register --
    # dates, proper nouns and model notes will always score hard. Drop them.
    # Only the sourcing ones: .box is also used for real editorial content
    # ("The Vocabulary the Reader Takes Home", "Why We're Calling It Anyway"),
    # and excluding those would hide exactly the prose we mean to measure.
    for t in body.find_all(class_="box"):
        h = t.find(["h3", "h4"])
        if h and re.search(r"notes|sources|how this was computed",
                           h.get_text(strip=True), re.I):
            t.decompose()
    return re.sub(r"\s+", " ", html.unescape(body.get_text(" ", strip=True)))


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def bluf_check(path, text):
    """Is the finding in the first breath, or buried?

    The test is deliberately crude: a number in the opening. Every issue is built
    on one, so if the first two sentences contain none, the piece is warming up
    instead of starting.
    """
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    deck = soup.find(class_="deck")
    # First 60 WORDS, not first 2 sentences. Headlines are often two sentences
    # by themselves ("A Math Teacher Invented the Point Spread. It Took Forty
    # Years to Reach Your Living Room."), so a sentence-based window could stop
    # before reaching the deck and report "no number" on a piece that leads with
    # one. Words are the honest unit: it is roughly what a reader takes in
    # before deciding to stay.
    opening = " ".join(text.split()[:60])
    has_num = bool(re.search(r"\d", opening))
    deck_num = bool(re.search(r"\d", deck.get_text(" ", strip=True))) if deck else False
    return has_num, deck_num, opening[:170]


# ---------------------------------------------------------------- reader's contract
#
# Plain sentences are not the same as a clear piece. Issue #142 scored grade 5.0
# and was still opaque, because a reader could not tell what question it was
# answering, why the answer was surprising, or what to do with it. Simple words,
# invisible purpose.
#
# So four things have to be findable near the top of every issue:
#   1. the QUESTION it answers, written as a question
#   2. the ANSWER, with its number   (covered by the bottom-line-up-front check)
#   3. why the answer is SURPRISING -- what a reasonable person would have expected
#   4. what the reader can TAKE HOME
#
# HONEST LIMIT: this detects the presence of those signals, not their quality. It
# cannot tell a real question from a rhetorical one, or a genuine surprise from a
# claimed one. It catches the piece that never tries. A human still has to read it.
QUESTION_WINDOW = 130      # words

SURPRISE = re.compile(
    r"surpris|counterintuit|you would (expect|think)|most people (assume|think|expect)"
    r"|the opposite|turns out|against intuition|everyone (assumes|thinks|believes)"
    r"|nearly everyone|the answer is no|it is not|it isn't|wrong for the same reason"
    r"|feels obvious|sounds like|you might think", re.I)

TAKEAWAY = re.compile(
    r"take home|take away|takeaway|the lesson|what (this|it) teaches"
    r"|what to carry|worth carrying|what to do with", re.I)


def contract(path, text):
    """Returns (has_question, has_surprise, has_takeaway, the question found)."""
    opening = " ".join(text.split()[:QUESTION_WINDOW])
    q = None
    for sent in sentences(opening):
        if "?" in sent:
            q = sent.strip()
            break
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    heads = " ".join(h.get_text(" ", strip=True) for h in soup.find_all(class_="sh"))
    return bool(q), bool(SURPRISE.search(text)), bool(TAKEAWAY.search(heads)), q


def score(path, quiet=False):
    text = article_text(path)
    words = text.split()
    if len(words) < 80:
        return None
    fk = textstat.flesch_kincaid_grade(text)
    ease = textstat.flesch_reading_ease(text)
    ss = sentences(text)
    long_ss = [s for s in ss if len(s.split()) > LONG_SENTENCE]
    low = text.lower()
    tells = sorted({t for t in AI_TELLS if t in low})
    hard = sorted({w: r for w, r in HARD_WORDS.items() if re.search(rf"\b{re.escape(w)}\b", low)}.items())
    has_num, deck_num, opening = bluf_check(path, text)

    has_q, has_s, has_t, the_q = contract(path, text)
    missing = [n for n, ok in (("question", has_q), ("surprise", has_s),
                               ("takeaway", has_t)) if not ok]

    grade_status = ("PASS" if fk <= TARGET_GRADE else
                    "WARN" if fk <= WARN_GRADE else "FAIL")
    # A piece that reads easily but never says what it is for is not finished.
    # Two or more missing frame elements is a fail on its own.
    frame_status = "PASS" if not missing else ("WARN" if len(missing) == 1 else "FAIL")
    status = max((grade_status, frame_status),
                 key=lambda s: {"PASS": 0, "WARN": 1, "FAIL": 2}[s])
    if quiet and status == "PASS":
        return status

    print(f"\n{'='*72}\n{os.path.basename(path)}   [{status}]")
    print(f"  Flesch-Kincaid grade {fk:.1f}   (target <= {TARGET_GRADE}, warn <= {WARN_GRADE})")
    print(f"  Reading ease         {ease:.1f}   (60-70 plain, 80+ easy)")
    print(f"  {len(words)} words, {len(ss)} sentences, "
          f"avg {len(words)/max(len(ss),1):.1f} words/sentence")

    print(f"\n  BOTTOM LINE UP FRONT   [{grade_status} on grade]")
    print(f"    number in first two sentences : {'yes' if has_num else 'NO -- the piece is warming up'}")
    print(f"    number in the deck            : {'yes' if deck_num else 'NO'}")
    print(f"    opens: {opening!r}")

    print(f"\n  READER'S CONTRACT   [{frame_status}]")
    print(f"    states a QUESTION up front    : "
          + (f"yes -- {the_q[:80]!r}" if has_q else
             "NO -- reader cannot tell what is being asked"))
    print(f"    names why it is SURPRISING    : "
          + ("yes" if has_s else "NO -- reader cannot tell why the answer is news"))
    print(f"    has a TAKEAWAY section        : "
          + ("yes" if has_t else "NO -- reader cannot tell what to do with it"))
    if missing:
        print(f"    missing: {', '.join(missing)}")

    if long_ss:
        print(f"\n  LONG SENTENCES ({len(long_ss)} over {LONG_SENTENCE} words) -- split these:")
        for s in sorted(long_ss, key=lambda s: -len(s.split()))[:5]:
            print(f"    [{len(s.split())}w] {s[:120]}...")
    if hard:
        print(f"\n  LONG WORDS WITH SHORT EQUIVALENTS ({len(hard)}):")
        print("    " + ", ".join(f"{w} -> {r}" for w, r in hard[:12]))
    if tells:
        print(f"\n  AI / OPACITY TELLS ({len(tells)}):")
        print("    " + ", ".join(tells[:12]))
    return status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--quiet", action="store_true", help="only print problems")
    a = ap.parse_args()

    files = []
    for p in a.paths:
        files += sorted(glob.glob(os.path.join(p, "*.html"))) if os.path.isdir(p) else [p]

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for f in files:
        s = score(f, a.quiet)
        if s:
            counts[s] += 1
    print(f"\n{'='*72}")
    print(f"PASS {counts['PASS']}   WARN {counts['WARN']}   FAIL {counts['FAIL']}")
    # Non-zero only on FAIL, so a drifting draft warns without blocking the day.
    sys.exit(1 if counts["FAIL"] else 0)


if __name__ == "__main__":
    main()
