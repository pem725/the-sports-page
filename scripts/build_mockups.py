#!/usr/bin/env python3
"""Flat-lay garment mockups at TRUE relative scale.

Size-L measurements in mm: 560 chest, 780 across the sleeves, 720 body. The
artwork is composited at its actual millimetre size, so what you see is what
lands on the garment. A mockup that flatters the artwork is worse than none --
logos always look bigger in your head than they do on a chest.
"""
import os, sys, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cairosvg
from PIL import Image, ImageDraw
import build_merch as B

BODY_W, TOTAL_W, BODY_L = 560, 780, 720
PAD = 70
W = TOTAL_W + PAD*2
H = BODY_L + PAD*2 + 70
BX = PAD + (TOTAL_W-BODY_W)/2
TOP = PAD + 60
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = os.path.join(REPO, "merch")
OUT = os.path.join(M, "mockups")


def garment(kind, fabric, stitch, back=False):
    L, R = BX, BX+BODY_W
    nw = 96 if kind == "tee" else 74
    cx = BX + BODY_W/2
    sl_out, sl_dn, sl_in = PAD, 210, 165
    dip = 34 if back else 74                      # backs have a shallower neck
    neck = (f'M{cx-nw},{TOP} Q{cx},{TOP+dip} {cx+nw},{TOP}' if kind == "tee"
            else f'M{cx-nw},{TOP} L{cx-nw},{TOP+22} L{cx+nw},{TOP+22} L{cx+nw},{TOP}')
    body = (f'M{cx-nw},{TOP} L{L+40},{TOP+20} '
            f'L{sl_out},{TOP+96} L{sl_out+58},{TOP+sl_dn} L{L+34},{TOP+sl_in} '
            f'L{L+18},{TOP+BODY_L} L{R-18},{TOP+BODY_L} '
            f'L{R-34},{TOP+sl_in} L{PAD+TOTAL_W-58},{TOP+sl_dn} L{PAD+TOTAL_W},{TOP+96} '
            f'L{R-40},{TOP+20} L{cx+nw},{TOP} Z')
    out = [f'<path d="{body}" fill="{fabric}" stroke="{stitch}" stroke-width="2.5" stroke-linejoin="round"/>',
           f'<path d="{neck}" fill="none" stroke="{stitch}" stroke-width="7"/>']
    if kind == "polo" and not back:
        out.append(f'<path d="M{cx-nw},{TOP+22} L{cx-14},{TOP+150} L{cx},{TOP+118} '
                   f'L{cx+14},{TOP+150} L{cx+nw},{TOP+22}" fill="{fabric}" stroke="{stitch}" '
                   f'stroke-width="2.5" stroke-linejoin="round"/>')
        out.append(f'<line x1="{cx}" y1="{TOP+118}" x2="{cx}" y2="{TOP+232}" stroke="{stitch}" stroke-width="2.5"/>')
        for yy in (150, 200):
            out.append(f'<circle cx="{cx}" cy="{TOP+yy}" r="5.5" fill="none" stroke="{stitch}" stroke-width="2"/>')
    elif kind == "polo" and back:
        out.append(f'<path d="M{cx-nw},{TOP+22} L{cx-nw},{TOP+40} L{cx+nw},{TOP+40} L{cx+nw},{TOP+22} Z" '
                   f'fill="{fabric}" stroke="{stitch}" stroke-width="2.5"/>')
    out.append(f'<line x1="{sl_out}" y1="{TOP+96}" x2="{sl_out+58}" y2="{TOP+sl_dn}" stroke="{stitch}" stroke-width="5"/>')
    out.append(f'<line x1="{PAD+TOTAL_W}" y1="{TOP+96}" x2="{PAD+TOTAL_W-58}" y2="{TOP+sl_dn}" stroke="{stitch}" stroke-width="5"/>')
    out.append(f'<line x1="{L+18}" y1="{TOP+BODY_L-26}" x2="{R-18}" y2="{TOP+BODY_L-26}" stroke="{stitch}" stroke-width="2" opacity=".55"/>')
    return "\n".join(out)


def rsvg(t, px):
    return Image.open(io.BytesIO(cairosvg.svg2png(bytestring=t.encode(), output_width=px))).convert("RGBA")


def build(kind, fabric, stitch, art, art_mm, xy, label, out, back=False, px=880,
          center=True):
    """xy is (centre_x, top_y) in mm when center=True.

    Placement is measured from the artwork's INK bounds, not its canvas. Several
    lockups are not centred inside their own SVG box -- the stacked masthead sits
    right of centre because the S hangs off the wordmark -- so compositing by
    canvas put it visibly off-centre on the back of the shirt.
    """
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'<rect width="{W}" height="{H}" fill="#ddd6c6"/>{garment(kind,fabric,stitch,back)}</svg>')
    base = rsvg(doc, px); sc = px / W
    if art:
        a = rsvg(open(os.path.join(M, art)).read(), max(int(art_mm*sc), 1))
        bb = a.getbbox()                      # ink bounds within the art canvas
        if center and bb:
            x = int(xy[0]*sc) - (bb[0] + bb[2]) // 2
            y = int(xy[1]*sc) - bb[1]
        else:
            x, y = int(xy[0]*sc), int(xy[1]*sc)
        base.alpha_composite(a, (x, y))
    ImageDraw.Draw(base).text((14, 12), label, fill=(70, 60, 46))
    os.makedirs(OUT, exist_ok=True)
    base.save(os.path.join(OUT, out)); print("  ", out)


CX = BX + BODY_W/2
CREAM_F, CREAM_S = "#f2ece0", "#c3b9a6"
NAVY_F,  NAVY_S  = "#16224a", "#33436f"

def main():
    # POLO -- embroidered badge, left chest, unchanged
    build("polo", NAVY_F, NAVY_S, "polo-01-badge-reversed.svg", 82, (BX+153, TOP+215),
          "POLO  navy  ·  EMBROIDERED badge 82mm (3.25in) left chest", "polo-navy.png")
    build("polo", CREAM_F, CREAM_S, "polo-01-badge.svg", 82, (BX+153, TOP+215),
          "POLO  cream  ·  EMBROIDERED badge 82mm (3.25in) left chest", "polo-cream.png")
    # TEE -- badge + domain on the front, masthead on the back
    for tag, fab, st, front, back_art in (
            ("cream", CREAM_F, CREAM_S, "tee-front-badge-url.svg", "tee-01-masthead.svg"),
            ("navy",  NAVY_F,  NAVY_S,  "tee-front-badge-url-reversed.svg", "tee-01-masthead-reversed.svg")):
        build("tee", fab, st, front, 190, (CX, TOP+165),
              f"TEE  {tag}  ·  FRONT  ·  badge + domain, 190mm (7.5in)", f"tee-{tag}-front.png")
        build("tee", fab, st, back_art, 280, (CX, TOP+150),
              f"TEE  {tag}  ·  BACK  ·  masthead 280mm (11in)", f"tee-{tag}-back.png", back=True)

if __name__ == "__main__":
    main()
