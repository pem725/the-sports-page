"""Thanksgiving NFL games 1999-2025: Lions/Cowboys records vs market, excitement, playoff stakes; 2026 slate.
Sources: nflverse games (research/momentum/nfl/data/games.csv), nflverse pbp summary (data/pbp_game_summary.csv,
built by 1_pbp_excitement.py), data/nfl-odds.json (the paper's Odds Board, generated 2026-11-17)."""
import csv, json, math, os, statistics as st
from collections import defaultdict, Counter
import numpy as np

H = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(H, '..', '..'))
SD = 13.5
Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))

def ml_prob(m):
    m = float(m); return -m / (-m + 100) if m < 0 else 100 / (m + 100)

games = [r for r in csv.DictReader(open(f'{REPO}/research/momentum/nfl/data/games.csv'))]
def is_tg(r):
    return r['weekday'] == 'Thursday' and r['gameday'][5:7] == '11' and 22 <= int(r['gameday'][8:]) <= 28 and r['game_type'] == 'REG'

def home_p(r):
    """market chance home wins: vig-free moneyline if present, else spread through normal sd 13.5"""
    p_spread = Phi(float(r['spread_line']) / SD) if r['spread_line'] else None
    if r['home_moneyline'] and r['away_moneyline']:
        h, a = ml_prob(r['home_moneyline']), ml_prob(r['away_moneyline'])
        return h / (h + a), p_spread, 'ml'
    return p_spread, p_spread, 'spread'

done = [r for r in games if r['result'] != '' and 1999 <= int(r['season']) <= 2025]
reg = [r for r in done if r['game_type'] == 'REG']
for r in reg:
    r['tg'] = is_tg(r); r['res'] = float(r['result'])
    r['hp'], r['hp_spread'], r['psrc'] = home_p(r)
tg = [r for r in reg if r['tg']]
other = [r for r in reg if not r['tg']]
out = {'sample': {'seasons': '1999-2025', 'reg_games': len(reg), 'thanksgiving_games': len(tg)}}

# ---------- Q1 team records ----------
def team_view(team):
    rows = []
    for r in reg:
        if team not in (r['home_team'], r['away_team']): continue
        home = r['home_team'] == team
        m = r['res'] if home else -r['res']
        p = r['hp'] if home else 1 - r['hp']
        ps = r['hp_spread'] if home else 1 - r['hp_spread']
        rows.append(dict(season=r['season'], date=r['gameday'], opp=r['away_team'] if home else r['home_team'], home=home,
                         won=1.0 if m > 0 else 0.0 if m < 0 else 0.5, margin=m, p=p, p_spread=ps, tg=r['tg'],
                         score=f"{r['home_score'] if home else r['away_score']}-{r['away_score'] if home else r['home_score']}"))
    return rows

def rec(rows):
    w = sum(1 for x in rows if x['won'] == 1); l = sum(1 for x in rows if x['won'] == 0); t = sum(1 for x in rows if x['won'] == .5)
    return f'{w}-{l}' + (f'-{t}' if t else '')

teamq = {}
for team in ('DET', 'DAL'):
    rows = team_view(team)
    t = [x for x in rows if x['tg']]
    seasons = {x['season'] for x in t}
    o = [x for x in rows if not x['tg'] and x['season'] in seasons]
    teamq[team] = dict(
        tg_record=rec(t), tg_n=len(t), tg_win_per_100=round(100 * st.mean(x['won'] for x in t)),
        other_games_same_seasons_record=rec(o), other_win_per_100=round(100 * st.mean(x['won'] for x in o)),
        tg_expected_wins_market=round(sum(x['p'] for x in t), 1), tg_expected_wins_spread_only=round(sum(x['p_spread'] for x in t), 1),
        tg_actual_wins=sum(x['won'] for x in t),
        other_expected_wins_market=round(sum(x['p'] for x in o), 1), other_actual_wins=sum(x['won'] for x in o),
        tg_favored=sum(1 for x in t if x['p'] > .5), tg_record_when_favored=rec([x for x in t if x['p'] > .5]),
        tg_record_when_underdog=rec([x for x in t if x['p'] < .5]),
        opponents=Counter(x['opp'] for x in t).most_common(),
        opponents_beat_them=Counter(x['opp'] for x in t if x['won'] == 0).most_common(),
        games=[{k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items() if k != 'tg'} for x in t])
    # binomial: chance of <= actual wins given market probabilities (Poisson-binomial via DP)
    dist = np.zeros(len(t) + 1); dist[0] = 1
    for x in t:
        dist[1:] = dist[1:] * (1 - x['p']) + dist[:-1] * x['p']; dist[0] *= (1 - x['p'])
    k = int(sum(1 for x in t if x['won'] == 1))
    teamq[team]['p_this_few_or_fewer_wins_given_market'] = round(float(dist[:k + 1].sum()), 2)
    teamq[team]['p_this_many_or_more_wins_given_market'] = round(float(dist[k:].sum()), 2)
    # Dallas never in Lions TG
teamq['DET']['games_vs_DAL'] = sum(1 for x in team_view('DET') if x['tg'] and x['opp'] == 'DAL')
teamq['DET']['games_vs_NFC_North'] = sum(1 for x in team_view('DET') if x['tg'] and x['opp'] in ('CHI', 'GB', 'MIN'))
out['q1_teams'] = teamq

# ---------- Q2 boring? ----------
pbp = {r['game_id']: r for r in csv.DictReader(open(f'{H}/data/pbp_game_summary.csv'))}
def boring(rows):
    have = [r for r in rows if r['game_id'] in pbp and int(pbp[r['game_id']]['n_wp']) > 50]
    exc = [float(pbp[r['game_id']]['excitement']) for r in have]
    fav = [max(r['hp'], 1 - r['hp']) for r in rows]
    return dict(n=len(rows), within8_per_100=round(100 * st.mean(abs(r['res']) <= 8 for r in rows)),
                within3_per_100=round(100 * st.mean(abs(r['res']) <= 3 for r in rows)),
                mean_abs_margin=round(st.mean(abs(r['res']) for r in rows), 1),
                ot_per_100=round(100 * st.mean(r['overtime'] == '1' for r in rows)),
                favorite_chance_mean=round(st.mean(fav), 2), tossups_55_or_less_per_100=round(100 * st.mean(f <= .55 for f in fav)),
                n_pbp=len(have), excitement_mean=round(st.mean(exc), 2), excitement_median=round(st.median(exc), 2),
                excitement_se=round(st.stdev(exc) / math.sqrt(len(exc)), 2),
                lead_changes_mean=round(st.mean(int(pbp[r['game_id']]['lead_changes']) for r in have), 2),
                q4_comeback_per_100=round(100 * st.mean(int(pbp[r['game_id']]['q4_comeback']) for r in have)),
                trailed_entering_q4_won_per_100=round(100 * st.mean(int(pbp[r['game_id']]['trailed_entering_q4']) for r in have)))
allexc = sorted(float(pbp[r['game_id']]['excitement']) for r in reg if r['game_id'] in pbp)
def pct(x): return round(100 * sum(1 for v in allexc if v < x) / len(allexc))
q2 = dict(thanksgiving=boring(tg), all_other_reg=boring(other),
          other_thursday=boring([r for r in other if r['weekday'] == 'Thursday']),
          same_week_sunday=boring([r for r in other if r['weekday'] == 'Sunday' and any(t['season'] == r['season'] and t['week'] == r['week'] for t in tg)]))
ranked = sorted([r for r in tg if r['game_id'] in pbp], key=lambda r: -float(pbp[r['game_id']]['excitement']))
fmt = lambda r: dict(game=f"{r['gameday']} {r['away_team']} {r['away_score']} at {r['home_team']} {r['home_score']}" + (' (OT)' if r['overtime'] == '1' else ''),
                     excitement=round(float(pbp[r['game_id']]['excitement']), 2), percentile_all_games=pct(float(pbp[r['game_id']]['excitement'])),
                     lead_changes=int(pbp[r['game_id']]['lead_changes']), q4_comeback=int(pbp[r['game_id']]['q4_comeback']))
q2['most_exciting_tg'] = [fmt(r) for r in ranked[:5]]
q2['least_exciting_tg'] = [fmt(r) for r in ranked[-5:]]
tgexc = [float(pbp[r['game_id']]['excitement']) for r in ranked]
q2['tg_games_above_league_median_excitement'] = f"{sum(1 for v in tgexc if v > st.median(allexc))} of {len(tgexc)}"
# by slot
for name, f in (('lions_games', lambda r: r['home_team'] == 'DET'), ('cowboys_games', lambda r: r['home_team'] == 'DAL'),
                ('night_or_third_game', lambda r: r['home_team'] not in ('DET', 'DAL'))):
    q2['tg_' + name] = boring([r for r in tg if f(r)])
# permutation p-value for excitement mean
rng = np.random.default_rng(1)
pool = np.array(allexc); n = len(tgexc); obs = np.mean(tgexc) - np.mean(pool)
perm = [rng.choice(pool, n, replace=False).mean() - pool.mean() for _ in range(20000)]
q2['excitement_diff_tg_minus_all'] = round(float(obs), 2)
q2['excitement_perm_p_two_sided'] = round(float(np.mean(np.abs(perm) >= abs(obs))), 2)
w8 = [abs(r['res']) <= 8 for r in reg]; k8 = sum(abs(r['res']) <= 8 for r in tg)
perm8 = [sum(rng.choice(w8, n, replace=False)) for _ in range(20000)]
q2['within8_perm_p_two_sided'] = round(float(np.mean(np.abs(np.array(perm8) - np.mean(w8) * len(tg)) >= abs(k8 - np.mean(w8) * len(tg)))), 2)
out['q2_boring'] = q2

# ---------- Q3 stakes ----------
playoffs = defaultdict(set)
for r in done:
    if r['game_type'] != 'REG':
        playoffs[r['season']].update([r['home_team'], r['away_team']])
# pregame records
tg_weeks = {(r['season'], r['week']) for r in tg}
recs = defaultdict(lambda: [0.0, 0.0]); rows3 = []
for r in sorted(reg, key=lambda r: (r['season'], r['gameday'], r['game_id'])):
    for team, opp, m in ((r['home_team'], r['away_team'], r['res']), (r['away_team'], r['home_team'], -r['res'])):
        w, gp = recs[(r['season'], team)]
        if (r['season'], r['week']) in tg_weeks:
            rows3.append(dict(season=r['season'], game_id=r['game_id'], team=team, tg=r['tg'], wpct=w / gp if gp else .5, gp=gp,
                              won=1.0 if m > 0 else 0.0 if m < 0 else 0.5, po=int(team in playoffs[r['season']])))
    for team, m in ((r['home_team'], r['res']), (r['away_team'], -r['res'])):
        x = recs[(r['season'], team)]; x[0] += 1 if m > 0 else .5 if m == 0 else 0; x[1] += 1
X = lambda d, won: np.array([1, d['wpct'], d['wpct'] ** 2, won, won * d['wpct'], won * d['wpct'] ** 2, d['gp']])
A = np.array([X(d, d['won']) for d in rows3]); y = np.array([d['po'] for d in rows3])
b = np.zeros(A.shape[1])
for _ in range(50):
    p = 1 / (1 + np.exp(-A @ b)); W = p * (1 - p)
    b = b + np.linalg.solve(A.T @ (A * W[:, None]) + 1e-6 * np.eye(len(b)), A.T @ (y - p))
pr = lambda d, won: float(1 / (1 + np.exp(-X(d, won) @ b)))
for d in rows3: d['lev'] = pr(d, 1) - pr(d, 0)
lt = [d['lev'] for d in rows3 if d['tg']]; lo = [d['lev'] for d in rows3 if not d['tg']]
def gamepairs(f):
    by = defaultdict(list)
    for d in rows3:
        if f(d): by[d['game_id']].append(d)
    g = [v for v in by.values() if len(v) == 2]
    return dict(games=len(g), both_losing_record_per_100=round(100 * st.mean(all(x['wpct'] < .5 for x in v) for v in g)),
                both_winning_record_per_100=round(100 * st.mean(all(x['wpct'] > .5 for x in v) for v in g)),
                both_made_playoffs_per_100=round(100 * st.mean(all(x['po'] for x in v) for v in g)),
                neither_made_playoffs_per_100=round(100 * st.mean(not any(x['po'] for x in v) for v in g)),
                game_leverage_mean_pts=round(100 * st.mean(sum(x['lev'] for x in v) for v in g), 1))
q3 = dict(model='logit(made playoffs) ~ wpct + wpct^2 + won*(1 + wpct + wpct^2) + games played; fit on all team-games in Thanksgiving weeks 1999-2025',
          n_team_games=len(rows3), n_tg_team_games=len(lt),
          leverage_tg_mean_pts=round(100 * st.mean(lt), 1), leverage_other_same_week_mean_pts=round(100 * st.mean(lo), 1),
          leverage_tg_median_pts=round(100 * st.median(lt), 1), leverage_other_median_pts=round(100 * st.median(lo), 1),
          raw_po_rate_tg_teams_per_100=round(100 * st.mean(d['po'] for d in rows3 if d['tg'])),
          raw_po_rate_other_per_100=round(100 * st.mean(d['po'] for d in rows3 if not d['tg'])),
          tg_games=gamepairs(lambda d: d['tg']), other_games_same_week=gamepairs(lambda d: not d['tg']))
# raw conditional: winners vs losers within tg and other
for lab, f in (('tg', True), ('other', False)):
    sub = [d for d in rows3 if d['tg'] == f]
    q3[f'raw_po_if_won_{lab}'] = round(100 * st.mean(d['po'] for d in sub if d['won'] == 1))
    q3[f'raw_po_if_lost_{lab}'] = round(100 * st.mean(d['po'] for d in sub if d['won'] == 0))
# per-slot leverage
for name, team in (('DET', 'DET'), ('DAL', 'DAL')):
    q3[f'leverage_{name}_pts'] = round(100 * st.mean(d['lev'] for d in rows3 if d['tg'] and d['team'] == team), 1)
q3['leverage_tg_opponents_and_night_teams_pts'] = round(100 * st.mean(d['lev'] for d in rows3 if d['tg'] and d['team'] not in ('DET', 'DAL')), 1)
# most consequential TG games by leverage
byg = defaultdict(list)
for d in rows3:
    if d['tg']: byg[d['game_id']].append(d)
gl = sorted(byg.items(), key=lambda kv: -sum(x['lev'] for x in kv[1]))
q3['top_leverage_tg_games'] = [dict(game_id=k, leverage_pts=round(100 * sum(x['lev'] for x in v), 1)) for k, v in gl[:5]]
q3['bottom_leverage_tg_games'] = [dict(game_id=k, leverage_pts=round(100 * sum(x['lev'] for x in v), 1)) for k, v in gl[-5:]]
out['q3_stakes'] = q3

# ---------- Q4 2026 slate ----------
g26 = [r for r in games if r['season'] == '2026' and r['game_type'] == 'REG']
rec26 = defaultdict(lambda: [0, 0, 0])
for r in g26:
    if r['result'] == '': continue
    m = float(r['result'])
    for team, mm in ((r['home_team'], m), (r['away_team'], -m)):
        rec26[team][0 if mm > 0 else 1 if mm < 0 else 2] += 1
odds = json.load(open(f'{REPO}/data/nfl-odds.json'))
ot = {t['team']: t for t in odds['teams']}
slate = []
for r in g26:
    if r['gameday'] != '2026-11-26': continue
    hp, ps, src = home_p(r); row = dict(game=f"{r['away_team']} at {r['home_team']}", spread_line_home=float(r['spread_line']),
                                       home_moneyline=r['home_moneyline'], away_moneyline=r['away_moneyline'],
                                       home_win_chance_vigfree=round(hp, 2), teams={})
    lev = 0
    for team in (r['away_team'], r['home_team']):
        w, l, t = rec26[team]; gp = w + l + t
        d = dict(wpct=(w + .5 * t) / gp, gp=gp)
        lv = pr(d, 1) - pr(d, 0); lev += lv
        o = ot.get(team, {})
        row['teams'][team] = dict(record=f'{w}-{l}' + (f'-{t}' if t else ''), playoff_odds=o.get('po'), division_odds=o.get('dv'),
                                  model_leverage_pts=round(100 * lv, 1))
    row['game_leverage_pts_model'] = round(100 * lev, 1)
    slate.append(row)
out['q4_2026'] = dict(records_through=max(r['gameday'] for r in g26 if r['result'] != ''), odds_generated=odds['generated'],
                      note='records are before week 12 (Nov 22-23); leverage from the 1999-2025 model applied to current records, approximate',
                      games=slate, historical_tg_game_leverage_mean_pts=q3['tg_games']['game_leverage_mean_pts'],
                      historical_other_game_leverage_mean_pts=q3['other_games_same_week']['game_leverage_mean_pts'])
json.dump(out, open(f'{H}/results.json', 'w'), indent=1, default=str)
print(json.dumps({k: v for k, v in out.items()}, indent=1, default=str)[:12000])
