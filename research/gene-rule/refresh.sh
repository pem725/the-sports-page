#!/usr/bin/env bash
# Refresh the 2026 numbers behind Gene's Rule: nflverse 2026 drives, the team table, the
# ESPN second-feed check, and (while it is still queued) queue/203-genes-rule.html.
# Runs every morning in .github/workflows/autopublish.yml, BEFORE the publish, so the
# piece goes out on the freshest numbers both feeds share. By hand: research/gene-rule/refresh.sh
# The "through" date is computed from the feeds; THROUGH="Nov. 16" overrides it.
# Exit codes: 0 fine; 3 the headline no longer holds (Bears dropped out); other = a feed failed.
set -e
cd "$(dirname "$0")"
python3 0_nfl_drives.py 2026 2026
python3 1_nfl.py > /dev/null
python3 2_nfl_game_and_2026.py | tail -1
python3 3_verify_espn.py | tail -2
python3 - <<'PY'
import json, sys
mine = {t["team"]: t["rec"] for t in json.load(open("data/nfl-2026.json"))["teams"]}
same = json.load(open("data/nfl-2026-espn.json"))["records"]
bad = {t: (mine[t], same.get(t)) for t in mine if mine[t] != same.get(t)}
if bad: sys.exit(f"nflverse and ESPN disagree on records: {bad}")
PY
[ -f ../../queue/203-genes-rule.html ] || { echo "piece already published; data refreshed only"; exit 0; }
python3 4_build_piece.py || exit 3
cd ../.. && python3 scripts/add_topic_glyph.py queue/203-genes-rule.html
python3 scripts/check_scores.py queue/203-genes-rule.html | tail -2
