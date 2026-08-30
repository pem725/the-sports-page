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

**The house shirt is a two-position print on a NATURAL garment:**

| Position | File | Width | Colours |
|---|---|---|---|
| **Front** | `tee-front-badge-url-natural.svg` | 190 mm | 1 (navy) |
| **Back** | `tee-01-masthead-natural.svg` | 280 mm | 1 (navy) |

**Send the `-natural` files, not the plain ones.** They are identical except for
the halo colour, and the reason is in "The halo" below. The plain
`tee-front-badge-url.svg` and `tee-01-masthead.svg` remain as the generic
light-garment masters for any future garment colour.

Front is the badge with the bare domain beneath it — no `http://`, no `www`.
`thesportspage.net` is the whole address anyone needs to type, and the extra
characters only cost legibility on fabric.

Alternate front designs, single position:

| File | Width | Colours | Notes |
|---|---|---|---|
| `tee-02-denominator.svg` | 280 mm | 2 (navy + rust) | "ASK FOR THE DENOMINATOR" |
| `tee-03-sixty-seven-five.svg` | 280 mm | 2 (navy + rust) | "67.5" — the founding stat |
| `*-reversed.svg` | — | 1–2 on dark | For navy/charcoal garments |

### Master brand files

`logo-badge.svg` (100 mm) · `wordmark-stacked.svg` (180 mm) · `wordmark-horizontal.svg` (180 mm)

Use these for anything else — signage, stickers, hats. Scale freely; it's vector.

`previews/` holds a PNG render of every SVG, each on the ground it belongs on
(rebuild with `scripts/build_previews.py`), and
`mockups/` holds flat-lay garment mockups drawn at true relative scale — useful
for showing people what they are actually getting. **Do not send either to the
printer** — send the SVGs.

---

## The garment: Gildan Softstyle, Natural

> **The blank is under review.** Softstyle was picked on colour alone and it is
> the slimmest-cut shirt in its price band. See [`blanks.md`](blanks.md) for a
> priced comparison against a size-and-comfort brief, and for the three things
> that do *not* transfer if the garment changes.


The tee is **Gildan Softstyle Jersey in "Natural"** — unbleached cotton, with the
faint dark flecks that come with it. Chosen for a measurable reason rather than a
taste one.

The site's page background is `--aged #e0d8c5`. Natural samples at about
`#e4dccf`. In Lab space that is **ΔE 3.5**, inside the range where two colours
read as the same colour under different light. The shirt is not coordinated with
the newspaper; it is the same colour as the newspaper. For comparison: Off White
is ΔE 6.4, plain white is ΔE 17.

It is also the cheapest option. Navy ink on a light garment is a single screen
with no white underbase.

**Two limits to know before ordering:**

- **Natural runs YS/YM/YL and S–3XL.** There is no XS and nothing above 3XL. If
  anyone needs 4XL or 5XL, that person cannot have this colour — **Off White**
  (`#f2ead4`, S–5XL, no youth sizes) is the fallback and still matches well.
  Navy is the only colour carrying the full YS–5XL run.
- **The flecks are part of it.** Unbleached cotton is not a uniform field. Fine
  under a solid navy print; worth knowing before someone is surprised by it.

## Colours

| Name | Hex | Nearest Pantone (verify against a physical book) |
|---|---|---|
| Navy | `#051954` | PMS 2758 C, or 282 C if you want it deeper |
| Cream | `#f9f2de` | PMS 7499 C |
| Rust | `#b83a1e` | PMS 1675 C |
| Rust (on dark) | `#e8703f` | Lightened so it holds contrast on navy |
| Natural (garment, not a brand colour) | `#e4dccf` | n/a — this is the shirt, not ink |

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

**The polo is EMBROIDERED, not printed.** Badge only, left chest, no domain and
no back decoration. That restraint is the point — it should read as considered
rather than promotional.

**Recommended founder combination:** navy polo, cream badge
(`polo-01-badge-reversed.svg`).

---

## T-shirt specification

Two positions, both screen printed.

- **Front:** badge over the domain, **190 mm (7.5") wide**, centred, top of art
  about 95 mm below the collar seam.
- **Back:** the masthead lockup, **280 mm (11") wide**, centred, top of art about
  80 mm below the collar seam.
- Scale both to roughly 80% for S and youth. Never run one film across all
  sizes; an 11" back print on a small reads as a billboard.
- Two positions means **two set-ups**. Confirm the quote covers front *and* back
  — shops often price a "one-colour tee" assuming a single position.
- **Screen print:** `tee-01` is one colour and the cheapest thing here.
  `tee-02` and `tee-03` are two.
- **Printing on dark garments costs more than you'd think.** Reversed art needs
  a white underbase to keep the cream and rust opaque, which adds a screen and a
  flash. Budget for it, or use DTG for short runs.
- **DTG:** fine for all of these. Ask for a light pretreat on Natural, and send
  the `-natural` files — see "Why the `-natural` files exist" below.

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

## The mark: an S with a normal curve through it

The badge is the S with a bell curve sweeping through its lower half. Nothing
else — no histogram bars, no axis. Getting here took several rounds and the
failures are worth keeping:

1. **Chart in solid ink over the S** — merges into the letter, reads as a blob.
2. **Chart knocked out of the S** — reads as a *damaged letter*. Scanning the
   rendered glyph row by row showed why: the S's thickest horizontal band is only
   about **32% of its width**. There is not enough ink to cut into, at any size.
3. **A diagonal trend line across the S** — fought the letterform no matter how
   thin the stroke got. The reason is geometric: **the S's spine runs upper-left
   to lower-right**, so any sloped line crosses it at close to a right angle. The
   problem was the angle, not the weight.
4. **Line parallel to the spine with bars hanging off it** — solved the conflict
   but produced a curved deck over evenly spaced piers: a **bridge**.
5. **Normal curve with a histogram beneath it** — read correctly at last, but the
   bars crowded the letterform and were by far the hardest part to embroider.
6. **What shipped: the curve alone.** A bell is horizontal and symmetric, so it
   sits *across* the S rather than fighting the diagonal, and it says
   "statistics" without any supporting furniture. Dropping the bars and the axis
   removed the fiddliest elements in the mark and cost it nothing.

Final proportions: **S at 0.70 of the badge** (up from 0.42), curve spanning
1.35× the S width, peak 0.42, sigma 0.34, stroke at 65% weight.

### The halo

Where the curve crosses the S it carries a halo in the colour *behind* the art.
On open ground the halo is invisible. **It costs nothing** — the halo is the
garment colour, so on a one-colour print or a single thread it is unprinted
fabric. No extra screen, no extra thread.

The halo must match **what is behind the art**, not the file's background
setting. Reversed files have no background rect (the garment supplies it) but
their ground is still navy, so their halo is navy. The build keeps these
separate — `bg` paints a rectangle, `ground` says what the art sits on.

**If anyone recolours this for a new garment, the halo colour must change with
the garment.** It is the one thing about this mark that is not automatic.

### Why the `-natural` files exist, and when it would have bitten

The halo is a **painted stroke in the ground colour**, not a gap in the artwork.
That distinction is invisible right up until it isn't:

- **Screen print** — the shop separates by colour. A one-colour navy job burns a
  screen for the navy only; the halo is simply not on it, so unprinted fabric
  fills the gap. The halo's hex never matters.
- **DTG** — the machine prints the file as drawn. Our standard light-garment art
  carries a halo in `#f9f2de`, our cream. On a Natural shirt (`#e4dccf`) that is
  ink, and it lands as a **slightly paler outline tracing the curve where it
  crosses the S**.

  Worth being exact about the size of this, rather than alarming: the two
  colours are **ΔE 8.3** apart. In isolation that is a shade of difference you
  might not name. Against a hard edge, directly abutting the fabric, it is
  visible — edge contrast is where the eye is most sensitive. It reads as a
  printing artefact rather than as part of the mark, which is the objection.
  It is not a ruined shirt; it is a shirt with a flaw you would notice on the
  second wearing and never stop noticing.

So the art going to the printer is built with `ground=NATURAL`. It is correct for
either method, which is the point: it should not depend on the shop choosing the
process we assumed.

### Physical dimensions at 82 mm (3.25")

| Element | Size |
|---|---|
| S cap height | 57.4 mm |
| Curve span | 66.0 mm |
| Curve stroke | 2.80 mm |
| **Halo gap** | **1.54 mm** ← the tightest dimension |
| Clearance to ring | 5.6 mm each side |

The halo gap is the binding constraint against a ~1.0–1.2 mm practical satin
stitch, and at 1.54 mm there is comfortable margin — noticeably more than the
1.24 mm the earlier diagonal version had. **Do not go below 76 mm (3")**, where
it falls to about 1.43 mm. Tell the digitiser the gap must stay open; it is what
keeps the curve legible where it crosses the S. Below 3", use
`polo-02-wordmark.svg`.

The curve is now the only element besides the S and the ring, which makes this
the simplest version of the mark to stitch by a wide margin.

## What to send the printer

For the tee order as specified — Gildan Softstyle, Natural:

1. **`tee-front-badge-url-natural.svg`** (front, 190 mm) and
   **`tee-01-masthead-natural.svg`** (back, 280 mm). Not the previews, and not
   the versions without `-natural`.
2. The Pantone number for the navy, flagged as **to be confirmed against physical
   chips** — it is easy to get too purple.
3. Garment: **Gildan Softstyle Jersey, Natural**, with the size breakdown.
   Remember Natural stops at 3XL.
4. This note: *"All type is outlined. One colour, navy. The lighter stroke
   tracing the curve is a knockout to garment colour, not a second ink — it is
   already set to this garment. Reversed art is intentionally transparent; the
   garment is the background. Do not add a fill layer."*

For the founder polos: `polo-01-badge-reversed.svg`, embroidered, navy garment.

If a shop insists on `.ai` or `.eps`, any SVG here opens losslessly in
Illustrator and can be saved out in one step. Nothing needs redrawing.

---

*Rebuild from source: `python3 scripts/build_merch.py`, then
`python3 scripts/build_mockups.py`. Requires `fonttools` and `cairosvg`; the two
variable fonts are committed at `scripts/fonts/` so the build runs anywhere. (They
used to live only in a session scratchpad, which meant the mark could not be
regenerated on any machine — including the one that drew it.) The art is
generated, not hand-drawn, so it can be reissued at any size on demand.*
