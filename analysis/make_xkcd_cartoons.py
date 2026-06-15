"""Prototype xkcd-style cartoons for past issues.

Each cartoon distills the article's *question* (not its full chart) into a
single hand-drawn diagram. Site palette (ink, rust, gold, steel, cream)
substituted for matplotlib's defaults so the cartoons sit naturally
inside The Sports Page broadsheet aesthetic.

Output: assets/xkcd/<slug>.svg
"""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as fm
import numpy as np

REPO = Path(__file__).resolve().parent.parent
FONT = REPO / "assets" / "fonts" / "HumorSans.ttf"
OUT = REPO / "assets" / "xkcd"
OUT.mkdir(parents=True, exist_ok=True)

# Register HumorSans so matplotlib's xkcd mode picks it up
fm.fontManager.addfont(str(FONT))
HUMOR = fm.FontProperties(fname=str(FONT)).get_name()

# Site palette
INK = "#1a1208"
RUST = "#b83a1e"
GOLD = "#c9962a"
STEEL = "#2c4a6e"
CREAM = "#f5f0e8"
MUTED = "#6b5e4a"


def setup_axes(ax, *, hide_spines_right_top=True, ink=INK):
    if hide_spines_right_top:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(ink)
        ax.spines[s].set_linewidth(2.5)
    ax.tick_params(colors=ink)
    ax.set_facecolor(CREAM)


def with_xkcd(figsize=(8, 5)):
    """Context manager wrapper: applies xkcd style + our font + cream bg."""
    return plt.xkcd(scale=1.2, length=120, randomness=2)


def save_svg(name):
    path = OUT / f"{name}.svg"
    plt.savefig(path, format="svg", bbox_inches="tight",
                facecolor=CREAM, edgecolor="none", transparent=False)
    plt.close()
    print(f"  → {path.relative_to(REPO)}")


# ──────────────────────────────────────────────────────────────────────
# Cartoon 1 — Issue #074 (Mets are 70x more predictable than the snow)
# ──────────────────────────────────────────────────────────────────────
def predictability_bars():
    with with_xkcd():
        plt.rcParams["font.family"] = HUMOR
        fig, ax = plt.subplots(figsize=(8.5, 5.2))
        setup_axes(ax)

        labels = ["SNOW", "METS"]
        values = [0.007, 0.41]
        colors = [STEEL, RUST]
        bars = ax.bar(labels, values, color=colors, width=0.55, edgecolor=INK, linewidth=2)

        ax.set_ylabel("YEAR-OVER-YEAR\nMEMORY  ( r )", color=INK)
        ax.set_title("THINGS YOU'D EXPECT TO BE RANDOM", color=INK, pad=20)
        ax.set_ylim(0, 0.55)
        ax.set_yticks([])

        # Value labels
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.02,
                    f"{v:+.3f}".replace("0.", "."),
                    ha="center", va="bottom", color=INK)

        # Hand-drawn annotation arrows — both ABOVE their bars to avoid
        # the y-axis label on the left.
        ax.annotate("ATMOSPHERE\nDOES NOT\nREMEMBER",
                    xy=(0, 0.05), xytext=(0.05, 0.28),
                    color=STEEL, ha="center",
                    arrowprops=dict(arrowstyle="->", color=STEEL, lw=2,
                                    connectionstyle="arc3,rad=.2"))

        ax.annotate("THE ROSTER\nMOSTLY DOES",
                    xy=(1, 0.39), xytext=(0.95, 0.50),
                    color=RUST, ha="center",
                    arrowprops=dict(arrowstyle="->", color=RUST, lw=2,
                                    connectionstyle="arc3,rad=-.2"))

        save_svg("074-snow-vs-mets")


# ──────────────────────────────────────────────────────────────────────
# Cartoon 2 — Issue #064 (Mariners variance: same team, both ends of the tail)
# ──────────────────────────────────────────────────────────────────────
def variance_curve():
    with with_xkcd():
        plt.rcParams["font.family"] = HUMOR
        fig, ax = plt.subplots(figsize=(8.5, 5.2))
        setup_axes(ax)

        x = np.linspace(-3.5, 3.5, 400)
        y = np.exp(-(x ** 2) / 2.0)
        ax.plot(x, y, color=INK, lw=3)
        ax.fill_between(x, 0, y, color=GOLD, alpha=0.18)

        # Arrows to the tails
        ax.annotate("8-GAME\nSTREAK",
                    xy=(2.6, 0.06), xytext=(2.0, 0.45),
                    color=RUST,
                    arrowprops=dict(arrowstyle="->", color=RUST, lw=2.2,
                                    connectionstyle="arc3,rad=.25"))

        ax.annotate("ONE-RUN\nDUD",
                    xy=(-2.6, 0.06), xytext=(-3.4, 0.45),
                    color=STEEL,
                    arrowprops=dict(arrowstyle="->", color=STEEL, lw=2.2,
                                    connectionstyle="arc3,rad=-.25"))

        ax.text(0, 0.78, "THE TEAM", ha="center", color=INK)
        ax.text(0, 0.68, "(.234 / .398)", ha="center", color=MUTED, fontsize=11)

        ax.set_title("BOTH GAMES SAME ROSTER", color=INK, pad=20)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines["bottom"].set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.set_ylim(-0.05, 1.1)

        save_svg("064-variance-tails")


# ──────────────────────────────────────────────────────────────────────
# Cartoon 3 — Issue #071 (Career half-life: the cliff at the end of the runway)
# ──────────────────────────────────────────────────────────────────────
def half_life_runway():
    with with_xkcd():
        plt.rcParams["font.family"] = HUMOR
        fig, ax = plt.subplots(figsize=(8.5, 5.2))
        setup_axes(ax)

        x = np.linspace(1, 18, 200)
        # Survival curve — flat-ish then cliff
        y = 100 * np.exp(-((x - 1) / 9.0) ** 2.4)
        ax.plot(x, y, color=INK, lw=3.2)

        ax.set_xlim(0.5, 19)
        ax.set_ylim(0, 110)
        ax.set_xlabel("YEARS SINCE DEBUT", color=INK)
        ax.set_ylabel("% STILL IN THE LEAGUE", color=INK)
        ax.set_title("WHAT WE'VE BEEN CALLING\nAN AGING CURVE", color=INK, pad=20)

        # Mark the half-life
        idx = np.argmin(np.abs(y - 50))
        x50 = x[idx]
        ax.axhline(50, color=GOLD, lw=1.5, ls="--", alpha=0.7)
        ax.axvline(x50, color=GOLD, lw=1.5, ls="--", alpha=0.7)
        ax.text(x50 + 0.3, 53, f"HALF GONE", color=RUST)

        ax.annotate("STILL HERE\nAND STILL GOOD",
                    xy=(1.5, 95), xytext=(3.2, 75),
                    color=STEEL,
                    arrowprops=dict(arrowstyle="->", color=STEEL, lw=2,
                                    connectionstyle="arc3,rad=-.25"))

        ax.annotate("ELITE 5%",
                    xy=(17, 8), xytext=(13, 30),
                    color=RUST,
                    arrowprops=dict(arrowstyle="->", color=RUST, lw=2,
                                    connectionstyle="arc3,rad=.3"))

        save_svg("071-half-life-cliff")


# ──────────────────────────────────────────────────────────────────────
# Cartoon 4 — Issue #078 (Cross-sport persistence: domain × predictor)
# ──────────────────────────────────────────────────────────────────────
def cross_sport_scoreboard():
    with with_xkcd():
        plt.rcParams["font.family"] = HUMOR
        fig, ax = plt.subplots(figsize=(8.5, 5.6))
        setup_axes(ax)

        labels = ["NBA", "NHL", "MLB", "NFL", "CO\nSNOW"]
        values = [65, 62, 49, 34, -48]
        colors = [GOLD, STEEL, "#2a6e3f", "#8b1e3f", MUTED]
        bars = ax.barh(labels, values, color=colors, edgecolor=INK, linewidth=2, height=0.55)

        ax.set_xlim(-70, 80)
        ax.axvline(0, color=INK, lw=2)
        ax.set_xlabel("HOW INFORMATIVE THE\nPREDICTOR ACTUALLY IS", color=INK)
        ax.set_title("EACH DOMAIN, BEST-KNOWN PREDICTOR", color=INK, pad=20)

        # Value labels at end of each bar
        for bar, v in zip(bars, values):
            ha = "left" if v >= 0 else "right"
            offset = 2 if v >= 0 else -2
            ax.text(v + offset, bar.get_y() + bar.get_height()/2,
                    f"{v:+}", ha=ha, va="center", color=INK)

        ax.annotate("WAIT WHAT",
                    xy=(-46, 4), xytext=(-30, 3.0),
                    color=RUST,
                    arrowprops=dict(arrowstyle="->", color=RUST, lw=2,
                                    connectionstyle="arc3,rad=.2"))

        ax.set_yticks(range(len(labels)))
        ax.invert_yaxis()
        ax.set_xticks([])

        save_svg("078-cross-sport")


# ──────────────────────────────────────────────────────────────────────
# Cartoon 5 — Issue #082 (Sixteen and three: NHL 16-3 first time ever)
# ──────────────────────────────────────────────────────────────────────
def sixteen_and_three():
    """One tiny bar in a sea of bigger ones — the visceral case for rarity.

    Shows the distribution of NHL champion playoff losses, 1987-2026.
    Every bar is the count of champions with that many losses. The
    "3 losses" bar is a SINGLE dot — the 2026 Hurricanes are the only
    NHL team ever to finish a 16-win playoff run at 16-3. Annotation
    drives the point: "this happened exactly once."
    """
    with with_xkcd():
        plt.rcParams["font.family"] = HUMOR
        fig, ax = plt.subplots(figsize=(8.5, 5.4))
        setup_axes(ax)

        # Verified NHL champion loss-count distribution (1987-2026, ex-2005)
        loss_counts = [2, 3, 4, 5, 6, 7, 8, 9, 10]
        n_champs    = [1, 1, 5, 3, 9, 10, 5, 2, 3]
        colors      = [STEEL if l != 3 else RUST for l in loss_counts]

        bars = ax.bar(loss_counts, n_champs, color=colors, edgecolor=INK,
                      linewidth=2, width=0.7)

        # Value labels on top of each bar
        for bar, v in zip(bars, n_champs):
            ax.text(bar.get_x() + bar.get_width()/2, v + 0.25,
                    f"{v}", ha="center", va="bottom", color=INK, fontsize=11)

        ax.set_xlabel("LOSSES ON THE WAY TO THE CUP", color=INK)
        ax.set_ylabel("NHL CHAMPIONS,\n1987-2026", color=INK)
        ax.set_title("ONE OF THESE IS NOT LIKE THE OTHERS", color=INK, pad=22)

        ax.set_xticks(loss_counts)
        ax.set_yticks([])
        ax.set_ylim(0, 13.5)
        ax.set_xlim(1, 11.5)

        # Annotation pointing at the lone "3" bar
        ax.annotate("HAPPENED EXACTLY ONCE\n(THE 2026 HURRICANES)",
                    xy=(3, 1.2), xytext=(5.5, 6.5),
                    color=RUST, ha="center",
                    fontsize=11,
                    arrowprops=dict(arrowstyle="->", color=RUST, lw=2.2,
                                    connectionstyle="arc3,rad=-.3"))

        # Smaller annotation: the modal/common shape
        ax.annotate("WHAT A CHAMPION\nUSUALLY LOOKS LIKE",
                    xy=(7, 10.2), xytext=(8.7, 12.2),
                    color=STEEL, ha="center", fontsize=10,
                    arrowprops=dict(arrowstyle="->", color=STEEL, lw=1.8,
                                    connectionstyle="arc3,rad=.2"))

        save_svg("082-sixteen-and-three")


if __name__ == "__main__":
    predictability_bars()
    variance_curve()
    half_life_runway()
    cross_sport_scoreboard()
    sixteen_and_three()
    print(f"\n5 cartoons in {OUT.relative_to(REPO)}")
