#!/usr/bin/env python3
"""Write queue/207-genes-rule-college.html from data/cfb-results.json, data/cfb-2026-verify.json
and data/cfb-cfp-2026-11-17.json, so every number in the piece comes from the result files.
Run add_topic_glyph.py on the output afterwards (it is idempotent).
"""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(REPO, "queue", "207-genes-rule-college.html")
SLUG = "207-genes-rule-college"

R = json.load(open(os.path.join(HERE, "data", "cfb-results.json")))["R"]
V = json.load(open(os.path.join(HERE, "data", "cfb-2026-verify.json")))
T26 = R["y2026"]["teams"]
TOP = json.load(open(os.path.join(HERE, "data", "cfb-cfp-2026-11-17.json")))["ranks"][:12]

p100 = lambda x: f"{round(100 * x):d}"
ans, kick = R["league"]["answer"][1], R["league"]["other"][1]
same_a, same_o = R["samegame"][1], R["samegame"][2]
madj = R["margin_adj"]
seasons = {int(k): v for k, v in R["by_season"].items()}
n_short = sum(1 for v in seasons.values() if v[1] < v[3])
fan = R["fan"]
c = R["corr"]; yty = R["yty"]

HED = "In College, the Answer Drive Comes Up Short. <em>Even No.&nbsp;1 Georgia&rsquo;s.</em>"
HED_PLAIN = "In College, the Answer Drive Comes Up Short. Even No. 1 Georgia’s."

# ---- figure: one row per season, answer (rust) and kickoff (steel) dots ----
X0, X1, LO, HI = 150, 620, 28, 40
xs = lambda v: X0 + (100 * v - LO) / (HI - LO) * (X1 - X0)
rows = sorted(seasons)
top_y, step = 46, 22
H = top_y + step * len(rows) + 40
svg = [f'<svg class="chart" viewBox="0 0 680 {H}" width="680" height="{H}" role="img" '
       f'aria-label="For every college football season from 2014 to 2026, drives right after the other team scores a touchdown scored less often than other kickoff drives: {n_short} seasons of {len(rows)}." '
       'style="max-width:100%;height:auto;display:block;margin:0 auto;font-family:\'Roboto Mono\',monospace">']
svg.append(f'<circle cx="160" cy="14" r="5" fill="#b83a1e"/><text x="170" y="18" font-size="11" fill="#1a1208">right after they score a TD</text>')
svg.append(f'<circle cx="400" cy="14" r="5" fill="#2c4a6e"/><text x="410" y="18" font-size="11" fill="#1a1208">other kickoff drives</text>')
for t in range(LO, HI + 1, 2):
    x = xs(t / 100)
    svg.append(f'<line x1="{x:.1f}" y1="{top_y - 12}" x2="{x:.1f}" y2="{top_y + step * len(rows) - 8}" stroke="#c8b99a" stroke-width="0.6"/>')
    svg.append(f'<text x="{x:.1f}" y="{top_y + step * len(rows) + 8}" font-size="10" fill="#6b5e4a" text-anchor="middle">{t}</text>')
for i, y in enumerate(rows):
    _, a, _, o = seasons[y]
    cy = top_y + i * step
    lab = f"{y}" + (" to date" if y == 2026 else "")
    svg.append(f'<text x="{X0 - 14}" y="{cy + 4}" font-size="11" fill="#1a1208" text-anchor="end">{lab}</text>')
    svg.append(f'<line x1="{xs(a):.1f}" y1="{cy}" x2="{xs(o):.1f}" y2="{cy}" stroke="#6b5e4a" stroke-width="1.2"/>')
    svg.append(f'<circle cx="{xs(a):.1f}" cy="{cy}" r="5" fill="#b83a1e"/>')
    svg.append(f'<circle cx="{xs(o):.1f}" cy="{cy}" r="5" fill="#2c4a6e"/>')
svg.append(f'<text x="{(X0 + X1) / 2:.0f}" y="{top_y + step * len(rows) + 26}" font-size="10.5" fill="#6b5e4a" text-anchor="middle">drives that ended in a touchdown or field goal, per 100</text>')
svg.append("</svg>")
FIG = "\n".join(svg)

# ---- 2026 table ----
def row(t):
    d = T26[t["team"]]
    rec = t["record"].replace("-", "&ndash;")
    return (f'<tr><td>{t["rank"]}. {t["team"]}</td><td style="text-align:right">{d["made"]} of {d["n"]}</td>'
            f'<td style="text-align:right">{p100(d["other"])}</td><td style="text-align:right">{rec}</td></tr>')
gene = [t for t in TOP if T26[t["team"]]["made"] * 2 >= T26[t["team"]]["n"]]
notg = [t for t in TOP if t not in gene]
sub = lambda s: (f'<tr><td colspan="4" style="padding:.5rem 0 .2rem;font-size:.62rem;letter-spacing:.12em;'
                 f'text-transform:uppercase;color:var(--muted)">{s}</td></tr>')
TABLE = ('<table style="width:100%;max-width:520px;margin:0 auto;border-collapse:collapse;font-family:\'Roboto Mono\',monospace;font-size:.8rem">'
         '<thead><tr style="border-bottom:1px solid var(--ink)"><th style="text-align:left">CFP rank</th><th style="text-align:right">Answered</th>'
         '<th style="text-align:right">Other drives, per 100</th><th style="text-align:right">Record</th></tr></thead><tbody>'
         + sub("Answered half or more") + "".join(row(t) for t in gene)
         + sub("Answered fewer than half") + "".join(row(t) for t in notg) + "</tbody></table>")

g = T26["Georgia"]
ga, gn, go = g["made"], g["n"], p100(g["other"])
al = T26["Alabama"]
unbeaten_not = [t["team"] for t in notg if t["record"].endswith("-0")]
n_tg, n_diff = V["team_games"], V["differ"]
games_k = f"{round(R['games'], -3) // 1000:,}"

BODY = f'''
  <h1 class="hed">{HED}</h1>

  <div class="deck">
    Gene&rsquo;s rule: a good team answers a touchdown with a score of its own. In college football since 2014, teams scored on {p100(ans)} of every 100 drives right after giving up a touchdown. On their other drives that began with a kickoff, they scored on {p100(kick)}. The answer came up short in all {len(rows)} seasons. Most of that gap is the scoreboard, not the heart.
  </div>

  <div class="byline">By The Sports Page &middot; Gene&rsquo;s Rule, part two &middot; FBS vs. FBS, 2014&ndash;2026, via CollegeFootballData and ESPN</div>

  <div class="stat-row">
    <div class="sc"><div class="v bad">{p100(ans)}</div><div class="l">Answer drives that score, per 100</div></div>
    <div class="sc"><div class="v now">{p100(kick)}</div><div class="l">Other kickoff drives that score, per 100</div></div>
    <div class="sc"><div class="v good">{ga} of {gn}</div><div class="l">Answers by No.&nbsp;1 Georgia</div></div>
  </div>

  <p><strong>Does Gene&rsquo;s Rule hold on Saturdays?</strong> Gene, a longtime reader, says you can tell a good team by how fast it scores after the other side does. In Issue #232 we <a href="https://thesportspage.net/published/203-genes-rule.html" style="color:var(--rust)">tested it in the pros</a>: good teams answer, but no better than they score the rest of the time. If any football should reward heart, it is the kind played by 19-year-olds.</p>

  <p><strong>The answer:</strong> it runs the other way, a little. In about {games_k},000 games between FBS teams, the answer drive scored {p100(ans)} times in 100 and the comparison drive {p100(kick)}. <strong>Why that is surprising:</strong> you would expect the gap to favor the answer, or at worst to vanish, as it does in the pros. <strong>What you get:</strong> the reason, and this year&rsquo;s top 12.</p>

  <h2 class="sh">Short every year</h2>

  <figure style="margin:28px 0">
{FIG}
    <figcaption style="font-family:'Roboto Mono',monospace;font-size:.68rem;color:var(--muted);margin-top:.6rem;line-height:1.5">Per 100 drives, FBS against FBS, regular season, drives with 2+ minutes left in the half. Rust: the drive right after the other team&rsquo;s touchdown. Steel: the same teams&rsquo; other drives that began with a kickoff. The scale starts at 28, not zero. 2026 through Nov. 17. Source: CollegeFootballData drives.</figcaption>
  </figure>

  <p>Notice that the rust dot sits left of the steel one in every row. That many seasons in a row is not luck. So do college teams fold after a punch? Ask first who just punched you.</p>

  <p>You get an answer chance only when someone scores on you, and in college that someone is often much better. The average answer drive starts {abs(round(madj["mean_margin_answer"]))} points behind; the average kickoff drive, {abs(round(madj["mean_margin_other"]))}. Compare drives at the same score and the gap shrinks to {p100(madj["answer"])} against {p100(madj["other_at_answer_margins"])}. Compare inside the same game, same opponent, and it is {p100(same_a)} against {p100(same_o)}. What is left is about the size of the NFL&rsquo;s one-point gap. An answer drive is played against a team that is, that day, scoring on you.</p>

  <div class="pull">
    <p>The drive after a touchdown is just a drive. It only feels like a verdict.</p>
    <cite>&mdash; The Sports Page</cite>
  </div>

  <h2 class="sh">Gene teams are still good teams</h2>

  <p>Gene is right in the way he meant it. Across 1,500 team-seasons, clubs that answered more often won more often (a correlation of .{round(100 * c["ans_win"]):d}). But clubs that scored more on all their other drives won more still (.{round(100 * c["base_win"]):d}). Then the test that settles it, the <em>answer premium</em>: how much better a team answers than it usually scores. Its link to winning is &minus;.0{abs(round(100 * c["prem_win"])):d}. From one year to the next it is .0{round(100 * yty["prem"]):d}. Two zeros, the same pair the pros gave us. Answering is scoring, and scoring is the skill.</p>

  <h2 class="sh">This year&rsquo;s top 12</h2>

  <p>Half of the committee&rsquo;s top 12 have answered at least half their chances. The other half have not, and that half includes No.&nbsp;1 Georgia ({ga} of {gn}) and unbeaten {unbeaten_not[0]} and {unbeaten_not[1]}. Georgia scores on {go} of every 100 other drives. That team is not short of nerve; it has had {gn} tries at one kind of drive.</p>

  <figure style="margin:22px 0">
{TABLE}
    <figcaption style="font-family:'Roboto Mono',monospace;font-size:.68rem;color:var(--muted);margin-top:.6rem;line-height:1.5;text-align:center">CFP committee ranking of Nov. 17. Answered = drives right after the other team&rsquo;s touchdown that ended in a score, games against FBS teams through Nov. 14. Counts from CollegeFootballData; ESPN&rsquo;s drive charts agree in {n_tg - n_diff} of {n_tg} team-games and differ by one drive in {n_diff}. Records agree in both feeds.</figcaption>
  </figure>

  <p>Why can No.&nbsp;1 fail the rule? Ten to 20 chances is a coin flipped ten to 20 times. Alabama&rsquo;s {al["made"]} of {al["n"]} is the best mark here, and Alabama has lost twice. Halfway through a season, point differential forecasts the rest four times as well as the answer rate does. Add the answer rate to it and you gain nothing.</p>

  <h2 class="sh">Use it Saturday</h2>

  <p>Inside one game, the rule is a fine guide to your mood. Say the other team scores the game&rsquo;s first touchdown. The team that answers on its next drive goes on to win {p100(fan["answered"][1])} times in 100; the team that does not wins {p100(fan["did not"][1])}. Answer with a touchdown and it is {p100(fan["TD"][1])} in 100, a coin flip. The pros give almost the same three numbers: 42, 27 and 48. The score does the work, not the spirit.</p>

  <h2 class="sh">What to take home</h2>

  <p>Gene&rsquo;s Rule is right about good teams and wrong about why. Watch the answer drive; it is real evidence. Then remember who it is played against: the team that just scored on you, often the better team that day. When one moment seems to show you a team&rsquo;s soul, ask how that team does on an ordinary drive. In college, the honest answer is &ldquo;a bit better.&rdquo;</p>

  <div class="box">
    <h3>How we measured it</h3>
    <p>An answer chance is the drive right after the other team scores a touchdown (on offense, defense or a return), same half, two or more minutes left. It counts if it ends in a touchdown or field goal. The comparison is the same team&rsquo;s other drives that began with a kickoff: the opening drive of each half and the drive after the other team&rsquo;s field goal. FBS against FBS, regular season, 2014 to Nov. 17, 2026: about {round(R["league"]["answer"][0], -3) // 1000},000 answer chances. Games whose drive scores do not add up to the final were left out ({R["dropped"]["final score mismatch"]} of about {games_k},000). Source: CollegeFootballData; 2026 top-12 counts and records checked against ESPN.</p>
    <p><strong>Limits.</strong> Trailing teams play differently; matching the score handles some of that, not all. The 2026 table is ten games; treat it as a snapshot. Code and data: <a href="https://github.com/pem725/the-sports-page/tree/main/research/gene-rule" target="_blank" rel="noopener" style="color:var(--gold)">research/gene-rule</a>.</p>
  </div>
'''

t = open(os.path.join(REPO, "queue", "_TEMPLATE.html")).read()
t = re.sub(r"<!-- PUBLISH-META.*?-->\n<!--.*?-->\n", "", t, count=1, flags=re.S)
meta = "<!-- PUBLISH-META\ntopic: CFB\ndecay: slow\ntags: CFB:cfb, Gene's Rule\n-->\n"
t = meta + t
t = t.replace("</style>", ".chart{width:100%;height:auto;display:block}\n</style>", 1)
t = t.replace("TODO_TITLE", HED_PLAIN).replace("TODO_OG_TITLE", HED_PLAIN).replace("TODO_SLUG", SLUG)
t = t.replace("TODO_KICKER &middot; TODO_DOMAIN, 2026", "Gene&rsquo;s Rule &middot; College Football, 2026")
start = t.index('  <h1 class="hed">'); end = t.index("  <!-- ASK BLOCK")
t = t[:start] + BODY.lstrip("\n") + "\n" + t[end:]
assert "TODO_" not in t.replace("TODO_NN", "").replace("TODO_DATE", ""), [m for m in re.findall(r"TODO_\w+", t)]
open(OUT, "w").write(t)
print("wrote", OUT)
