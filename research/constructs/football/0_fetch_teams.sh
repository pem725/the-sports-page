#!/bin/bash
# Team-season stats, 2014-2025. CFB: CFBD /stats/season (12 calls). NFL: nflverse stats_team.
# Load the key the house way; never echo it.
set -e; cd "$(dirname "$0")/data/raw/teams"
set -a; . ~/.config/secrets/tokens.env; set +a
for y in $(seq 2014 2025); do
  [ -s cfb$y.json ] || curl -s --compressed -H "Authorization: Bearer $CFBD_KEY" "https://api.collegefootballdata.com/stats/season?year=$y" -o cfb$y.json
  [ -s nfl$y.csv ]  || curl -sL -o nfl$y.csv https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_reg_$y.csv
done
