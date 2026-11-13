#!/usr/bin/env bash
# Refresh the 2026 numbers in queue/203-genes-rule.html the day before it publishes.
# Usage: THROUGH="Nov. 16" research/gene-rule/refresh.sh
set -e
cd "$(dirname "$0")"
python3 0_nfl_drives.py 2026 2026
python3 1_nfl.py > /dev/null
python3 2_nfl_game_and_2026.py | tail -1
python3 3_verify_espn.py | tail -1        # must say: records differing from ESPN: none
python3 4_build_piece.py
cd ../.. && python3 scripts/add_topic_glyph.py queue/203-genes-rule.html
python3 scripts/check_scores.py queue/203-genes-rule.html | tail -2
