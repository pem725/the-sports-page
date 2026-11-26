#!/usr/bin/env python3
"""Scorecard No. 3: grade the rivalry-weekend predictions frozen in commit 4cd49e7.

Tuesday night, after the CFP ranking:
    set -a; . ~/.config/secrets/tokens.env; set +a
    python3 weekly.py --refresh          # 2 CFBD calls: results + the new ranking
    python3 grade_rivalry.py             # writes grade-rivalry-2026.json, prints the summary

--fake plays the weekend out at random from our own odds (to test the code before the games).

Three grades:
  1. Win forecasts: expected upsets (sum of underdog chances) vs actual; Brier score vs a coin flip.
  2. Playoff calls: for every team with a stake, our chance of making the field GIVEN its actual
     result, against where the committee put it (top 12 as the proxy for "in": the bracket's
     conference-champion bids are not decided until Selection Day; stated in the piece).
  3. Bye calls: our chance of a top-4 seed given the result, against committee top 4.
"""
import json, gzip, os, sys, random
H = os.path.dirname(os.path.abspath(__file__)); Y = 2026
L = json.load(open(os.path.join(H, '..', 'rivalry', 'leverage.json')))
FAKE = '--fake' in sys.argv
results = {}
if FAKE:
    random.seed(7)
    for g in L['games']:
        s = {x['team']: x for x in g['sides']}
        results[(g['away'], g['home'])] = g['home'] if random.random() < s[g['home']]['p_win'] else g['away']
    new_rank = {}
    # fake committee: rank by our post-result playoff chance (only to exercise the code)
    post = []
    for g in L['games']:
        w = results[(g['away'], g['home'])]
        for x in g['sides']: post.append((x['if_win'] if x['team'] == w else x['if_lose'], x['team']))
    for i, (_, t) in enumerate(sorted(post, reverse=True)[:25]): new_rank[t] = i + 1
else:
    G = json.load(gzip.open(os.path.join(H, 'raw', f'games-{Y}.json.gz'), 'rt'))
    byteams = {(g['awayTeam'], g['homeTeam']): g for g in G}
    for g in L['games']:
        x = byteams.get((g['away'], g['home']))
        if x and x.get('completed') and x['homePoints'] is not None:
            results[(g['away'], g['home'])] = g['home'] if x['homePoints'] > x['awayPoints'] else g['away']
    wk = sorted(f for f in os.listdir(H) if f.startswith('weekly-') and f.endswith('.json'))[-1]
    W = json.load(open(os.path.join(H, wk)))
    # weekly-<date>.json is written the day after a ranking; the predictions were run the day after
    # the Nov 24 ranking, so only a weekly file dated AFTER that run carries a new ranking.
    if W['date'] <= L['run']:
        sys.exit(f'newest weekly file is {wk}: the new ranking is not in yet. Run weekly.py --refresh after it is released.')
    new_rank = {r['team']: r['cfp'] for r in W['rows'] if r['cfp']}
# 1. win forecasts
played = [g for g in L['games'] if (g['away'], g['home']) in results]
exp_up = act_up = brier = 0.0
for g in played:
    s = {x['team']: x for x in g['sides']}; w = results[(g['away'], g['home'])]
    fav = max(s, key=lambda t: s[t]['p_win']); dog = [t for t in s if t != fav][0]
    exp_up += s[dog]['p_win']; act_up += (w == dog)
    brier += (s[g['home']]['p_win'] - (w == g['home'])) ** 2
n = len(played)
# 2-3. playoff and bye calls for teams with a stake (any chance of the field before the games)
calls = []
for g in played:
    w = results[(g['away'], g['home'])]
    for x in g['sides']:
        if x['in'] < .02: continue
        won = x['team'] == w
        p_in = x['if_win'] if won else x['if_lose']; p_bye = x['bye_if_win'] if won else x['bye_if_lose']
        r = new_rank.get(x['team'])
        calls.append(dict(team=x['team'], won=won, before_in=round(x['in'], 3), after_in=round(p_in, 3),
            before_bye=round(x['bye'], 3), after_bye=round(p_bye, 3), cfp=r,
            in_agree=(p_in >= .5) == (r is not None and r <= 12), bye_agree=(p_bye >= .5) == (r is not None and r <= 4)))
calls.sort(key=lambda c: -c['after_in'])
out = dict(fake=FAKE, games=n, expected_upsets=round(exp_up, 1), upsets=int(act_up), brier=round(brier / n, 3) if n else None,
           coin_brier=.25, calls=calls, in_agree=sum(c['in_agree'] for c in calls), bye_agree=sum(c['bye_agree'] for c in calls))
json.dump(out, open(os.path.join(H, 'grade-rivalry-2026' + ('-FAKE' if FAKE else '') + '.json'), 'w'), indent=1)
print(f"{'FAKE RUN -- ' if FAKE else ''}{n} games graded. Upsets: expected {out['expected_upsets']}, happened {out['upsets']}. "
      f"Brier {out['brier']} (coin flip .25).")
print(f"Playoff calls agreeing with the committee's top 12: {out['in_agree']} of {len(calls)}; bye calls vs top 4: {out['bye_agree']} of {len(calls)}")
print(f"{'team':<16}{'won':<5}{'in before':>10}{'in after':>9}{'bye after':>10}{'CFP':>5}  agree")
for c in calls[:20]:
    print(f"{c['team']:<16}{'W' if c['won'] else 'L':<5}{c['before_in']:>10.2f}{c['after_in']:>9.2f}{c['after_bye']:>10.2f}{str(c['cfp'] or '-'):>5}  {'yes' if c['in_agree'] else 'NO'}")
