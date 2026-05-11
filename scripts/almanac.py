#!/usr/bin/env python3
"""
almanac.py — silly fake-Latin issue labels and the Almanac history block.

Mocks the federal government's "semiquincentennial" coinage by treating
every issue number as if it were a year-anniversary requiring a Latin name.
The further from natural milestones (50, 100, 250, 500), the sillier the
compound. The joke peaks at Issue #250 ("Semiquincentennial") matching
the federal usage exactly, and resolves at Issue #500 ("Quincentennial").

Pairs with almanac_data.py for the year-level historical facts that
populate the Almanac block at the end of each issue.

Used by autopublish.py to inject content at publish time.
"""

from __future__ import annotations
import datetime
import random


# ---------------------------------------------------------------------------
# Silly fake-Latin label generator
# ---------------------------------------------------------------------------

# Real terms for milestone numbers — these are deliberate (the joke lands
# at #250 matching the federal usage).
MILESTONES = {
    1:   "Primal",
    25:  "Quintavicessennial",
    50:  "Semicentennial",
    75:  "Triquartacentennial",
    100: "Centennial",
    125: "Sesquincentennial",
    150: "Sesquicentennial",
    175: "Triquartersesquicentennial",
    200: "Bicentennial",
    225: "Bicentavicessennial",
    250: "Semiquincentennial",     # the federal joke, exactly
    275: "Bicentaquintaseptaquinquagessennial",
    300: "Tercentennial",
    350: "Sesquibicentennial",
    400: "Quadricentennial",
    450: "Sesquinonacentennial",
    500: "Quincentennial",         # the goal
}

# Latin ones-place prefixes (modified for euphony in compounds).
LATIN_ONES = ["", "una", "duo", "tert", "quart", "quint", "sext", "sept", "oct", "non"]

# Latin tens-place stems.
LATIN_TENS = {
    1: "decim",      # 11-19 (with prefix)
    2: "viges",
    3: "triges",
    4: "quadrages",
    5: "quinquages",
    6: "sexages",
    7: "septuages",
    8: "octoges",
    9: "nonages",
}


def silly_label(n: int) -> str:
    """Build a fake-Latin -ennial name for issue number n.

    Returns the bare adjective ("Quartaquadragesennial"), without "Edition"
    or "The" — those are added at the styling layer.
    """
    if n in MILESTONES:
        return MILESTONES[n]

    if n < 10:
        return f"{LATIN_ONES[n].capitalize()}ennial"

    if n < 20:
        # 10 = "Decennial", 11 = "Undecennial", ... 19 = "Nondecennial"
        teen_prefixes = ["", "Un", "Duo", "Ter", "Quart", "Quint",
                         "Sext", "Sept", "Oct", "Non"]
        if n == 10:
            return "Decennial"
        return f"{teen_prefixes[n - 10]}decennial"

    if n < 100:
        tens = n // 10
        ones = n % 10
        if ones == 0:
            return f"{LATIN_TENS[tens].capitalize()}imennial"
        return f"{LATIN_ONES[ones].capitalize()}a{LATIN_TENS[tens]}ennial"

    # 100-499: build "<hundreds>cent..." compounds, with no doubled "cent"
    if n < 500:
        hundreds = n // 100
        remainder = n % 100
        if remainder == 0:
            return ["", "Centennial", "Bicentennial",
                    "Tercentennial", "Quadricentennial"][hundreds]
        h_prefix = ["", "Cent", "Bicent", "Tercent", "Quadricent"][hundreds]
        sub = silly_label(remainder).lower()
        return f"{h_prefix}a{sub}"

    # >= 500 just keeps escalating
    return f"Post-Quincentennial-{n}"


def label_with_article(n: int) -> str:
    """Returns 'The Quartaquadragesennial Edition' (or similar)."""
    return f"The {silly_label(n)} Edition"


# ---------------------------------------------------------------------------
# Almanac HTML block
# ---------------------------------------------------------------------------

def almanac_html(issue_num: int, today: datetime.date | None = None) -> str:
    """Render the Almanac footer block for an issue.

    Pulls one fact per anniversary year from almanac_data.ANNIVERSARIES,
    rotated deterministically by issue_num so consecutive issues see
    different facts about the same anniversary years.
    """
    # Lazy import so this module is testable in isolation.
    from almanac_data import ANNIVERSARIES

    rows = []
    for year_data in ANNIVERSARIES:
        year = year_data["year"]
        years_ago = year_data["years_ago"]
        facts = year_data["facts"]
        # Rotate fact selection by issue number — different issues see
        # different facts about the same anniversary year.
        fact = facts[issue_num % len(facts)]
        rows.append(
            f'    <li><span class="alm-yr">{year}</span>'
            f'<span class="alm-age">({years_ago} yrs ago)</span> '
            f'&mdash; {fact}</li>'
        )

    rows_html = "\n".join(rows)

    return f'''<section class="almanac">
  <h2 class="alm-hed">The Almanac &middot; <em>Did You Know?</em></h2>
  <p class="alm-intro">In each of our Republic&rsquo;s prior fifty-year
  observances, history was running its own headlines. The federal government,
  in 2026, has named the present year the <em>semiquincentennial</em> &mdash;
  five Latin morphemes for what could have been &ldquo;two-fifty.&rdquo; This
  newsletter, in solidarity with that branch of the joke, observes its issues
  in the same manner. The current edition is <strong>{label_with_article(issue_num)}</strong>.</p>
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
    # Sanity test
    for n in [1, 2, 5, 10, 11, 25, 43, 44, 50, 99, 100, 143, 250, 500]:
        print(f"#{n:>3d} → {label_with_article(n)}")
