#!/usr/bin/env python3
"""Build a public web page for a talk from its slide deck.

    python3 scripts/build_talk_page.py talks/gmu-2026-11-04

Reads TALK/src/deck.json and TALK/src/slides/*.html (the 1920x1080 slide
sections authored for the deck) and writes TALK/index.html: every slide scaled
to the page width, with what was said beneath it.

Speaker notes carry stage directions meant only for the speaker ("Move on").
PUBLIC_NOTES below overrides a slide's note for the public page; None drops
the note. Deck-only constructs are translated: <x-shape> arrows get CSS, and
uploaded deck images (/_blob/<id>) map to the site's own OG cards.

Each slide reached on screen sends one GoatCounter event (talk/<slug>/NN), so
the drop-off from slide to slide shows how far visitors actually read.
"""
import html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

BLOBS = {
    "13ec0dd39da2d34aba14ad446da416ed": "../../assets/og/001-skenes-era.png",
    "6f87b555bcd4497800f892be2ed227fd": "../../assets/og/190-every-program.png",
    "a73ef7fec714086b975afec3bca72380": "../../assets/og/182-rays-out-of-nowhere.png",
    "e79a5d71844ff6e0a8a403da3a9a1717": "../../assets/og/188-nd-navy.png",
}

# Stage directions out; the classroom description stays in the room only.
STRIP = [
    "Start cold, no introduction. ",
    " Keep this point short. The room already agrees with it; you are just naming it.",
    " Move on; don't teach the model.",
    "Here is the situation, and I describe it without judgment. Fewer people come in, fewer ask questions, and fewer read the text, and the text is essential. I made videos because that was the only way the material was reaching anyone. ",
]
PUBLIC_NOTES = {
    "cover": None,
    "ask": "We closed by taking one argument from the room and framing it live: what is the question, what number would answer it, what would a reasonable person expect, and what would they take home. If you have one, send it. If it is a good one, it becomes an issue, and you get your first name in it.",
}

SLIDE_CSS = """
.frame{position:relative;width:100%;aspect-ratio:16/9;overflow:hidden;background:#e0d8c5;box-shadow:0 1px 4px rgba(0,0,0,.18)}
.frame>section{position:absolute;left:0;top:0;width:1920px;height:1080px;box-sizing:border-box;overflow:hidden;transform-origin:0 0}
.frame section *{box-sizing:border-box;margin:0}
.frame section aside{display:none}
x-shape{display:block}
x-shape[kind=arrow-right]{clip-path:polygon(0 35%,60% 35%,60% 0,100% 50%,60% 100%,60% 65%,0 65%)}
x-shape[kind=arrow-down]{clip-path:polygon(35% 0,65% 0,65% 60%,100% 60%,50% 100%,0 60%,35% 60%)}
"""


def note_for(sid, raw):
    if sid in PUBLIC_NOTES:
        return PUBLIC_NOTES[sid]
    for s in STRIP:
        raw = raw.replace(s, "")
    return raw.strip() or None


def main(talk):
    talk = (ROOT / talk).resolve()
    deck = json.loads((talk / "src/deck.json").read_text())
    meta = json.loads((talk / "talk.json").read_text())
    starts = {v["start"]: v["description"] for v in deck["sections"].values()}
    blocks = []
    for n, sid in enumerate(deck["order"], 1):
        sec = (talk / f"src/slides/{sid}.html").read_text()
        m = re.search(r"<aside>(.*?)</aside>", sec, re.S)
        note = note_for(sid, html.unescape(re.sub(r"<[^>]+>", "", m.group(1)))) if m else None
        for blob, path in BLOBS.items():
            sec = sec.replace(f"/_blob/{blob}", path)
        if sid in starts:
            blocks.append(f'<h2 class="part">{html.escape(starts[sid])}</h2>')
        said = f'<p class="said"><span>What I said</span> {html.escape(note)}</p>' if note else ""
        blocks.append(f'<figure class="slide" data-n="{n:02d}"><div class="frame">{sec}</div>{said}</figure>')

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(meta['title'])} &middot; The Sports Page</title>
<meta name="description" content="{html.escape(meta['description'])}">
<meta property="og:title" content="{html.escape(meta['title'])}">
<meta property="og:description" content="{html.escape(meta['description'])}">
<meta property="og:image" content="https://thesportspage.net/assets/banner@2x.png">
<link rel="icon" href="../../assets/favicon.png">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&family=Roboto+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--ink:#1a1208;--cream:#f5f0e8;--aged:#e0d8c5;--rust:#b83a1e;--steel:#2c4a6e;--gold:#c9962a;--muted:#6b5e4a}}
body{{margin:0;background:var(--aged);color:var(--ink);font-family:'Libre Baskerville',Georgia,serif}}
.paper{{max-width:1040px;margin:0 auto;background:var(--cream);padding:2rem 1.5rem 3rem}}
.title{{font-family:'Playfair Display',Georgia,serif;font-weight:900;font-size:1.3rem;text-align:center}}
.kicker{{font-family:'Roboto Mono',monospace;font-size:.75rem;letter-spacing:.15em;text-transform:uppercase;color:var(--rust);text-align:center;margin:1.6rem 0 .4rem}}
h1{{font-family:'Playfair Display',Georgia,serif;font-size:2.4rem;line-height:1.1;text-align:center;margin:.2rem 0 .6rem}}
.byline{{font-family:'Roboto Mono',monospace;font-size:.8rem;color:var(--muted);text-align:center;margin-bottom:1.6rem}}
.lede{{font-size:1.05rem;line-height:1.65;max-width:42rem;margin:0 auto 2rem}}
.part{{font-family:'Roboto Mono',monospace;font-size:.85rem;letter-spacing:.1em;text-transform:uppercase;color:var(--rust);border-top:2px solid var(--ink);padding-top:.7rem;margin:2.6rem 0 1rem}}
.slide{{margin:0 0 2rem}}
.said{{font-size:.95rem;line-height:1.65;margin:.8rem 0 0;color:#3a2f20}}
.said span{{font-family:'Roboto Mono',monospace;font-size:.7rem;letter-spacing:.1em;text-transform:uppercase;color:var(--steel);margin-right:.4rem}}
.cta{{background:var(--ink);color:var(--cream);padding:1.6rem;margin-top:2.6rem;line-height:1.6}}
.cta h2{{font-family:'Playfair Display',Georgia,serif;margin:0 0 .6rem;color:var(--gold)}}
.cta a{{color:var(--gold)}}
.foot{{font-family:'Roboto Mono',monospace;font-size:.75rem;color:var(--muted);text-align:center;margin-top:2rem}}
.foot a{{color:inherit}}
@media (max-width:600px){{h1{{font-size:1.8rem}}.paper{{padding:1.2rem 1rem 2rem}}}}
{SLIDE_CSS}
</style>
<script src="../../assets/sitenav.js" defer></script>
</head>
<body>
<div class="paper">
<div class="title"><a href="https://thesportspage.net/" style="color:inherit;text-decoration:none">The Sports Page</a></div>
<p class="kicker">{html.escape(meta['kicker'])}</p>
<h1>{html.escape(meta['title'])}</h1>
<p class="byline">{html.escape(meta['byline'])}</p>
<p class="lede">{meta['lede']}</p>
{''.join(blocks)}
<div class="cta">
<h2>Were you there? Pull up a chair.</h2>
<p>{meta['cta']}</p>
</div>
<p class="foot"><a href="https://thesportspage.net/">thesportspage.net</a> &middot; <a href="https://thesportspage.net/engine.html">The Engine</a></p>
</div>
<script>
/* Fit each 1920x1080 slide to its frame. */
function fit(){{document.querySelectorAll('.frame').forEach(function(f){{
  f.firstElementChild.style.transform='scale('+(f.clientWidth/1920)+')';}});}}
addEventListener('resize',fit);addEventListener('load',fit);fit();
/* One GoatCounter event per slide reached: the drop-off is who stayed. */
var seen={{}};
function send(n,tries){{  /* count.js loads async; wait for it */
  if(window.goatcounter&&window.goatcounter.count){{
    window.goatcounter.count({{path:'talk/{meta['slug']}/'+n,title:'{meta['slug']} slide '+n,event:true}});
  }} else if(tries<30) setTimeout(function(){{send(n,tries+1);}},500);
}}
var io=new IntersectionObserver(function(es){{es.forEach(function(e){{
  var n=e.target.dataset.n;
  if(!e.isIntersecting||seen[n]) return; seen[n]=1;
  send(n,0);
}});}},{{threshold:.6}});
document.querySelectorAll('.slide').forEach(function(s){{io.observe(s);}});
window.goatcounter = window.goatcounter || {{}};
window.goatcounter.path = function (p) {{
  return (p.replace(/^\\/the-sports-page/, '').replace(/\\/index\\.html$/, '/')) || '/';
}};
</script>
<script data-goatcounter="https://thesportspage.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
</body>
</html>
"""
    (talk / "index.html").write_text(page)
    print(f"wrote {talk.relative_to(ROOT)}/index.html: {len(deck['order'])} slides")


if __name__ == "__main__":
    main(sys.argv[1])
