#!/usr/bin/env python3
"""Campaign log and ABA chart for the board.

The editor, 2026-11-16: evaluate ad campaigns with ABA (reversal) designs and tune
the paper over the run to Issue #500. A reversal design is only honest if every
phase change is written down WHEN it happens, so this keeps a timestamped log and
the board draws the daily series with the phases shaded behind it.

    python3 scripts/campaigns.py --phase A "baseline"          # start a phase today
    python3 scripts/campaigns.py --phase B "ad: r/CFB post" --tag rcfb
    python3 scripts/campaigns.py --idea "trade a link with a Bills podcast"
    python3 scripts/campaigns.py --link rcfb                   # a tagged URL to send
    python3 scripts/campaigns.py --list
    python3 scripts/campaigns.py --print                       # the series, as text

The log (data/campaign-log.json) holds phases and ideas only -- no counts -- so it
can live in the public repo. The numbers are fetched at board build time and shown
only inside the locked page, like readership_stats.py.

Outcome measures, in order of usefulness at our size (10 subscribers, ~10 visits a
day, Nov 2026):
  visits/day        the main ABA outcome; it can go up AND come back down
  tagged visits     visits that arrived on a campaign link (?ref=TAG), by tag
  new subs/day      mostly zeros for now; shown, not tested
  opens per issue   per email, for the record
Cumulative subscribers can never reverse, so it is never the ABA outcome.
"""
import argparse
import datetime
import html as H
import json
import os
import re
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOG = REPO / "data" / "campaign-log.json"
GC = "https://thesportspage.goatcounter.com/api/v0"
BD = "https://api.buttondown.com/v1"
SITE = "https://thesportspage.net/"
DAYS = 84  # twelve weeks on the chart


# ---------- the log ----------

def load():
    if LOG.exists():
        return json.loads(LOG.read_text())
    return {"phases": [], "ideas": []}


def save(log):
    LOG.write_text(json.dumps(log, indent=1, ensure_ascii=False) + "\n")


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="minutes")


def add_phase(log, label, what, tag=None, start=None):
    start = start or datetime.date.today().isoformat()
    if log["phases"] and start < log["phases"][-1]["start"]:
        raise SystemExit("a phase cannot start before the last one; the log only moves forward")
    log["phases"].append({"start": start, "label": label, "what": what, "tag": tag, "logged": now_iso()})


def link(tag, path=""):
    # GoatCounter files ?ref= as the referrer, so a tagged visit shows up by name.
    return f"{SITE}{path}?ref={tag}"


# ---------- the series ----------

def _get(url, auth):
    req = urllib.request.Request(url, headers={"Authorization": auth, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def visits(start, end):
    tok = os.environ.get("GOATCOUNTER_TOKEN")
    if not tok:
        return {}
    r = _get(f"{GC}/stats/total?start={start}&end={end}", f"Bearer {tok}")
    return {d["day"]: d["daily"] for d in r.get("stats", [])}


def tagged(start, end, tags):
    """Visits per campaign tag over the window (GoatCounter referrers)."""
    tok = os.environ.get("GOATCOUNTER_TOKEN")
    if not tok or not tags:
        return {}
    r = _get(f"{GC}/stats/toprefs?start={start}&end={end}&limit=100", f"Bearer {tok}")
    out = {}
    for h in r.get("stats", []):
        name = (h.get("name") or "").lower()
        for t in tags:
            if name == t.lower() or name.endswith("/" + t.lower()):
                out[t] = out.get(t, 0) + h.get("count", 0)
    return out


def subs_and_opens(start):
    key = os.environ.get("BUTTONDOWN_KEY")
    if not key:
        return {}, []
    auth = f"Token {key}"
    new, url = {}, f"{BD}/subscribers?type=regular&page_size=100&ordering=-creation_date"
    while url:
        page = _get(url, auth)
        stop = False
        for r in page["results"]:
            d = r["creation_date"][:10]
            if d < start:
                stop = True
                break
            new[d] = new.get(d, 0) + 1
        url = None if stop else page.get("next")
    opens = []
    for e in _get(f"{BD}/emails?page_size=100&ordering=-publish_date", auth)["results"]:
        d = (e.get("publish_date") or "")[:10]
        a = e.get("analytics") or {}
        if d >= start and a.get("opens") is not None:
            opens.append((d, a["opens"], a.get("recipients")))
    return new, sorted(opens)


def series(today=None):
    today = today or datetime.date.today()
    end = today - datetime.timedelta(days=1)          # yesterday: today is still filling
    start = end - datetime.timedelta(days=DAYS - 1)
    days = [(start + datetime.timedelta(days=i)).isoformat() for i in range(DAYS)]
    v = visits(start.isoformat(), end.isoformat())
    new, opens = subs_and_opens(start.isoformat())
    log = load()
    tags = sorted({p["tag"] for p in log["phases"] if p.get("tag")})
    return {"days": days, "visits": [v.get(d) for d in days], "new": [new.get(d, 0) for d in days],
            "opens": opens, "tagged": tagged(start.isoformat(), end.isoformat(), tags),
            "phases": log["phases"]}


def phase_of(day, phases):
    cur = None
    for p in phases:
        if p["start"] <= day:
            cur = p
    return cur


def phase_verdict(phase_visits, baseline_visits):
    """Decide what the board says about one phase against the baseline before it.

    phase_visits, baseline_visits: lists of daily visit counts (ints), one per day.
    Return a short string for the board (e.g. "up, clears baseline range"), or None
    to say nothing. TODO(editor): the decision rule is yours to set.
    """
    return None


# ---------- the board section ----------

def board_section(s):
    vals = [x for x in s["visits"] if x is not None]
    if not vals:
        return ""
    W, Hh, L, R, T, B = 760, 220, 34, 10, 14, 26
    n = len(s["days"])
    ymax = max(max(vals), 5)
    x = lambda i: L + i * (W - L - R) / (n - 1)
    y = lambda v: T + (Hh - T - B) * (1 - v / ymax)
    parts = []
    # phase shading: B-type phases (anything not "A") get the gold wash
    for k, p in enumerate(s["phases"]):
        if p["start"] > s["days"][-1]:
            continue
        i0 = max(s["days"].index(p["start"]) if p["start"] in s["days"] else 0, 0)
        nxt = s["phases"][k + 1]["start"] if k + 1 < len(s["phases"]) else None
        i1 = s["days"].index(nxt) if nxt in s["days"] else n - 1
        if p["label"].upper() != "A":
            parts.append(f'<rect x="{x(i0):.1f}" y="{T}" width="{max(x(i1) - x(i0), 2):.1f}" '
                         f'height="{Hh - T - B}" fill="#c9962a" opacity=".18"/>')
        parts.append(f'<line x1="{x(i0):.1f}" x2="{x(i0):.1f}" y1="{T}" y2="{Hh - B}" stroke="#6b5e4a" stroke-dasharray="3 3"/>'
                     f'<text x="{x(i0) + 3:.1f}" y="{T + 10}" font-size="11" fill="#6b5e4a">{H.escape(p["label"])}</text>')
    pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(s["visits"]) if v is not None)
    parts.append(f'<polyline points="{pts}" fill="none" stroke="#2c4a6e" stroke-width="1.6"/>')
    for i, v in enumerate(s["new"]):
        if v:
            parts.append(f'<circle cx="{x(i):.1f}" cy="{Hh - B + 8}" r="{2 + v}" fill="#b83a1e"><title>{s["days"][i]}: {v} new</title></circle>')
    for t in (0, ymax // 2, ymax):
        parts.append(f'<text x="{L - 4}" y="{y(t) + 4:.1f}" font-size="10" text-anchor="end" fill="#6b5e4a">{t}</text>')
    for i in (0, n // 2, n - 1):
        parts.append(f'<text x="{x(i):.1f}" y="{Hh - 2}" font-size="10" text-anchor="middle" fill="#6b5e4a">{s["days"][i][5:]}</text>')
    svg = (f'<svg viewBox="0 0 {W} {Hh}" width="100%" role="img" aria-label="Site visits per day with campaign phases" '
           f'style="font-family:Roboto Mono,monospace">{"".join(parts)}</svg>')

    rows = []
    for k, p in enumerate(s["phases"]):
        nxt = s["phases"][k + 1]["start"] if k + 1 < len(s["phases"]) else None
        dv = [v for d, v in zip(s["days"], s["visits"]) if v is not None and d >= p["start"] and (not nxt or d < nxt)]
        base = []
        if k:
            q = s["phases"][k - 1]
            base = [v for d, v in zip(s["days"], s["visits"]) if v is not None and q["start"] <= d < p["start"]]
        verdict = phase_verdict(dv, base) if base and dv else None
        tagn = s["tagged"].get(p.get("tag")) if p.get("tag") else None
        rows.append(f'<tr><td>{H.escape(p["label"])}</td><td>{p["start"]}</td><td>{H.escape(p["what"])}</td>'
                    f'<td>{len(dv)}</td><td>{(sum(dv) / len(dv)):.0f}</td>'
                    f'<td>{"" if tagn is None else tagn}</td><td>{H.escape(verdict or "")}</td></tr>' if dv else
                    f'<tr><td>{H.escape(p["label"])}</td><td>{p["start"]}</td><td>{H.escape(p["what"])}</td>'
                    f'<td>0</td><td></td><td></td><td>starts counting tomorrow</td></tr>')
    table = ('<table class="camp"><tr><th>Phase</th><th>Began</th><th>What changed</th><th>Days</th>'
             '<th>Visits/day</th><th>Tagged visits</th><th>Call</th></tr>' + "".join(rows) + '</table>') if rows else \
        '<p>No phases logged yet. Start the baseline: <code>python3 scripts/campaigns.py --phase A "baseline"</code></p>'
    ideas = load().get("ideas", [])
    idea_html = ("<p><strong>Campaign ideas waiting:</strong></p><ul>" +
                 "".join(f"<li>{H.escape(i['text'])}</li>" for i in ideas if not i.get("used")) + "</ul>") if ideas else ""
    return ('\n  <section class="campaigns" aria-label="Campaign tests">\n'
            '  <h2>Campaign tests (ABA)</h2>\n'
            '  <p>Site visits per day, last twelve weeks. Gold = a campaign phase; dashed line = a logged change. '
            'Red dots = new subscribers that day. Judge a phase by visits a day, which can rise and fall back; '
            'total subscribers never fall back, so they cannot show a reversal.</p>\n  '
            + svg + "\n  " + table + "\n  " + idea_html + "\n  </section>\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", nargs=2, metavar=("LABEL", "WHAT"))
    ap.add_argument("--tag", help="campaign tag for this phase's links (?ref=TAG)")
    ap.add_argument("--start", help="phase start date YYYY-MM-DD (default today)")
    ap.add_argument("--idea")
    ap.add_argument("--link", metavar="TAG")
    ap.add_argument("--path", default="", help="page for --link, e.g. published/sunday-032.html")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--print", dest="show", action="store_true")
    a = ap.parse_args()
    log = load()
    if a.phase:
        add_phase(log, a.phase[0], a.phase[1], a.tag, a.start)
        save(log)
        print(f"phase {a.phase[0]} from {log['phases'][-1]['start']}: {a.phase[1]}")
        if a.tag:
            print("send this link:", link(a.tag, a.path))
    if a.idea:
        log["ideas"].append({"text": a.idea, "added": now_iso()})
        save(log)
        print("idea logged")
    if a.link:
        print(link(a.link, a.path))
    if a.list:
        for p in log["phases"]:
            print(f'{p["start"]}  {p["label"]:3s} {p["what"]}' + (f'  [ref={p["tag"]}]' if p.get("tag") else ""))
        for i in log["ideas"]:
            print(f'  idea: {i["text"]}')
    if a.show:
        s = series()
        for d, v, nw in zip(s["days"], s["visits"], s["new"]):
            p = phase_of(d, s["phases"])
            print(d, f"{v if v is not None else '-':>4}", "+" * nw, p["label"] if p else "")
        print("opens per issue:", s["opens"][-7:])
        print("tagged:", s["tagged"])


if __name__ == "__main__":
    main()
