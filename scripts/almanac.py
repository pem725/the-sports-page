#!/usr/bin/env python3
"""
almanac.py — silly fake-Latin labels and the Almanac history block, applied
only on milestone editions.

Mocks the federal government's "semiquincentennial" coinage by giving every
fiftieth issue a fake-Latin -ennial name, as if the newsletter's own issue
count required pomp-Latin observance. Non-milestone issues stay plain. The
joke peaks at Issue #250, where the newsletter's internal label
("Semiquincentennial") matches the federal usage for the nation's 250th year
exactly — same word, different denominator. The Quincentennial (#500)
closes the run.

Milestone schedule:
  - Every 50 issues from #50 through #10,000 (200 milestones total).
  - Beyond #10,000 we move to geological/epoch labels (effectively never,
    given ~340 issues/year publication rate; this is a stub for symmetry).
  - All other issues get no label and no Almanac block.

Pairs with almanac_data.py for the year-level historical facts that
populate the Almanac block on milestone issues. Used by autopublish.py.
"""

from __future__ import annotations
import datetime


# ---------------------------------------------------------------------------
# Silly fake-Latin label generator (milestone-only)
# ---------------------------------------------------------------------------

# Real Latin/Latin-ish terms for major milestone numbers. The federal
# joke is at K=5 (Issue #250 = "Semiquincentennial"), matching the
# usage the federal government has adopted for the nation's 250th.
REAL_TERMS = {
    1:  "Semicentennial",        # 50
    2:  "Centennial",            # 100
    3:  "Sesquicentennial",      # 150
    4:  "Bicentennial",          # 200
    5:  "Semiquincentennial",    # 250 — federal usage, deliberate
    6:  "Tercentennial",         # 300
    8:  "Quadricentennial",      # 400
    10: "Quincentennial",        # 500
    12: "Sexcentennial",         # 600
    14: "Septucentennial",       # 700
    16: "Octocentennial",        # 800
    18: "Nonacentennial",        # 900
    20: "Millennial",            # 1000
    30: "Sesquimillennial",      # 1500
    40: "Bimillennial",          # 2000
    50: "Bisesquimillennial",    # 2500 — a stretch, but on-theme
    60: "Trimillennial",         # 3000
    80: "Quadrimillennial",      # 4000
    100: "Quinquemillennial",    # 5000
    120: "Sexmillennial",        # 6000
    140: "Septuamillennial",     # 7000
    160: "Octomillennial",       # 8000
    180: "Nonamillennial",       # 9000
    200: "Decamillennial",       # 10,000 — last numeric milestone
}

# Beyond #10,000 we drop the year-anniversary conceit and use
# geological/cosmological terms. This is a stub; we will not reach
# this regime in any human lifetime.
EPOCH_TERMS = [
    "Holocene",
    "Anthropocene",
    "Pleistocene",
    "Miocene",
    "Eocene",
    "Mesozoic",
    "Paleozoic",
]


def _silly_coin(k: int) -> str:
    """Coin a silly Latin compound for K when no real term exists.

    K is the 50-multiple count (n = K * 50). Used for K=7, 9, 11, etc.
    """
    # Build a compound from the nearest two real anchors. For K=7 (350),
    # we riff on the "5" anchor (250 = Semiquincentennial) and the "2"
    # anchor (100 = Centennial). For most odd K, sesqui- prefixed to the
    # next-lower even produces a serviceable joke compound.
    if k < 20 and k % 2 == 1:
        # Odd K up to 19: "Sesqui" + the (K-1)-anchor
        base = REAL_TERMS.get(k - 1, "")
        if base:
            return f"Sesqui{base.lower()}"
    # Generic fallback: combine "Semi" + the next-higher real anchor
    nearest_above = min((kk for kk in REAL_TERMS if kk > k), default=None)
    if nearest_above is not None:
        return f"Semi{REAL_TERMS[nearest_above].lower()}"
    return f"Iteration-{k}"


def silly_label(n: int) -> str | None:
    """Return the edition label for issue n, or None if n is not a milestone.

    Milestones are every 50 issues from 50 through 10,000. Beyond that,
    epoch-style names cycle in for the joke's symmetry.
    """
    if n < 50:
        return None
    if n > 10_000:
        # Pick an epoch deterministically; cycles through EPOCH_TERMS.
        idx = ((n - 10_000) // 1000) % len(EPOCH_TERMS)
        return f"{EPOCH_TERMS[idx]} Era"
    if n % 50 != 0:
        return None

    k = n // 50
    if k in REAL_TERMS:
        return REAL_TERMS[k]
    return _silly_coin(k).capitalize()


def label_with_article(n: int) -> str | None:
    """Returns 'The Semicentennial Edition' or None."""
    label = silly_label(n)
    return f"The {label} Edition" if label else None


def is_milestone(n: int) -> bool:
    """True iff issue n is a labeled milestone."""
    return silly_label(n) is not None


# ---------------------------------------------------------------------------
# Almanac HTML block
# ---------------------------------------------------------------------------

def almanac_html(issue_num: int, today: datetime.date | None = None) -> str | None:
    """Render the Almanac footer block for milestone issues only.

    Returns None for non-milestone issues — autopublish skips injection
    when the return is None. For milestones, pulls one fact per anniversary
    year from almanac_data.ANNIVERSARIES, rotated deterministically by
    issue_num so different milestones see different facts.
    """
    if not is_milestone(issue_num):
        return None

    # Lazy import so this module is testable in isolation.
    from almanac_data import ANNIVERSARIES

    rows = []
    for year_data in ANNIVERSARIES:
        year = year_data["year"]
        years_ago = year_data["years_ago"]
        facts = year_data["facts"]
        # Rotate fact selection by issue number — different milestones see
        # different facts about the same anniversary year.
        fact = facts[issue_num % len(facts)]
        rows.append(
            f'    <li><span class="alm-yr">{year}</span>'
            f'<span class="alm-age">({years_ago} yrs ago)</span> '
            f'&mdash; {fact}</li>'
        )

    rows_html = "\n".join(rows)

    return f'''<section class="almanac">
  <h2 class="alm-hed">The Almanac &middot; <em>A Milestone Observance</em></h2>
  <p class="alm-intro">Every fiftieth issue of this newsletter is, by our
  own coinage, an &ldquo;edition&rdquo; in the same fake-Latin manner that
  the federal government has decreed 2026 the <em>semiquincentennial</em>
  of the Republic. This is <strong>{label_with_article(issue_num)}</strong>.
  In observance, the Almanac looks back at what was actually happening at
  the five prior fifty-year marks of our national life.</p>
  <ul class="alm-list">
{rows_html}
  </ul>
</section>'''


# ---------------------------------------------------------------------------
# CSS for the Almanac block (injected once into <style> by autopublish)
# ---------------------------------------------------------------------------

ALMANAC_CSS = """
.almanac{border-top:3px double var(--ink);margin:2.5rem 0 0;padding:1.4rem 0 0}
.almanac .alm-hed{font-family:'Playfair Display',serif;font-size:1.05rem;font-weight:700;text-transform:uppercase;letter-spacing:.1em;color:var(--ink);margin-bottom:.5rem}
.almanac .alm-hed em{color:var(--rust);font-style:italic;text-transform:none;letter-spacing:0;font-weight:400}
.almanac .alm-intro{font-family:'Libre Baskerville',serif;font-size:.85rem;color:var(--muted);font-style:italic;line-height:1.55;margin-bottom:.9rem}
.almanac .alm-intro em{color:var(--rust)}
.almanac .alm-intro strong{color:var(--ink);font-style:normal}
.almanac .alm-list{list-style:none;padding:0;margin:0;font-size:.86rem;line-height:1.6}
.almanac .alm-list li{padding:.35rem 0;border-bottom:1px solid var(--div)}
.almanac .alm-list li:last-child{border-bottom:none}
.almanac .alm-yr{font-family:'Roboto Mono',monospace;font-weight:700;color:var(--steel);margin-right:.45rem}
.almanac .alm-age{font-family:'Roboto Mono',monospace;font-size:.7rem;color:var(--muted);margin-right:.45rem}
"""


if __name__ == "__main__":
    # Sanity test — show that only milestones get labels
    print("Non-milestone issues (no label, no Almanac):")
    for n in [1, 2, 5, 25, 43, 44, 45, 49, 51, 99, 101, 149, 249, 251, 499]:
        label = label_with_article(n)
        print(f"  #{n:>4d} → {label or '(no label — plain issue)'}")
    print("\nMilestone issues (label + Almanac):")
    for n in [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 1000,
              1500, 2000, 5000, 10000, 11000]:
        label = label_with_article(n)
        print(f"  #{n:>5d} → {label}")
