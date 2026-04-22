#!/usr/bin/env python3
"""
Fit the empirical JND curve (logistic) to the CFB ranked-matchup data and
emit SVG <path> strings for both the theoretical ideal ogive and the
fitted empirical ogive. Prints paths + per-delta points ready to paste.
"""
import csv
import math
import os
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "scripts", "data", "cfb-ranked-matchups.csv")


def load_per_delta():
    pd = defaultdict(lambda: [0, 0])
    with open(CSV_PATH) as f:
        r = csv.DictReader(f)
        for row in r:
            d = int(row["rank_delta"])
            pd[d][1] += 1
            if row["higher_rank_won"] == "True":
                pd[d][0] += 1
    return pd


def fit_logistic(xs, ys, lr=0.003, iters=5000):
    """P = 1/(1+exp(-(a + b*x)))"""
    a, b = 0.0, 0.0
    n = len(xs)
    for _ in range(iters):
        ga = gb = 0.0
        for x, y in zip(xs, ys):
            p = 1.0 / (1.0 + math.exp(-(a + b * x)))
            ga += (y - p)
            gb += (y - p) * x
        a += lr * ga / n
        b += lr * gb / n
    return a, b


def logistic_p(a, b, x):
    return 1.0 / (1.0 + math.exp(-(a + b * x)))


def jnd_from_params(a, b, target=0.75):
    return (math.log(target / (1 - target)) - a) / b


# ------------------------- SVG geometry -------------------------
# viewBox 0 0 680 300
# Plot area: x in [60, 660] mapped to delta in [0, 30]
# y in [260, 30] mapped to pct in [50, 100]
X0, XW = 60, 600
Y0, YH = 260, 230   # y=260 is 50%, y=30 is 100%
D_MAX = 30
P_MIN, P_MAX = 50, 100


def xpx(delta):
    return X0 + (delta / D_MAX) * XW


def ypx(pct):  # pct in 0..100
    return Y0 - ((pct - P_MIN) / (P_MAX - P_MIN)) * YH


def curve_path(fn, step=0.25):
    """Build SVG path string by sampling fn(delta) -> win probability in [0,1]."""
    pts = []
    d = 0.0
    while d <= D_MAX + 0.001:
        p = fn(d) * 100  # to percent
        pts.append(f"{xpx(d):.1f},{ypx(p):.1f}")
        d += step
    return "M " + " L ".join(pts)


def main():
    pd = load_per_delta()

    # Expand to individual observations for logistic fit
    xs, ys = [], []
    for d, (won, tot) in pd.items():
        xs.extend([d] * tot)
        ys.extend([1] * won + [0] * (tot - won))

    # EMPIRICAL fit
    a, b = fit_logistic(xs, ys)
    jnd_emp = jnd_from_params(a, b)
    print(f"EMPIRICAL logistic: a={a:.4f}, b={b:.4f}")
    print(f"  JND (P=0.75) at delta = {jnd_emp:.1f}")
    print(f"  P(delta=1)  = {logistic_p(a,b,1)*100:.1f}%")
    print(f"  P(delta=5)  = {logistic_p(a,b,5)*100:.1f}%")
    print(f"  P(delta=10) = {logistic_p(a,b,10)*100:.1f}%")
    print(f"  P(delta=15) = {logistic_p(a,b,15)*100:.1f}%")
    print(f"  P(delta=20) = {logistic_p(a,b,20)*100:.1f}%")
    print(f"  P(delta=30) = {logistic_p(a,b,30)*100:.1f}%  (asymptote approach)")

    # THEORETICAL: ideal ranking, JND at delta=4
    # 0.75 = 1/(1+exp(-k*4)) → k = ln(3)/4
    k_th = math.log(3) / 4
    print(f"\nTHEORETICAL ideal: k={k_th:.4f} (JND at delta=4)")
    print(f"  P(delta=1)  = {logistic_p(0, k_th, 1)*100:.1f}%")
    print(f"  P(delta=4)  = {logistic_p(0, k_th, 4)*100:.1f}% (target JND)")
    print(f"  P(delta=10) = {logistic_p(0, k_th, 10)*100:.1f}%")
    print(f"  P(delta=20) = {logistic_p(0, k_th, 20)*100:.1f}%")

    # Paths
    emp_path = curve_path(lambda d: logistic_p(a, b, d))
    th_path  = curve_path(lambda d: logistic_p(0, k_th, d))

    print("\n" + "=" * 60)
    print("SVG PATHS")
    print("=" * 60)
    print(f"\nTHEORETICAL path:\n{th_path}\n")
    print(f"EMPIRICAL path:\n{emp_path}\n")

    # Empirical scatter points for Figure 2
    print("EMPIRICAL scatter points (delta, rate, n):")
    for d in sorted(pd):
        if d > D_MAX or pd[d][1] < 1:
            continue
        won, tot = pd[d]
        rate = won / tot * 100
        cx = xpx(d)
        cy = ypx(rate)
        # Radius scaled by sqrt(n) so bigger samples look bigger
        r = 2 + math.sqrt(tot) * 0.35
        print(f'  <circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.2f}" fill="#2c4a6e" opacity="0.6"/>'
              f'  <!-- delta={d}, n={tot}, rate={rate:.1f}% -->')

    # JND reference data
    print(f"\nJND annotation position (empirical): x={xpx(jnd_emp):.1f}, delta={jnd_emp:.1f}")
    print(f"JND annotation position (theoretical): x={xpx(4):.1f}, delta=4")


if __name__ == "__main__":
    main()
