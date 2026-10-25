#!/usr/bin/env python3
"""Cold read: a local model reads a queued issue the way a stranger would.

check_readability.py says in its own docstring what it cannot do: it detects that
a question, an answer and a takeaway are PRESENT, not whether a reader comes away
with them. This fills that gap with a reader, not a checker.

The model on the AI box (docs/ai-box.md in NASerator; Ollama, LAN only) gets the
article text and nothing else, and reports back what it understood:

  - the question the piece answers
  - the answer, with its number
  - what it expected before reading, and whether the piece changed that
  - the sentences where it got lost

Then YOU compare its answers to what the piece meant to say. A reader that
recovers the wrong number, or no number, has found a real fault no score can.

Two rules, both binding:

  1. The model is a reader, never a source. Nothing it says goes into a piece as
     a fact, and it is told so. If it "corrects" a number, ignore the correction
     and ask why the sentence was misreadable.
  2. Local only. The box is not reachable from GitHub Actions, so this never runs
     in the 4:30am publish; it is a desk tool, run before queueing.

Usage:
  python3 scripts/cold_read.py queue/NNN-slug.html [more files]
  python3 scripts/cold_read.py --model gemma3:27b queue/NNN-slug.html
  AIBOX=http://192.168.0.65:11434 is the default host.
"""
import argparse, html, json, os, re, sys, time, urllib.request

HOST = os.environ.get("AIBOX", "http://192.168.0.65:11434")
DEFAULT_MODEL = "gpt-oss:20b"

PROMPT = """You are a curious sports fan with no statistics training, reading a short newspaper article once, quickly.
You are a READER, not a fact-checker. Do not add facts, do not correct numbers, do not use outside knowledge.
Report only what YOU took away from the text, in plain words.

Reply with JSON only, these keys:
  "question": the one question the article answers, in your own words, ending with "?"
  "answer": the article's answer in one sentence, including the key number exactly as you understood it
  "expected_before": what you would have guessed before reading
  "surprised": true or false, and "why" in one short sentence
  "takeaway": what you could now do or notice that you could not before
  "lost_me": up to 3 short quotes (copied exactly) where you got confused or had to reread; [] if none
  "clarity": 1-5, how easy the main point was to get

ARTICLE:
"""


def article_text(path):
    """Headline, deck and body prose only: no CSS, scripts, chart internals,
    share panel or footer furniture, which a reader skims past anyway."""
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"(?s)<!--.*?-->|<style.*?</style>|<script.*?</script>|<svg.*?</svg>", " ", s)
    m = re.search(r'(?s)<div id="main-content" class="paper">(.*?)(?:<div class="box">|Argued about something)', s)
    body = m.group(1) if m else s
    body = re.sub(r"(?s)<figcaption.*?</figcaption>", " ", body)
    body = re.sub(r"</(p|h1|h2|div)>", "\n", body)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", text)).strip()


def ask(model, text, timeout=300):
    payload = {"model": model, "stream": False, "format": "json",
               "options": {"temperature": 0.2, "num_ctx": 16384},
               "messages": [{"role": "user", "content": PROMPT + text}]}
    if model.startswith("gpt-oss"):
        payload["think"] = "low"
    req = urllib.request.Request(f"{HOST}/api/chat", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        out = json.load(r)
    return json.loads(out["message"]["content"]), time.time() - t0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--json", action="store_true", help="raw JSON per file")
    a = ap.parse_args()
    try:
        urllib.request.urlopen(f"{HOST}/api/tags", timeout=5)
    except OSError as e:
        sys.exit(f"AI box not reachable at {HOST} ({e}). This is a LAN-only desk tool.")
    for f in a.files:
        text = article_text(f)
        try:
            r, secs = ask(a.model, text)
        except (OSError, ValueError, KeyError) as e:
            print(f"\n{f}: cold read failed ({type(e).__name__}: {e})"); continue
        if a.json:
            print(json.dumps({"file": f, **r}, indent=1)); continue
        print("=" * 72)
        print(f"{os.path.basename(f)}   [{a.model}, {secs:.0f}s, {len(text.split())} words read]")
        print(f"  QUESTION  {r.get('question', '-')}")
        print(f"  ANSWER    {r.get('answer', '-')}")
        print(f"  EXPECTED  {r.get('expected_before', '-')}")
        sur, why = r.get("surprised", "-"), r.get("why", "")
        if isinstance(sur, dict):            # some models nest it: {"true": false, "why": ...}
            why = sur.get("why", why); sur = next((v for k, v in sur.items() if k != "why"), "-")
        print(f"  SURPRISED {sur}  {why}")
        print(f"  TAKEAWAY  {r.get('takeaway', '-')}")
        print(f"  CLARITY   {r.get('clarity', '-')}/5")
        for q in r.get("lost_me") or []:
            print(f"  LOST ME   \"{q}\"")
    print("\nThe model is a reader, not a source: compare its answers to what the piece meant; never copy a fact from it.")


if __name__ == "__main__":
    main()
