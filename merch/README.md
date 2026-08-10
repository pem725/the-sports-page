# The Sports Page — Apparel Artwork

Print-ready vector art for founder polos and general-issue t-shirts.

**These are the project's first vector brand assets.** Before this, `assets/` held
only PNGs, which no embroiderer or screen printer can use at size. Everything
here is SVG with **all text converted to outlines** — no fonts required on the
printer's machine, and nothing can reflow or substitute.

Canvases are sized in real millimetres, so files drop into a print layout at 1:1.

---

## Files

### Polo — founders (embroidery)

| File | Size | Use |
|---|---|---|
| `polo-01-badge.svg` | 82 mm | **Primary.** Left chest, light garments |
| `polo-01-badge-reversed.svg` | 82 mm | Left chest, navy/dark garments |
| `polo-02-wordmark.svg` | 82 mm | Understated alternative, no badge |
| `polo-02-wordmark-reversed.svg` | 82 mm | Same, dark garments |

### T-shirt — everyone (screen print or DTG)

| File | Width | Colours | Notes |
|---|---|---|---|
| `tee-01-masthead.svg` | 280 mm | 1 (navy) | The house shirt. Cheapest to print |
| `tee-02-denominator.svg` | 280 mm | 2 (navy + rust) | "ASK FOR THE DENOMINATOR" |
| `tee-03-sixty-seven-five.svg` | 280 mm | 2 (navy + rust) | "67.5" — the founding stat |
| `*-reversed.svg` | 280 mm | 1–2 on dark | For navy/charcoal garments |

### Master brand files

`logo-badge.svg` (100 mm) · `wordmark-stacked.svg` (180 mm) · `wordmark-horizontal.svg` (180 mm)

Use these for anything else — signage, stickers, hats. Scale freely; it's vector.

`previews/` holds PNG renders of every file for quick reference. **Do not send
the PNGs to the printer** — send the SVGs.

---

## Colours

| Name | Hex | Nearest Pantone (verify against a physical book) |
|---|---|---|
| Navy | `#051954` | PMS 2758 C, or 282 C if you want it deeper |
| Cream | `#f9f2de` | PMS 7499 C |
| Rust | `#b83a1e` | PMS 1675 C |
| Rust (on dark) | `#e8703f` | Lightened so it holds contrast on navy |

**The Pantone values are approximations.** Hex-to-Pantone conversion is not
exact, and screen colour is not fabric colour. Have the printer pull physical
chips and confirm before the run — especially the navy, which is easy to get
too purple.

For embroidery, give the shop the Pantone number and ask them to match from
their Madeira or Isacord chart. Don't accept a thread number sight-unseen; ask
to see the spool against the garment.

---

## Polo specification

- **Placement:** left chest, centred roughly 190–215 mm down from the shoulder
  seam and 75–90 mm in from the placket. Confirm on an actual garment in the
  size you're ordering most — chest height varies more than people expect.
- **Size:** 82 mm (3.25") wide as supplied.
- **Do not shrink below 76 mm (3").** The arced "THE SPORTS PAGE" sits at about
  5 mm cap height at the supplied size, which is already near the floor for
  legible embroidery. Below that the counters fill in and it turns to mush.
  If you need smaller, use `polo-02-wordmark.svg` instead.
- **Colours:** 2 thread colours maximum (ring + type in one, or all one colour).
  One-colour is cleanest and cheapest.
- **Rough stitch estimate:** 7,000–9,000 stitches for the badge at 3.25".
  Useful for getting a quote; the digitiser will give you the real number.

**Recommended founder combination:** navy polo, cream badge
(`polo-01-badge-reversed.svg`). It reads as considered rather than promotional,
which is the point for a founder shirt.

---

## T-shirt specification

- **Placement:** centred, top of art 75–90 mm below the collar seam.
- **Size:** 280 mm (11") wide for adult M–XXL. Scale to 230 mm (9") for S and
  youth. Never scale one film for all sizes; an 11" print on a small looks like
  a billboard.
- **Screen print:** `tee-01` is one colour and the cheapest thing here.
  `tee-02` and `tee-03` are two.
- **Printing on dark garments costs more than you'd think.** Reversed art needs
  a white underbase to keep the cream and rust opaque, which adds a screen and a
  flash. Budget for it, or use DTG for short runs.
- **DTG:** fine for all of these. Ask for a light pretreat on cream garments.

---

## Reversed art — read this

The reversed files have a **transparent background on purpose.** The garment
supplies the navy. If you open one and it looks like it's floating on nothing,
that is correct.

Do not let anyone "helpfully" add a navy rectangle behind it. That prints navy
ink onto navy fabric — you get a visible panel edge, a different sheen, a
heavier hand, and you pay for ink you didn't need.

The `previews/*-reversed.png` files show them on navy so you can see the intent.

---

## The chart: a histogram under a normal curve

The mark is the S over a histogram and a bell curve. It took several rounds to
get here and the failures are the useful record:

1. **Chart in solid ink over the S** — merges into the letter, reads as a blob.
2. **Chart knocked out of the S** — reads as a *damaged letter*. Scanning the
   rendered glyph row by row showed why: the S's thickest horizontal band is only
   about **32% of its width**. There is not enough ink to cut into, at any size.
3. **A diagonal trend line across the S** — fought the letterform no matter how
   thin the stroke got. The reason is geometric: **the S's spine runs upper-left
   to lower-right**, so any sloped line crosses it at close to a right angle. The
   problem was the angle, not the weight.
4. **Line running parallel to the spine, bars hanging off it** — solved the
   conflict but produced a curved deck over evenly spaced piers, which reads
   unmistakably as a **bridge**.
5. **What shipped: a normal curve.** It is horizontal and symmetric, so it sits
   *beneath* the S rather than crossing the diagonal at all — the conflict simply
   stops existing. And a histogram under a bell is the most recognisable
   statistics image there is, which is what the newsletter is actually about.

Nine bars, tops meeting the curve exactly (they are placed by evaluating the
Gaussian, not positioned by hand), over a baseline axis.

Final proportions: **S at 0.70 of the badge** (up from 0.42), curve spanning
1.20× the S width, peak 0.32, sigma 0.30, chart at 65% weight.

### The halo

Where the chart meets the S it carries a halo in the colour *behind* the art. On
open ground the halo is invisible. **It costs nothing** — the halo is the garment
colour, so on a one-colour print or a single thread it is unprinted fabric. No
extra screen, no extra thread.

The halo must match **what is behind the art**, not the file's background
setting. Reversed files have no background rect (the garment supplies it) but
their ground is still navy, so their halo is navy. The build keeps these
separate — `bg` paints a rectangle, `ground` says what the art sits on.

**If anyone recolours this for a new garment, the halo colour must change with
the garment.** It is the one thing about this mark that is not automatic.

### Physical dimensions at 82 mm (3.25")

| Element | Size |
|---|---|
| S cap height | 57.4 mm |
| Curve span | 58.6 mm |
| Bar width | 4.20 mm |
| Curve stroke | 2.80 mm |
| **Halo gap** | **1.54 mm** ← the tightest dimension |
| Clearance to ring | 9.2 mm each side |

The halo gap is the binding constraint against a ~1.0–1.2 mm practical satin
stitch — but at 1.54 mm the bell-curve mark has noticeably more margin than the
diagonal version it replaced. **Do not go below 76 mm (3")**, where it falls to
1.43 mm. Tell the digitiser the gap must stay open; it is what keeps the chart
legible against the S. Below 3", use `polo-02-wordmark.svg`.

## What to send the printer

1. The relevant `.svg` files (not the previews).
2. The Pantone numbers above, flagged as **to be confirmed against physical chips.**
3. The garment colour and size breakdown.
4. This note: *"All type is outlined. Reversed art is intentionally
   transparent — the garment is the background. Do not add a fill layer."*

If a shop insists on `.ai` or `.eps`, any SVG here opens losslessly in
Illustrator and can be saved out in one step. Nothing needs redrawing.

---

*Rebuild from source: `scripts/build_merch.py` in the session scratchpad requires
`fonttools`, plus Playfair Display and Roboto Mono variable fonts. The art is
generated, not hand-drawn, so it can be regenerated at any size on demand.*
