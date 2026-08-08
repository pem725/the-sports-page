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

## One design decision worth knowing

**The bar-chart-inside-the-S from the web logo is deliberately not here.**

It was built and tested twice — once as solid ink, once knocked out of the
letterform. Both failed. At chest size, and in a single colour, the chart reads
as a damaged letter rather than a rising trend line. It works on screen at
banner width because it has room and anti-aliasing; apparel has neither.

The plain Playfair S carries the mark on its own. If you want the chart back for
a large-format application — a banner, a poster, signage — use the original
`assets/banner.png` artwork, which was drawn for that context.

---

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
