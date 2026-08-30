#!/usr/bin/env python3
"""Generate newsroom.html — the editorial board's one page.

    python3 scripts/build_newsroom.py

Everything on it is read from live files, so it is never a document someone
forgot to update:

    data/story-candidates.json   what is under consideration, scored
    QUEUE_ORDER.txt + queue/     what is actually scheduled, with decay tags
    data/picks-ledger.json       the standing forecast test
    index.html                   issues published

The board is Tim, Sean and Patrick jr. The page exists so a disagreement can be
specific -- not "I'd run something else" but "your TWIST on that is a 4."
"""
import datetime, json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "newsroom.html")
W = {"twist": .35, "clock": .25, "stack": .15, "carry": .25}
DECAY_NOTE = {"hot": "days", "dated": "has a deadline", "slow": "weeks", "keeps": "any time"}


def read(p):
    return open(os.path.join(REPO, p), encoding="utf-8").read()


def gather():
    cands = json.loads(read("data/story-candidates.json"))["candidates"]
    for c in cands:
        c["score"] = round((c["grip"] / 10) * sum(W[k] * c[k] for k in W), 2)
    cands.sort(key=lambda c: -c["score"])
    order = [l.strip() for l in read("QUEUE_ORDER.txt").splitlines() if l.strip()]
    d = datetime.date.today() + datetime.timedelta(days=1)
    if d.weekday() == 6:
        d += datetime.timedelta(days=1)
    q = []
    for f in order:
        p = os.path.join(REPO, "queue", f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        g = lambda k: (re.search(rf"{k}:\s*([^\n#]+)", t) or [None, "?"])[1].strip()
        hed = re.search(r'class="hed">(.*?)</h2>', t, re.S)
        title = re.sub(r"<[^>]+>", "", hed.group(1)).strip() if hed else f
        q.append(dict(date=d, topic=g("topic"), decay=g("decay"), title=title, file=f))
        d += datetime.timedelta(days=1)
        if d.weekday() == 6:
            d += datetime.timedelta(days=1)
    led = json.loads(read("data/picks-ledger.json"))
    picks = [p for wk in led["weeks"].values() for p in wk["picks"]]
    done = [p for p in picks if p.get("correct") is not None]
    issues = read("index.html").count('class="issue-num"')
    return cands, q, len(picks), len(done), issues


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def build():
    cands, q, npicks, ndone, issues = gather()
    ready = [c for c in cands if c.get("answerable")]
    held = [c for c in cands if not c.get("answerable")]
    rows = "".join(
        f'<tr><td class="n">{i}</td><td class="sc">{c["score"]}</td>'
        f'<td><strong>{esc(c["title"])}</strong><div class="wy">{esc(c.get("why",""))}</div>'
        f'<div class="nm">the number: {esc(c.get("number",""))}</div></td>'
        f'<td class="g">{c["grip"]}</td><td>{c["twist"]}</td><td>{c["clock"]}</td>'
        f'<td>{c["stack"]}</td><td>{c["carry"]}</td></tr>'
        for i, c in enumerate(ready, 1))
    heldrows = "".join(
        f'<li><strong>{esc(c["title"])}</strong> <span class="sc2">would score {c["score"]}</span>'
        f'<div class="wy">held: {esc(c.get("held",""))}</div></li>' for c in held)
    qrows = "".join(
        f'<tr><td class="dt">{x["date"]:%a %b %-d}</td><td class="tp">{x["topic"]}</td>'
        f'<td class="dc">{x["decay"]}<span class="dn"> &middot; {DECAY_NOTE.get(x["decay"],"")}</span></td>'
        f'<td>{esc(x["title"])}</td></tr>' for x in q)
    keeps = sum(1 for x in q if x["decay"] == "keeps")
    gap = issues - 0
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>The Sports Page &mdash; The Newsroom</title>
<meta name="description" content="How The Sports Page decides what to run: the NEWSINESS metric, the current story pile, the queue, and the open questions. For the editorial board.">
<meta name="robots" content="noindex">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--gold:#c9962a;--muted:#6b5e4a;--div:#c8b99a;--card:#ede5d2;--green:#2a6e3f}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif;font-size:15px;line-height:1.65;padding:1.4rem 1rem 3rem}}
.masthead{{max-width:900px;margin:0 auto;text-align:center;border-top:4px solid var(--ink);padding:.5rem 0 0}}
.kicker{{font-family:'Roboto Mono',monospace;font-size:.66rem;letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}}
.title{{font-family:'Playfair Display',serif;font-size:clamp(1.5rem,4vw,2.4rem);font-weight:700;letter-spacing:.04em;text-transform:uppercase;margin:.1rem 0}}
.title a{{color:inherit;text-decoration:none}}
.tagline{{font-family:'Playfair Display',serif;font-style:italic;font-size:.9rem;color:var(--muted)}}
.datebar{{display:flex;justify-content:space-between;font-family:'Roboto Mono',monospace;font-size:.62rem;color:var(--muted);letter-spacing:.1em;border-top:1px solid var(--ink);border-bottom:3px double var(--ink);padding:.3rem 0;margin-top:.3rem}}
.paper{{max-width:900px;margin:.8rem auto 0;background:var(--cream);padding:2rem 2.2rem 2.4rem;box-shadow:0 6px 40px rgba(0,0,0,.2);border:1px solid var(--div)}}
@media(max-width:620px){{.paper{{padding:1.2rem 1rem}}}}
h1{{font-family:'Playfair Display',serif;font-size:clamp(1.6rem,4vw,2.2rem);font-weight:900;line-height:1.15;margin-bottom:.3rem}}
h1 em{{color:var(--rust);font-style:italic}}
.deck{{font-style:italic;color:var(--muted);border-left:3px solid var(--rust);padding-left:.85rem;margin:.6rem 0 1.4rem;line-height:1.5}}
h2{{font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:700;text-transform:uppercase;letter-spacing:.05em;border-bottom:2px solid var(--rust);padding-bottom:.2rem;margin:1.9rem 0 .8rem}}
p{{margin-bottom:.75rem}}
.eq{{font-family:'Roboto Mono',monospace;font-size:.82rem;background:var(--card);border:1px solid var(--div);padding:.7rem .9rem;margin:.7rem 0;overflow-x:auto;white-space:nowrap}}
table{{width:100%;border-collapse:collapse;font-size:.84rem;margin:.5rem 0}}
th{{font-family:'Roboto Mono',monospace;font-size:.6rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);text-align:right;padding:.3rem .35rem;border-bottom:1px solid var(--div)}}
th:nth-child(3){{text-align:left}}
td{{padding:.45rem .35rem;border-bottom:1px solid var(--div);vertical-align:top;text-align:right}}
td:nth-child(3),td:nth-child(4){{text-align:left}}
.n{{color:var(--muted);font-family:'Roboto Mono',monospace}}
.sc{{font-family:'Playfair Display',serif;font-size:1.15rem;font-weight:900;color:var(--rust)}}
.sc2{{font-family:'Roboto Mono',monospace;font-size:.72rem;color:var(--muted)}}
.g{{font-weight:700;color:var(--steel)}}
.wy{{font-size:.78rem;color:var(--muted);line-height:1.45;margin-top:.15rem}}
.nm{{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--steel);margin-top:.15rem}}
.dt{{font-family:'Roboto Mono',monospace;font-size:.74rem;text-align:left !important;white-space:nowrap}}
.tp{{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--rust);text-align:left !important}}
.dc{{font-family:'Roboto Mono',monospace;font-size:.7rem;text-align:left !important}}
.dn{{color:var(--muted)}}
ul{{margin:.4rem 0 .8rem 1.1rem}} li{{margin-bottom:.5rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--div);border:1px solid var(--div);margin:1rem 0}}
.cell{{background:var(--card);padding:.8rem;text-align:center}}
.cell .v{{font-family:'Playfair Display',serif;font-size:1.8rem;font-weight:900;line-height:1}}
.cell .l{{font-family:'Roboto Mono',monospace;font-size:.58rem;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);margin-top:.2rem}}
.ask{{border:2px solid var(--steel);background:var(--card);padding:1rem 1.2rem;margin:1.4rem 0}}
.footer{{display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem;font-family:'Roboto Mono',monospace;font-size:.6rem;color:var(--muted);letter-spacing:.08em;border-top:3px double var(--ink);margin-top:2rem;padding-top:.7rem}}
.footer a{{color:var(--rust);text-decoration:none}}
</style>
</head>
<body>
<div class="masthead">
  <div class="kicker">For the Editorial Board &middot; Generated {datetime.date.today():%-d %B %Y}</div>
  <div class="title"><a href="https://thesportspage.net/">The Sports Page</a></div>
  <div class="tagline">Making the numbers mean something since the first pitch</div>
  <div class="datebar"><span>The Newsroom</span><span>{issues} issues published</span><span>Tim &middot; Sean &middot; Patrick jr</span></div>
</div>
<div class="paper">
  <h1>How We Decide What Runs. <em>And What We Are Arguing About.</em></h1>
  <div class="deck">One issue a day means every story competes with every other. This page is the argument, written down: what is in the pile, what it scored, what is already scheduled, and where we need you.</div>

  <div class="grid">
    <div class="cell"><div class="v">{issues}</div><div class="l">Issues published</div></div>
    <div class="cell"><div class="v">{len(q)}</div><div class="l">Days of queue</div></div>
    <div class="cell"><div class="v">{len(cands)}</div><div class="l">Stories under consideration</div></div>
    <div class="cell"><div class="v">{ndone}/{npicks}</div><div class="l">Forecasts graded so far</div></div>
  </div>

  <h2>The metric</h2>
  <p>Most sports desks pick the biggest event and hunt for numbers inside it. We do the reverse: pick the most interesting <strong>number</strong>, then explain the sport around it. <em>Stats driven by sports, not sports driven by stats.</em></p>
  <div class="eq">NEWSINESS = (GRIP &divide; 10) &times; (0.35 TWIST + 0.25 CLOCK + 0.15 STACK + 0.25 CARRY)</div>
  <p><strong>GRIP multiplies rather than adds.</strong> That is the editorial position, not a modelling convenience. A story with no number scores zero however good it sounds.</p>
  <ul>
    <li><strong>GRIP</strong> &mdash; the number. Ours? Defensible? Does it have an interval? A broadcast graphic is a 2; computed from primary data, verified three ways, with a stated limit, is a 10.</li>
    <li><strong>TWIST</strong> &mdash; distance from what a reasonable fan expects. The best have a trap: an obvious answer that is wrong.</li>
    <li><strong>CLOCK</strong> &mdash; what running it today buys over running it next month.</li>
    <li><strong>STACK</strong> &mdash; audience, on the paper-stack scale. One page is a thousand plausible readers; a Super Bowl is about fourteen trees. <em>Deliberately the smallest weight.</em></li>
    <li><strong>CARRY</strong> &mdash; does the lesson survive outside sport? &ldquo;A deficit is a fact, superiority is a rate&rdquo; carries. &ldquo;The Rays are lucky&rdquo; does not.</li>
  </ul>
  <p><strong>Answerability is a gate, not a term.</strong> If the data cannot settle it, the story is held rather than ranked &mdash; however well it scores.</p>

  <h2>The pile, ranked</h2>
  <table>
    <tr><th></th><th>score</th><th>story</th><th>grip</th><th>twist</th><th>clock</th><th>stack</th><th>carry</th></tr>
    {rows}
  </table>
  <p style="font-size:.82rem;color:var(--muted)"><strong>Held &mdash; good stories the data cannot settle yet:</strong></p>
  <ul style="font-size:.86rem">{heldrows}</ul>

  <h2>What is already scheduled</h2>
  <table>{qrows}</table>
  <p style="font-size:.82rem;color:var(--muted)">Decay tags govern the order. <strong>{keeps} evergreen pieces</strong> are banked as buffer &mdash; that is what lets a breaking story take tomorrow&rsquo;s slot without leaving a hole.</p>

  <div class="ask">
    <h2 style="margin-top:0">Where we actually need you</h2>
    <ul>
      <li><strong>Score the pile yourselves.</strong> Run the rubric and tell us where we are wrong &mdash; not &ldquo;I&rsquo;d run something else&rdquo; but &ldquo;your TWIST on that is a 4.&rdquo; A metric nobody argues with is a metric nobody is using, and the disagreements are how the weights get tuned.</li>
      <li><strong>Bring questions, not topics.</strong> The best issues this year came from someone asking a question they could not settle at the table. Gene&rsquo;s produced a concept primer and an issue with his name on it.</li>
      <li><strong>Tell us when a piece was boring.</strong> Nobody reports this and it is the most useful thing you can say.</li>
    </ul>
  </div>

  <h2>The open questions</h2>
  <ul>
    <li><strong>Readership.</strong> The target is one reader per issue published &mdash; {issues} today, and roughly a thousand before we hang a shingle. We have no weekly tracker for this yet; it is the next thing to build.</li>
    <li><strong>Our own calibration.</strong> We keep telling readers a thing is 71% likely. The picks ledger will eventually say how often those happened. {ndone} of {npicks} graded so far; it needs 25+ before it can speak.</li>
    <li><strong>Publishing the rejects.</strong> This page shows what we passed over. That record should itself become an issue &mdash; readers seeing the selection, not just the selected.</li>
    <li><strong>The Stack&rsquo;s anchors.</strong> The audience scale is built but its readership figures are illustrative, and every one must be verified three ways before it appears in an issue.</li>
  </ul>

  <div class="footer">
    <span>The Sports Page &middot; The Newsroom &middot; regenerated from live files</span>
    <span><a href="https://thesportspage.net/">&larr; The Archive</a> &middot; <a href="https://thesportspage.net/ask.html">Ask us something</a></span>
  </div>
</div>
</body>
</html>
"""


if __name__ == "__main__":
    open(OUT, "w", encoding="utf-8").write(build())
    print(f"  wrote newsroom.html ({os.path.getsize(OUT):,} bytes)")
