#!/usr/bin/env python3
"""Render every merch SVG to a PNG preview.

There was no script for this. The previews were made by hand in the session that
drew the logo, which meant that the moment two new files were added the folder
quietly stopped matching the README's claim to hold "a render of every file".
Generated previews cannot drift.

Each file is rendered on the ground it is meant to sit on, because the halo where
the curve crosses the S is painted in the ground colour -- on the wrong
background it shows as a ring, which is exactly the mistake the previews exist to
catch.
"""
import os, io, sys, glob
import cairosvg
from PIL import Image

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M    = os.path.join(REPO, "merch")
OUT  = os.path.join(M, "previews")
PX   = 700
PAD  = 28

GROUNDS = [                      # first match wins -- order matters
    ("-reversed", (0x16, 0x22, 0x4a)),   # dark garment
    ("-natural",  (0xe4, 0xdc, 0xcf)),   # Gildan Softstyle Natural
    ("",          (0xf9, 0xf2, 0xde)),   # our cream, the default light ground
]


def ground_for(name):
    for suffix, rgb in GROUNDS:
        if suffix and suffix in name:
            return rgb
    return GROUNDS[-1][1]


def main():
    os.makedirs(OUT, exist_ok=True)
    files = sorted(glob.glob(os.path.join(M, "*.svg")))
    if not files:
        sys.exit("no SVGs in merch/ -- run build_merch.py first")
    for path in files:
        name = os.path.basename(path)[:-4]
        art = Image.open(io.BytesIO(cairosvg.svg2png(
            url=path, output_width=PX))).convert("RGBA")
        bb = art.getbbox() or (0, 0, art.width, art.height)
        art = art.crop(bb)
        card = Image.new("RGB", (art.width + PAD*2, art.height + PAD*2),
                         ground_for(name))
        card.paste(art, (PAD, PAD), art)
        card.save(os.path.join(OUT, name + ".png"))
        print(f"   {name}.png  {card.width}x{card.height}")
    # anything left over is a preview whose SVG no longer exists
    live = {os.path.basename(f)[:-4] for f in files}
    for stale in sorted(glob.glob(os.path.join(OUT, "*.png"))):
        if os.path.basename(stale)[:-4] not in live:
            os.remove(stale)
            print(f"   removed stale {os.path.basename(stale)}")
    print(f"{len(files)} previews")


if __name__ == "__main__":
    main()
