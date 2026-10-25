#!/usr/bin/env python3
"""Does the archive already answer this? The AI box shortlists, a human decides.

Vetting step 2 of "A Reader Asks" (CLAUDE.md): grep published/ before writing
anything, because most questions are already answered and a same-day link is a
good outcome. Grep finds words; it misses the issue that answers the question in
different words. This builds a one-line card per published page (its own
headline + deck) and asks the local model which cards plausibly answer the
question. It returns slugs and a reason; it never answers the question itself.

LAN-only desk tool (see cold_read.py). The shortlist is a lead: open each page
and check before telling a reader "we covered this."

Usage:
  python3 scripts/archive_match.py "Do byes help teams?"
  python3 scripts/archive_match.py --file questions.txt      # one per line
"""
import argparse, html, json, os, re, urllib.request

HOST = os.environ.get("AIBOX", "http://192.168.0.65:11434")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cards():
    """One card per published page: its own headline and deck. Read from the
    pages, not index.html, whose newer entries use different markup."""
    out = []
    pub = os.path.join(REPO, "published")
    for f in sorted(os.listdir(pub)):
        if not f.endswith(".html"):
            continue
        s = open(os.path.join(pub, f), encoding="utf-8").read()
        hed = re.search(r'(?s)<h[12] class="hed">(.*?)</h[12]>', s)
        deck = re.search(r'(?s)<div class="deck">(.*?)</div>', s)
        num = re.search(r'Issue No\.\s*(\d+)|Vol\. I, No\.\s*(\d+)', s)
        clean = lambda x: html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?s)<svg.*?</svg>", "", x.group(1)))).strip() if x else ""
        n = next((g for g in num.groups() if g), "?") if num else "?"
        out.append(dict(n=n, slug=f, text=re.sub(r"\s+", " ", f"{clean(hed)} — {clean(deck)}")[:400]))
    return out


def ask(question, cs, model="gpt-oss:20b"):
    listing = "\n".join(f"[{c['slug']}] {c['text']}" for c in cs)
    prompt = ("Below is a list of published newsletter issues, one per line, each with its slug in brackets.\n"
              "A reader asked a question. Pick AT MOST 5 issues whose headline or summary plausibly answers it, "
              "fully or partly. Use only the list; do not answer the question yourself. If none fit, return [].\n"
              'Reply JSON: {"matches":[{"slug":"...","fit":"full|partial","why":"one short sentence"}]}\n\n'
              f"QUESTION: {question}\n\nISSUES:\n{listing}")
    payload = {"model": model, "stream": False, "format": "json", "think": "low",
               "options": {"temperature": 0.1, "num_ctx": 32768},
               "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(f"{HOST}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(json.load(r)["message"]["content"]).get("matches", [])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("question", nargs="?")
    ap.add_argument("--file")
    a = ap.parse_args()
    qs = [l.strip() for l in open(a.file) if l.strip()] if a.file else [a.question]
    cs = cards(); known = {c["slug"]: c for c in cs}
    for q in qs:
        print("=" * 72); print("Q:", q)
        for m in ask(q, cs):
            c = known.get(m.get("slug"))
            if not c:
                continue                      # the model named a slug that does not exist; drop it
            print(f"  #{c['n']:>4} {m.get('fit','?'):7s} {c['slug']}\n         {m.get('why','')}")
    print("\nShortlist only. Open each page before telling a reader it is answered.")


if __name__ == "__main__":
    main()
