"""Per-game excitement summary from nflverse play-by-play (1999-2025, REG).
excitement = sum |delta home_wp| across plays, plus a final step to the result (1/0/0.5).
lead_changes = sign flips of the score margin (ties skipped).
q4_comeback = eventual winner trailed at some point in the fourth quarter (or OT start) ; trailed_entering_q4 also stored.
Input: ~/.cache/sports-page/nflverse/pbp/play_by_play_YYYY.csv.gz (nflverse-data releases)."""
import csv, gzip, os, sys
csv.field_size_limit(10**9)
D = os.path.expanduser('~/.cache/sports-page/nflverse/pbp')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'pbp_game_summary.csv')
rows_out = []
for y in range(1999, 2026):
    games = {}
    with gzip.open(f'{D}/play_by_play_{y}.csv.gz', 'rt') as f:
        for r in csv.DictReader(f):
            if r.get('season_type') and r['season_type'] != 'REG':
                continue
            g = games.setdefault(r['game_id'], {'wp': [], 'marg': [], 'q4trail_home': False, 'q4trail_away': False,
                                               'enter_q4': None, 'home': r['home_team'], 'away': r['away_team']})
            try:
                hs, as_ = float(r['total_home_score']), float(r['total_away_score'])
            except ValueError:
                hs = as_ = None
            q = r['qtr']
            if hs is not None:
                g['marg'].append(hs - as_)
                if q and int(float(q)) >= 4:
                    if g['enter_q4'] is None:
                        g['enter_q4'] = hs - as_
                    if hs < as_: g['q4trail_home'] = True
                    if as_ < hs: g['q4trail_away'] = True
            if r['home_wp'] not in ('', 'NA'):
                g['wp'].append(float(r['home_wp']))
    for gid, g in games.items():
        m = [x for x in g['marg'] if x != 0]
        fin = g['marg'][-1] if g['marg'] else 0
        lc = sum(1 for a, b in zip(m, m[1:]) if (a > 0) != (b > 0))
        res = 1.0 if fin > 0 else 0.0 if fin < 0 else 0.5
        wp = g['wp'] + [res]
        exc = sum(abs(b - a) for a, b in zip(wp, wp[1:]))
        winner_home = fin > 0
        comeback = (g['q4trail_home'] if winner_home else g['q4trail_away']) if fin != 0 else False
        eq4 = g['enter_q4'] if g['enter_q4'] is not None else fin
        trailed_entering = (eq4 < 0 if winner_home else eq4 > 0) if fin != 0 else False
        rows_out.append(dict(game_id=gid, season=y, n_wp=len(g['wp']), excitement=round(exc, 4),
                             lead_changes=lc, q4_comeback=int(comeback), trailed_entering_q4=int(trailed_entering),
                             pbp_final_margin=fin))
    print(y, len(games), file=sys.stderr)
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows_out[0]))
    w.writeheader(); w.writerows(rows_out)
print(len(rows_out))
