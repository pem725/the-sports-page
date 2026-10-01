#!/usr/bin/env python3
"""Generate the editorial board's budget sheet from live files.

    python3 scripts/build_budget.py
    python3 scripts/build_budget.py --print     # stdout, write nothing

THE EDITOR, 2026-10-01: "The editors are going to be online at different times
during the day and different weeks. So let's do something more flexible and
permanent."

That rules out anything a human has to remember to refresh. This runs in the
daily workflow beside refresh_about and refresh_odds, so the board's page is
rebuilt every publishing day from QUEUE_ORDER.txt and the queue files
themselves. NOTHING on it is typed by hand -- if the running order changes, the
page changes, and if nobody changes the order the page still re-renders with the
dates walked forward.

WHY A GENERATOR AND NOT A WRITTEN PAGE. newsroom.html was hand-written and had
not been touched since 2026-08-30 while the archive moved from 155 to 186. A
page that documents a moving thing has to be generated or it lies, and it lies
quietly, which is the expensive kind. Same lesson as about.html.

ON PRIVACY, SAID PLAINLY BECAUSE IT WILL BE ASSUMED OTHERWISE. GitHub Pages
serves static files and cannot authenticate anybody. This page is UNLISTED, not
private: it sits at an unguessable path, carries noindex, and is excluded in
robots.txt, so it will not be crawled or stumbled upon. Anyone holding the link
can open it. For a four-person family board that is the right trade; if it ever
needs to be genuinely private, that requires an auth layer in front of the
domain, not a cleverer filename.
"""
import argparse
import datetime
import html as H
import json
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
ORDER = REPO / "QUEUE_ORDER.txt"
# Unguessable path. Changing it invalidates every link already shared, so do not
# rotate it casually -- the whole point is that it gets sent round once.
SLUG = "board/k7q2-desk-9f4m"

DECAY_NOTE = {
    "hot": "numbers move daily &middot; publish within ~3 days or rewrite",
    "dated": "tied to a fixed event &middot; must run before it",
    "slow": "season-bound &middot; stable for about three weeks",
    "keeps": "methods or history &middot; runs any time",
}


def meta(path):
    t = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"<!-- PUBLISH-META(.*?)-->", t, re.S)
    d = {k: v.split("#")[0].strip()
         for k, v in re.findall(r"^\s*(\w+):\s*(.+)$", m.group(1), re.M)} if m else {}
    body = re.sub(r"<!--.*?-->", "", t, flags=re.S)

    def text(pat):
        x = re.search(pat, body, re.S)
        return H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x.group(1)))).strip() if x else ""

    # Deck extraction walks tag depth. A non-greedy match to the first closing
    # tag stops at a nested <span> and silently truncates -- it took two decks
    # down to a dozen characters before anyone noticed.
    deck = ""
    o = re.search(r'<(\w+)[^>]*class="deck"[^>]*>', body)
    if o:
        tag, pos, depth = o.group(1), o.end(), 1
        for mm in re.finditer(rf"</?{tag}\b[^>]*>", body[pos:]):
            depth += -1 if mm.group(0).startswith("</") else 1
            if depth == 0:
                deck = H.unescape(re.sub(r"\s+", " ", re.sub(
                    r"<[^>]+>", "", body[pos:pos + mm.start()]))).strip()
                break
    return dict(file=path.name, topic=d.get("topic", "?"), decay=d.get("decay", "?"),
                tags=[s.strip().split(":")[0] for s in d.get("tags", "").split(",") if s.strip()],
                hed=text(r'<h[12][^>]*class="hed"[^>]*>(.*?)</h[12]>') or path.stem,
                deck=deck)


def schedule(rows, start=None):
    """Walk the real calendar: Mon-Sat publish, Sunday is the Sunday Edition."""
    d = start or datetime.date.today()
    out = []
    for r in rows:
        while d.weekday() == 6:
            out.append(("sunday", d, None))
            d += datetime.timedelta(days=1)
        out.append(("slot", d, r))
        d += datetime.timedelta(days=1)
    return out


def esc(s):
    return H.escape(s, quote=False)


def render(items, published, built):
    slots = [x for x in items if x[0] == "slot"]
    last = slots[-1][1] if slots else built
    hot = sum(1 for _, _, r in slots if r["decay"] == "hot")
    keeps = sum(1 for _, _, r in slots if r["decay"] == "keeps")
    rows = []
    for kind, d, r in items:
        if kind == "sunday":
            rows.append(
                '    <div class="sunday">\n'
                f'      <div class="when">Sun {d.day}</div>\n'
                '      <p>Sunday Edition &mdash; the weekly scorecard runs instead. '
                'No regular issue, ever.</p>\n'
                '    </div>')
            continue
        chips = (f'<span class="chip topic">{esc(r["topic"])}</span>'
                 f'<span class="chip d-{esc(r["decay"])}">{esc(r["decay"])}</span>'
                 + "".join(f'<span class="chip">{esc(t)}</span>'
                           for t in r["tags"] if t.lower() != r["topic"].lower()))
        rows.append(
            f'    <div class="slot{" is-hot" if r["decay"]=="hot" else ""}">\n'
            f'      <div class="when"><b>{d.strftime("%a")} {d.day}</b>{d.strftime("%b")}</div>\n'
            '      <div>\n'
            f'        <p class="hed disp">{esc(r["hed"])}</p>\n'
            f'        <p class="deck">{esc(r["deck"])}</p>\n'
            f'        <div class="chips">{chips}</div>\n'
            '      </div>\n'
            '    </div>')
    legend = "".join(
        f'<div><span class="chip d-{k}">{k}</span> {v}</div>' for k, v in DECAY_NOTE.items())
    return TEMPLATE.format(
        rows="\n".join(rows), legend=legend, published=published,
        nslots=len(slots), hot=hot, keeps=keeps,
        through=last.strftime("%a %-d %b %Y"),
        built=built.strftime("%-d %b %Y"))


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="robots" content="noindex, nofollow, noarchive">
<title>The Sports Page &mdash; The Budget</title>
<style>
:root{{
  --ink:#1a1208; --paper:#f5f0e8; --ground:#e0d8c5; --rule:#c8b99a;
  --rust:#b83a1e; --steel:#2c4a6e; --gold:#9a7320; --muted:#6b5e4a;
  --card:#ede5d2; --shadow:0 6px 40px rgba(26,18,8,.18);
}}
@media (prefers-color-scheme:dark){{
  :root{{--ink:#ece2cf;--paper:#1d1810;--ground:#120e08;--rule:#453a28;
  --rust:#e07050;--steel:#7fa8d4;--gold:#d6a949;--muted:#9c8d75;
  --card:#262013;--shadow:0 6px 40px rgba(0,0,0,.5);}}
}}
:root[data-theme="dark"]{{--ink:#ece2cf;--paper:#1d1810;--ground:#120e08;--rule:#453a28;
  --rust:#e07050;--steel:#7fa8d4;--gold:#d6a949;--muted:#9c8d75;
  --card:#262013;--shadow:0 6px 40px rgba(0,0,0,.5);}}
:root[data-theme="light"]{{--ink:#1a1208;--paper:#f5f0e8;--ground:#e0d8c5;--rule:#c8b99a;
  --rust:#b83a1e;--steel:#2c4a6e;--gold:#9a7320;--muted:#6b5e4a;
  --card:#ede5d2;--shadow:0 6px 40px rgba(26,18,8,.18);}}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;padding:1.5rem 1rem 4rem;background:var(--ground);color:var(--ink);
  font-family:Georgia,'Times New Roman',serif;font-size:17px;line-height:1.68;
  -webkit-text-size-adjust:100%}}
.disp{{font-family:'Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,serif}}
.wrap{{max-width:920px;margin:0 auto}}
.mast{{text-align:center;border-top:4px solid var(--ink);padding-top:.5rem}}
.eyebrow{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.64rem;
  letter-spacing:.22em;text-transform:uppercase;color:var(--muted)}}
.mast h1{{font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
  font-size:clamp(2rem,6vw,3.1rem);font-weight:700;letter-spacing:.04em;
  text-transform:uppercase;line-height:1.08;margin:.15rem 0 .1rem;text-wrap:balance}}
.mast .tag{{font-style:italic;color:var(--muted);font-size:.95rem;margin:0}}
.rulebar{{display:flex;justify-content:space-between;gap:.5rem;flex-wrap:wrap;
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.63rem;letter-spacing:.1em;
  color:var(--muted);border-top:1px solid var(--ink);border-bottom:3px double var(--ink);
  padding:.35rem 0;margin-top:.45rem;font-variant-numeric:tabular-nums}}
.sheet{{background:var(--paper);border:1px solid var(--rule);box-shadow:var(--shadow);
  padding:2.2rem 2.4rem 2.6rem;margin-top:.9rem}}
@media(max-width:620px){{.sheet{{padding:1.4rem 1.2rem 1.8rem}}}}
.lede{{font-size:1.06rem;margin:0 0 1.6rem;max-width:62ch}}
.lede strong{{color:var(--rust)}}
h2.sh{{font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
  font-size:1.12rem;font-weight:700;text-transform:uppercase;letter-spacing:.055em;
  border-bottom:2px solid var(--rust);padding-bottom:.22rem;margin:2.4rem 0 .3rem;
  text-wrap:balance}}
h2.sh:first-of-type{{margin-top:.4rem}}
.shnote{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.63rem;
  letter-spacing:.09em;color:var(--muted);text-transform:uppercase;margin:0 0 1.1rem}}
.slot{{display:grid;grid-template-columns:5.4rem 1fr;gap:0 1.25rem;
  border-top:1px solid var(--rule);padding:.95rem 0}}
.slot:first-of-type{{border-top:none}}
.slot.is-hot{{border-left:3px solid var(--rust);padding-left:.8rem;margin-left:-.8rem}}
.when{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.7rem;
  letter-spacing:.04em;color:var(--muted);font-variant-numeric:tabular-nums;
  padding-top:.3rem;line-height:1.5}}
.when b{{display:block;color:var(--ink);font-weight:600;font-size:.76rem}}
.hed{{font-family:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;
  font-size:1.2rem;font-weight:700;line-height:1.28;margin:0 0 .3rem;text-wrap:balance}}
.deck{{font-size:.93rem;color:var(--muted);margin:0 0 .5rem;max-width:64ch;line-height:1.6}}
.chips{{display:flex;flex-wrap:wrap;gap:.35rem;align-items:center}}
.chip{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.59rem;
  letter-spacing:.11em;text-transform:uppercase;padding:.18rem .44rem;
  border:1px solid var(--rule);color:var(--muted);border-radius:2px}}
.chip.topic{{border-color:var(--steel);color:var(--steel);font-weight:600}}
.chip.d-hot{{border-color:var(--rust);color:var(--rust);font-weight:600}}
.chip.d-dated{{border-color:var(--gold);color:var(--gold);font-weight:600}}
.chip.d-slow{{border-color:var(--steel);color:var(--steel)}}
.chip.d-keeps{{border-color:var(--rule);color:var(--muted)}}
.sunday{{display:grid;grid-template-columns:5.4rem 1fr;gap:0 1.25rem;
  border-top:1px solid var(--rule);padding:.5rem 0;align-items:center}}
.sunday .when{{padding-top:0}}
.sunday p{{margin:0;font-size:.82rem;font-style:italic;color:var(--muted)}}
.legend{{display:grid;grid-template-columns:repeat(auto-fit,minmax(248px,1fr));gap:.45rem 1.1rem;
  margin:1rem 0 0;font-size:.82rem;color:var(--muted)}}
.legend .chip{{margin-right:.35rem}}
.test{{margin:0;padding:0;list-style:none;counter-reset:t}}
.test li{{counter-increment:t;position:relative;padding:.55rem 0 .55rem 2.3rem;
  border-top:1px solid var(--rule);font-size:.97rem}}
.test li:first-child{{border-top:none}}
.test li::before{{content:counter(t);position:absolute;left:0;top:.62rem;
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.72rem;font-weight:600;color:var(--rust)}}
.test em{{color:var(--muted)}}
.formula{{background:var(--card);border:1px solid var(--rule);padding:1rem 1.1rem;
  margin:1.1rem 0;overflow-x:auto}}
.formula code{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.78rem;
  color:var(--ink);white-space:pre;display:block;line-height:1.75}}
.formula .k{{color:var(--rust);font-weight:600}}
.send{{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:1px;
  background:var(--rule);border:1px solid var(--rule);margin:1.1rem 0 0}}
.send > div{{background:var(--paper);padding:1rem 1.1rem}}
.send h3{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.63rem;
  letter-spacing:.13em;text-transform:uppercase;color:var(--muted);margin:0 0 .4rem;font-weight:600}}
.send p{{margin:0;font-size:.92rem;line-height:1.6}}
a{{color:var(--rust);text-decoration:none;border-bottom:1px solid rgba(184,58,30,.38)}}
a:hover{{border-bottom-color:var(--rust)}}
a:focus-visible{{outline:2px solid var(--steel);outline-offset:3px;border-radius:1px}}
.board{{display:flex;flex-wrap:wrap;gap:.4rem;margin-top:.9rem}}
.board span{{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.68rem;
  letter-spacing:.09em;border:1px solid var(--rule);padding:.26rem .6rem;color:var(--muted)}}
.foot{{border-top:3px double var(--ink);margin-top:2.4rem;padding-top:.7rem;
  display:flex;justify-content:space-between;flex-wrap:wrap;gap:.4rem;
  font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.6rem;
  letter-spacing:.07em;color:var(--muted)}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important;transition:none!important}}}}
</style>
</head>
<body>
<div class="wrap">

  <header class="mast">
    <div class="eyebrow">For the Editorial Board &middot; Unlisted</div>
    <h1 class="disp">The Budget</h1>
    <p class="tag">What runs, when it runs, and what we still need</p>
    <div class="rulebar">
      <span>{published} issues published</span>
      <span>{nslots} slots scheduled</span>
      <span>Through {through}</span>
    </div>
  </header>

  <div class="sheet">

    <p class="lede">This is the running order, rebuilt automatically every publishing day &mdash;
    so whenever you open it, it is current. One issue a day, Monday through Saturday, and the
    Sunday Edition on Sundays, which means every piece competes with every other piece for a
    single slot. <strong>If you have an idea, it displaces something on this page.</strong>
    That is the whole reason you are looking at it.</p>

    <h2 class="sh">The Running Order</h2>
    <p class="shnote">{hot} hot &middot; {keeps} evergreen in reserve &middot; no two consecutive days share a topic</p>

{rows}

    <div class="legend">{legend}</div>

    <h2 class="sh">What Makes an Idea Run</h2>
    <p class="shnote">Three questions. It needs all three, not two.</p>

    <ol class="test">
      <li><strong>Is there a number in it, or could there be?</strong>
        <em>You do not need the number. You need to believe one exists.</em></li>
      <li><strong>Could it not be settled at the table?</strong>
        <em>If somebody can end the argument with their phone, it is a fact, not an issue.</em></li>
      <li><strong>Could a reasonable person be wrong about it?</strong>
        <em>This is the one that matters. If nobody holds the wrong belief, there is nothing to correct.</em></li>
    </ol>

    <p style="margin:1.4rem 0 0;font-size:.97rem">When several ideas clear the bar on the same day,
    this decides the order:</p>

    <div class="formula">
      <code><span class="k">NEWSINESS</span> = (GRIP / 10) &times; (0.35 TWIST + 0.25 CLOCK + 0.15 STACK + 0.25 CARRY)</code>
    </div>

    <p style="margin:0;font-size:.95rem;max-width:62ch"><strong>GRIP multiplies rather than adds,
    and that is the editorial position.</strong> This paper is statistics driven by sport, not sport
    driven by statistics. A Super Bowl with a dull number scores near nothing. A Tuesday game between
    two eliminated clubs with a shocking number can lead. Audience &mdash; STACK &mdash; carries the
    smallest weight on purpose.</p>

    <h2 class="sh">Send It</h2>
    <p class="shnote">Hand-written, in your own words. There is no form and none is wanted.</p>

    <div class="send">
      <div>
        <h3>By email</h3>
        <p><a href="mailto:ideas@thesportspage.net?subject=Idea%20for%20The%20Sports%20Page">ideas@thesportspage.net</a><br>
        Half an idea is fine. A question you lost an argument about is better.</p>
      </div>
      <div>
        <h3>What helps most</h3>
        <p>Where you saw it, and roughly when. If you are not sure where a number came from, write
        <em>unknown</em> and we will chase it.</p>
      </div>
      <div>
        <h3>One hard rule</h3>
        <p>An assistant may point you at a fact. It may never be the source of one. A missing number
        costs an hour; a wrong one costs us a headline.</p>
      </div>
    </div>

    <h2 class="sh">The Board</h2>
    <p class="shnote">Scores independently. Disagreement is where the rubric gets tuned.</p>
    <div class="board"><span>Sean</span><span>Tim</span><span>Patrick jr</span><span>Patrick</span></div>
    <p style="margin:1rem 0 0;font-size:.93rem;max-width:62ch;color:var(--muted)">A metric nobody can
    argue with is a metric nobody is using. If you think something on this page is the wrong call,
    that is the most useful thing you can send.</p>

    <div class="foot">
      <span>The Sports Page</span>
      <span>Rebuilt {built}</span>
      <span>Unlisted &middot; please do not forward</span>
    </div>

  </div>
</div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", action="store_true")
    a = ap.parse_args()

    order = [l.strip() for l in ORDER.read_text().split("\n") if l.strip()]
    rows = []
    for name in order:
        p = REPO / "queue" / name
        if p.exists() and not name.startswith("_"):
            rows.append(meta(p))
    if not rows:
        raise SystemExit("no queue files resolved from QUEUE_ORDER.txt -- refusing to "
                         "publish an empty budget")

    published = (REPO / "index.html").read_text(encoding="utf-8").count('class="issue-num"')
    today = datetime.date.today()
    page = render(schedule(rows, today), published, today)

    if a.show:
        print(page)
        return 0
    out = REPO / SLUG / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"  budget: {len(rows)} slots, {published} published -> /{SLUG}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
