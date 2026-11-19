"""Fuzzy dots: a point estimate drawn as a haze whose width IS its uncertainty.

The editor's idea (2026-11-19): the less sure we are where a point sits, the bigger and
fainter it should be. Here that is made exact. Each dot is an ellipse filled with a radial
gradient whose opacity follows a normal curve: the haze reaches SPREAD standard errors out
on each side, and its peak opacity falls as 1/se, so every dot carries the same total ink.
A sure estimate is a tight dark dot; an unsure one is a wide pale smear.

Gradients, not blur filters: cairosvg (which draws the OG cards) ignores feGaussianBlur but
renders radialGradient, so the card shows the same haze the page does.

Usage:
    from fuzzydot import FuzzyDots
    fz = FuzzyDots(px_per_unit=39.2, se_ref=0.8)   # se_ref: the se that gets PEAK opacity
    svg.append(fz.dot(cx, cy, se, "#b83a1e"))
    svg.insert(1, fz.defs())                          # once, after all dots
"""
import math

SPREAD = 2.5        # haze reaches this many standard errors each side (95% = 1.96)
PEAK = 0.95         # opacity at the center of the surest dot
STOPS = 9           # gradient stops along the radius


class FuzzyDots:
    def __init__(self, px_per_unit, se_ref, ry=6.0, ry_max=9.0, core=1.6, spread=SPREAD, peak=PEAK, prefix="fz"):
        self.prefix = prefix  # unique per instance when one SVG holds two sets of dots
        self.k, self.se_ref, self.ry, self.ry_max = px_per_unit, se_ref, ry, ry_max
        self.core, self.spread, self.peak = core, spread, peak
        self._defs, self._n = [], 0

    def alpha(self, se):
        """Center opacity: inversely proportional to se, so total ink is constant."""
        return min(self.peak, self.peak * self.se_ref / se)

    def dot(self, cx, cy, se, color):
        self._n += 1
        gid = f"{self.prefix}{self._n}"
        a0 = self.alpha(se)
        stops = []
        for i in range(STOPS + 1):
            f = i / STOPS                                   # 0 = center, 1 = edge
            z = f * self.spread                             # standard errors out
            stops.append(f'<stop offset="{f:.3f}" stop-color="{color}" stop-opacity="{a0 * math.exp(-0.5 * z * z):.3f}"/>')
        self._defs.append(f'<radialGradient id="{gid}" cx="0.5" cy="0.5" r="0.5">{"".join(stops)}</radialGradient>')
        rx = self.spread * se * self.k
        ry = min(self.ry_max, self.ry * math.sqrt(se / self.se_ref))
        out = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="url(#{gid})"/>'
        if self.core:
            out += f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{self.core}" fill="{color}"/>'
        return out

    def defs(self):
        return "<defs>" + "".join(self._defs) + "</defs>"
