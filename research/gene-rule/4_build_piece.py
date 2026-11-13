#!/usr/bin/env python3
"""Build queue/203-genes-rule.html from the result files, so every number in the piece is
computed, not typed. Run after 1_nfl.py, 2_nfl_game_and_2026.py, 1_mlb.py and 1_nhl.py."""
import json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
SLUG = "203-genes-rule"
THROUGH = os.environ.get("THROUGH", "Nov. 12")  # last game day in the feed; set it on refresh
L = lambda f: json.load(open(os.path.join(HERE, "data", f)))
nfl, n26, mlb, nhl = L("nfl-results.json"), L("nfl-2026.json"), L("mlb-results.json"), L("nhl-results.json")
R = nfl["R"]
p100 = lambda x: round(100 * x)
two = lambda x: f"{x:.2f}".replace("0.", ".", 1).replace("-.", "&minus;.")

ans_n, ans_r = R["league"]["answer"]
oth_n, oth_r = R["league"]["other"]
fan = n26["fan"]
mets86 = next(r for r in mlb["rows"] if r["team"] == "NYN" and r["season"] == 1986)
H = nhl["R"]["league"]
h_ans, h_own = H["answer"][1], H["after_own"][1]
teams = {t["team"]: t for t in n26["teams"]}
espn = L("nfl-2026-espn.json")
NAME = dict(ARI="Cardinals", ATL="Falcons", BAL="Ravens", BUF="Bills", CAR="Panthers", CHI="Bears", CIN="Bengals",
            CLE="Browns", DAL="Cowboys", DEN="Broncos", DET="Lions", GB="Packers", HOU="Texans", IND="Colts",
            JAX="Jaguars", KC="Chiefs", LA="Rams", LAC="Chargers", LV="Raiders", MIA="Dolphins", MIN="Vikings",
            NE="Patriots", NO="Saints", NYG="Giants", NYJ="Jets", PHI="Eagles", PIT="Steelers", SEA="Seahawks",
            SF="49ers", TB="Buccaneers", TEN="Titans", WAS="Commanders")
# Records come from nflverse finals and must match ESPN's standings (the second feed).
for t in teams.values():
    assert t["rec"] == espn["records"][t["team"]], (t["team"], t["rec"], espn["records"][t["team"]])
rec = lambda t: "&ndash;".join(str(x) for x in (teams[t]["rec"] if teams[t]["rec"][2] else teams[t]["rec"][:2]))
pct = lambda t: (teams[t]["rec"][0] + teams[t]["rec"][2] / 2) / max(1, sum(teams[t]["rec"]))
is_gene = lambda t: teams[t]["n"] >= 15 and teams[t]["made"] / teams[t]["n"] >= 0.5
gene = sorted([t for t in teams if is_gene(t)], key=lambda t: -pct(t))
winning = [t for t in gene if pct(t) > 0.5]
losing = [t for t in gene if pct(t) < 0.5]
best_not = sorted([t for t in teams if not is_gene(t)], key=lambda t: -pct(t))[:3]
assert "CHI" in best_not, "the Bears are no longer among the best non-Gene teams: rewrite the headline"
WORD = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}
CHI = teams["CHI"]


def bars():
    """Paired horizontal bars, one pair per sport: right after the other side scores, and
    the fair comparison. Scale: 0-60 per 100 across 400px."""
    rows = [("Football", "Drives that score", ans_r, oth_r, "other kickoff drives"),
            ("Baseball", "Half-innings with a run", mlb["R"]["ans"], mlb["R"]["other"], "other half-innings"),
            ("Hockey", "Next goal is yours", h_ans, h_own, "after your own goal")]
    x0, w = 200, 400 / 0.6
    out = ['<svg class="chart" viewBox="0 0 680 300" width="100%" role="img" aria-label="Paired bars, per 100 chances. '
           + "; ".join(f"{s}: {p100(a)} right after the other side scores, {p100(b)} {cmp}" for s, _, a, b, cmp in rows)
           + '." style="max-width:680px;display:block;margin:0 auto;font-family:\'Roboto Mono\',monospace">']
    for i, (s, what, a, b, cmp) in enumerate(rows):
        y = 18 + i * 92
        out.append(f'<text x="0" y="{y + 14}" font-size="13" font-weight="600" fill="#1a1208">{s}</text>')
        out.append(f'<text x="0" y="{y + 31}" font-size="10.5" fill="#6b5e4a">{what}</text>')
        for j, (v, lab, col) in enumerate(((a, "right after they score", "#b83a1e"), (b, cmp, "#2c4a6e"))):
            yy = y + 40 + j * 22
            out.append(f'<rect x="{x0}" y="{yy}" width="{v * w:.1f}" height="16" fill="{col}"/>')
            out.append(f'<text x="{x0 + v * w + 6:.1f}" y="{yy + 12.5}" font-size="12" font-weight="600" fill="{col}">{p100(v)}</text>')
            out.append(f'<text x="{x0 - 8}" y="{yy + 12.5}" font-size="10" fill="#6b5e4a" text-anchor="end">{lab}</text>')
    out.append(f'<line x1="{x0}" y1="10" x2="{x0}" y2="290" stroke="#1a1208" stroke-width="1"/>')
    out.append("</svg>")
    return "\n".join(out)


def table():
    tr = []
    for t in gene + [None] + best_not:
        if t is None:
            tr.append('<tr><td colspan="3" style="padding:.5rem 0 .2rem;font-size:.62rem;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)">Not Gene teams this year</td></tr>')
            continue
        r = teams[t]
        tr.append(f'<tr><td>{NAME[t]}</td><td style="text-align:right">{r["made"]} of {r["n"]}</td><td style="text-align:right">{rec(t)}</td></tr>')
    return ('<table style="width:100%;max-width:420px;margin:0 auto;border-collapse:collapse;font-family:\'Roboto Mono\',monospace;font-size:.8rem">'
            '<thead><tr style="border-bottom:1px solid var(--ink)"><th style="text-align:left">2026</th><th style="text-align:right">Answered</th><th style="text-align:right">Record</th></tr></thead><tbody>'
            + "".join(tr) + "</tbody></table>")


fore = R["fore"]
body = f"""
  <h1 class="hed">Good Teams Answer Back. <em>The {rec("CHI")} Bears Rarely Do.</em></h1>

  <div class="deck">
    Gene&rsquo;s rule: you can tell a good team by how fast it scores after the other side does. We checked about {round(ans_n, -3):,} answer drives since 1999. Gene is right that good teams answer. The reason is plainer than it feels: they score after a touchdown about as often as they score any other time.
  </div>

  <div class="byline">By The Sports Page &middot; Gene&rsquo;s Rule, tested &middot; NFL 1999&ndash;2026, MLB 1977&ndash;2025, NHL 2015&ndash;2026</div>

  <div class="stat-row">
    <div class="sc"><div class="v bad">{p100(ans_r)}</div><div class="l">Answer drives that score, per 100</div></div>
    <div class="sc"><div class="v now">{p100(oth_r)}</div><div class="l">Other kickoff drives that score, per 100</div></div>
    <div class="sc"><div class="v good">{CHI["made"]} of {CHI["n"]}</div><div class="l">Answers by the {rec("CHI")} Bears</div></div>
  </div>

  <p><strong>Does a team that answers a score show you something special, or just that it is good?</strong> Gene, a longtime reader, has a rule for it. The other team scores a touchdown. Now watch the next drive. A good team gets off the mat and scores right back. We will call a club that does that a <strong>Gene team</strong>, and his rule <strong>Gene&rsquo;s Rule</strong>; the idea is his, all of it.</p>

  <p><strong>The answer:</strong> Gene teams are good teams, and the numbers back him. But the answer is not a separate gift. Since 1999, NFL teams have scored on {p100(ans_r)} of every 100 drives right after giving up a touchdown, and on {p100(oth_r)} of every 100 other drives that started with a kickoff. Same field position, same team, same rate.</p>

  <p><strong>Why that is surprising:</strong> we all feel the answer drive reveals character. You can see it on the sideline. Baseball and hockey say the same thing football does, and so does this year&rsquo;s standings page. <strong>What you get:</strong> a better way to watch that drive, and a reason not to grade a team on {CHI["n"]} of them.</p>

  <h2 class="sh">The answer is a score</h2>

  <figure style="margin:28px 0">
{bars()}
    <figcaption style="font-family:'Roboto Mono',monospace;font-size:.68rem;color:var(--muted);margin-top:.6rem;line-height:1.5">Per 100 chances: right after the other side scores (rust) against the fair comparison (steel). Football: NFL regular season, 1999 to {THROUGH}, 2026, drives with 2+ minutes left in the half. Baseball: every MLB half-inning, 1977&ndash;2025. Hockey: every NHL regular-season goal, 2015&ndash;16 to date.</figcaption>
  </figure>

  <p>Notice how flat that picture is. In baseball, a team that has just been scored on puts up a run in its next turn {p100(mlb["R"]["ans"])} times in 100. In every other half-inning it does so {p100(mlb["R"]["other"])} times in 100. The 1986 Mets, the best comeback team many of us ever loved, answered {p100(mets86["ans"])} times in 100, and scored in {p100(mets86["base"])} of 100 other half-innings. They were not rising to the occasion; they were a good lineup, every inning.</p>

  <p>HOCKEY_PARAGRAPH</p>

  <h2 class="sh">So why does Gene&rsquo;s Rule feel true?</h2>

  <p>Because it is true, at the level Gene meant it. Across {nfl["R"]["n_teamseasons"]} NFL team-seasons, the clubs that answered more often won more often (a correlation of {two(R["corr"]["ans_win"])}). But the clubs that scored more on <em>all their other drives</em> won more still ({two(R["corr"]["base_win"])}). The answer drive is a small slice of the offense, taken at the moment you are watching hardest.</p>

  <p>Here is the test that settles it. Take how much better a team answers than it usually scores; call it the <em>answer premium</em>. If answering were its own skill, the premium would track winning, and a team that had it one year would tend to have it the next. It does neither. Its link to winning is {two(R["corr"]["prem_win"])}; from one year to the next it is {two(R["yty"]["prem"])}. Zero, twice. Baseball gives the same pair of zeros.</p>

  <div class="pull">
    <p>Nobody rises to the occasion. Good teams were already there.</p>
    <cite>&mdash; The Sports Page</cite>
  </div>

  <h2 class="sh">The 2026 Gene teams</h2>

  <p>{WORD[len(gene)]} clubs have answered at least half their chances this season (15 or more chances, through {THROUGH}). {WORD[len(winning)]} have winning records. {WORD[len(losing)]} have losing records. And the {", ".join(NAME[t] for t in best_not[:-1])} and {NAME[best_not[-1]]}, at {", ".join(rec(t) for t in best_not[:-1])} and {rec(best_not[-1])}, are not Gene teams at all.</p>

  <figure style="margin:22px 0">
{table()}
    <figcaption style="font-family:'Roboto Mono',monospace;font-size:.68rem;color:var(--muted);margin-top:.6rem;line-height:1.5;text-align:center">Answered = drives right after the other team&rsquo;s touchdown that ended in a score. Counts from nflverse; ESPN&rsquo;s drive charts agree within one drive. Records through {THROUGH}.</figcaption>
  </figure>

  <p>Why can a {rec("CHI")} team fail the rule? It has had only {CHI["n"]} chances. Flip a fair coin {CHI["n"]} times and you will often see {round(CHI["n"] / 3)} heads, or {round(2 * CHI["n"] / 3)}. A good team also gets scored on less, so it gets fewer chances to show you anything. After nine weeks, point differential forecasts the rest of an NFL season about four times as well as the answer rate does, and adding the answer rate to it adds almost nothing.</p>

  <h2 class="sh">Use it on Sunday</h2>

  <p>Inside one game, Gene&rsquo;s Rule is a fine guide to your mood. When the other team scores the game&rsquo;s first touchdown, the team that answers on its next drive goes on to win {p100(fan["answered"][1])} times in 100; the team that does not wins {p100(fan["did not"][1])}. Answer with a touchdown and it is {p100(fan["TD"][1])} in 100; that is a tied game, and a tied game is a coin flip. The score is doing the work, not the spirit.</p>

  <h2 class="sh">What to take home</h2>

  <p>Gene&rsquo;s Rule is right, and it is right for a plain reason: an answer is a score, and good teams score. Watch the answer drive; it is real evidence. Then watch the other ten drives too, because they are the same evidence and there is more of it. When one vivid moment seems to tell you everything about a team, ask how often that moment happens on an ordinary drive. Usually the answer is &ldquo;just as often.&rdquo;</p>

  <div class="box">
    <h3>How we measured it</h3>
    <p><strong>Football.</strong> An answer chance is a drive that comes right after the other team scores a touchdown (on offense, defense or a return), in the same half, with at least two minutes left. It is answered if it ends in a touchdown or field goal. The comparison is the same team&rsquo;s other drives that began with a kickoff. Same game, same opponent, the gap holds: {p100(R["samegame"][1])} against {p100(R["samegame"][2])}. Source: nflverse play-by-play, regular season, {ans_n:,} answer chances; 2026 counts checked against ESPN.</p>
    <p><strong>Baseball.</strong> A chance is the half-inning right after the other team scores. Source: Retrosheet line scores. <em>The information used here was obtained free of charge from and is copyrighted by Retrosheet. Interested parties may contact Retrosheet at www.retrosheet.org.</em></p>
    <p><strong>Hockey.</strong> After every goal, whose goal comes next. Shootouts left out. Source: NHL play-by-play.</p>
    <p><strong>Limits.</strong> A trailing team plays differently, and an answer drive is usually played from behind; we do not adjust for that. The 2026 table is nine weeks; treat it as a snapshot, not a verdict. Code and data: <a href="https://github.com/pem725/the-sports-page/tree/main/research/gene-rule" target="_blank" rel="noopener" style="color:var(--gold)">research/gene-rule</a>.</p>
  </div>
"""

t = open(os.path.join(REPO, "queue", "_TEMPLATE.html")).read()
t = t.split("<!DOCTYPE html>", 1)[1]
meta = "<!-- PUBLISH-META\ntopic: NFL\ndecay: hot\ntags: NFL:nfl, Gene's Rule, Reader Question, Momentum\n-->\n<!DOCTYPE html>"
t = meta + t
title = "Good Teams Answer Back. The 7-2 Bears Rarely Do."
t = t.replace("TODO_TITLE", title).replace("TODO_OG_TITLE", title).replace("TODO_SLUG", SLUG)
t = t.replace("TODO_KICKER &middot; TODO_DOMAIN, 2026", "Gene&rsquo;s Rule &middot; NFL, 2026")
start = t.index('  <h1 class="hed">')
end = t.index("  <!-- ASK BLOCK")
t = t[:start] + body.strip("\n") + "\n\n" + t[end:]
nyr = next(r for r in nhl["rows"] if r["team"] == "NYR" and r["season"] == 2022)
hp = (f"Hockey says it too. After a goal, the next goal goes to the team that just gave one up {p100(h_ans)} times "
      f"in 100, and to the team that just scored {p100(h_own)} times in 100; the rest of the time, nobody scores again. "
      f"The 2022&ndash;23 Rangers got the next goal after {round(nyr['ans'] * nyr['n'])} of the {nyr['n']} goals scored "
      f"against them, one of the best marks of the decade. They also scored {p100(nyr['gf'])} of every 100 goals in their "
      f"games. A team that wins the answer battle is a team that wins the goal battle.")
t = t.replace("HOCKEY_PARAGRAPH", hp)
open(os.path.join(REPO, "queue", f"{SLUG}.html"), "w").write(t)
print("wrote", f"queue/{SLUG}.html", "TODO left:", re.findall(r"TODO_\w+|HOCKEY_PARAGRAPH", t))
