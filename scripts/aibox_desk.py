#!/usr/bin/env python3
"""The morning desk: routine checks run on the AI box before anyone is awake.

Set up 2026-10-25 on the editor's instruction to "use the aibox in the background
for simple tasks like queue management." It runs from the workstation's crontab
(LAN-only, like every AI-box tool) and does four things:

  1. QUEUE   -- queue_health.py: runway in days, topic clashes, stale pieces.
               The Oct 23-24 empty days happened because nobody looked; this looks.
  2. READ    -- cold_read.py on any queue file that is new or changed since the
               last morning, so a buried point is caught before it publishes.
  3. LEDGER  -- water_cooler.py: today's sports pages into the numbers ledger.
  4. REPORT  -- one short file, ~/.local/share/sports-page/desk-report.md, which
               the next Claude session reads first.

It never edits a queued piece, never commits, never pushes. The publishing bot in
GitHub Actions stays the only thing that ships. A problem becomes a line in the
report, and a short runway (two days or less) also becomes a desktop notice.

Usage:
  python3 scripts/aibox_desk.py            # the full morning run
  python3 scripts/aibox_desk.py --no-ledger
Crontab (installed 2026-10-25):
  50 5 * * * cd ~/GitTemp/the-sports-page && /usr/bin/python3 scripts/aibox_desk.py >> ~/.sports-page-desk.log 2>&1
"""
import argparse, datetime as dt, json, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.expanduser("~/.local/share/sports-page")
REPORT = os.path.join(STATE, "desk-report.md")
SEEN = os.path.join(STATE, "desk-seen.json")


def run(args, timeout=1800):
    p = subprocess.run([sys.executable] + args, cwd=REPO, capture_output=True, text=True, timeout=timeout)
    return (p.stdout + p.stderr).strip()


def notify(msg):
    try:
        subprocess.run(["notify-send", "The Sports Page desk", msg], timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--no-ledger", action="store_true")
    a = ap.parse_args()
    os.makedirs(STATE, exist_ok=True)
    now = dt.datetime.now()
    out = [f"# Desk report — {now:%A %Y-%m-%d %H:%M}", ""]

    # Step 0 of CLAUDE.md applies to robots too: the 4:30am bot may already have
    # published and pushed. Fast-forward only, so local work is never touched; if
    # it cannot fast-forward, say so and read the clone as it stands.
    pull = subprocess.run(["git", "pull", "--ff-only", "-q", "origin", "main"], cwd=REPO,
                          capture_output=True, text=True, timeout=120)
    if pull.returncode:
        out += [f"**Could not fast-forward the clone** ({pull.stderr.strip()[:200]}). Figures below may be stale.", ""]

    # 1. queue
    q = run(["scripts/queue_health.py"])
    m = re.search(r"(\d+) issues? queued, running through (\w+ \w+ \d+)", q)
    queued = int(m.group(1)) if m else 0
    out += ["## Queue", "", "```", q[-2500:], "```", ""]
    if queued <= 2:
        msg = f"Queue runway is {queued} issue(s). Write or schedule something."
        out.insert(2, f"**{msg}**\n"); notify(msg)

    # 2. cold-read new or changed queue files
    seen = json.load(open(SEEN)) if os.path.exists(SEEN) else {}
    qdir = os.path.join(REPO, "queue")
    order = [l.strip() for l in open(os.path.join(REPO, "QUEUE_ORDER.txt")) if l.strip()]
    fresh = [f"queue/{f}" for f in order            # scheduled pieces only; benched files are left alone
             if os.path.isfile(os.path.join(qdir, f))
             and seen.get(f) != os.path.getmtime(os.path.join(qdir, f))]
    out += ["## Cold reads (new or changed pieces)", ""]
    if fresh:
        out += ["```", run(["scripts/cold_read.py"] + fresh, timeout=3600)[-6000:], "```", ""]
        for f in fresh:
            seen[os.path.basename(f)] = os.path.getmtime(os.path.join(REPO, f))
        json.dump(seen, open(SEEN, "w"))
    else:
        out += ["Nothing new in the queue since the last read.", ""]

    # 3. ledger
    if not a.no_ledger:
        led = run(["scripts/water_cooler.py", "--limit", "80"], timeout=5400)
        last = led.splitlines()[-1] if led else "no output"
        out += ["## Water-cooler ledger", "", last, "", "```", run(["scripts/water_cooler.py", "--report"])[-3000:], "```", ""]

    open(REPORT, "w").write("\n".join(out) + "\n")
    print("\n".join(out[:4]))
    print(f"report: {REPORT}")


if __name__ == "__main__":
    main()
