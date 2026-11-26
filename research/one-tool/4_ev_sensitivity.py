#!/usr/bin/env python3
"""Sensitivity: re-count with the editor's expected-value rule (the analyst may forecast with a
group mean). Agreement between the two EV coders; strict vs generous vs conservative totals."""
import json, glob, math, collections
C = {}
for f in glob.glob('codes/coder[ABCD].jsonl'):
    for l in open(f): o = json.loads(l); C[str(o['issue'])] = o
E1 = {str(json.loads(l)['issue']): json.loads(l) for l in open('codes/ev_coder1.jsonl') if l.strip()}
E2 = {str(json.loads(l)['issue']): json.loads(l) for l in open('codes/ev_coder2.jsonl') if l.strip()}
ids = sorted(E1, key=int); assert set(ids) == set(E2)
lost = lambda v: v in ('CHANGED', 'CANNOT-ASK')
def kappa(pairs):
    N = len(pairs); cats = sorted({x for p in pairs for x in p}); po = sum(a == b for a, b in pairs) / N
    pe = sum((sum(a == c for a, _ in pairs) / N) * (sum(b == c for _, b in pairs) / N) for c in cats); return po, (po - pe) / (1 - pe)
po, k = kappa([(E1[i]['verdict'], E2[i]['verdict']) for i in ids]); po2, k2 = kappa([(lost(E1[i]['verdict']), lost(E2[i]['verdict'])) for i in ids])
print(f'EV coders on {len(ids)} issues: 4-way agreement {po:.0%} (kappa {k:.2f}); lost-or-not {po2:.0%} (kappa {k2:.2f})')
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h)), round(100 * (c + h))
n = len(C); base_lost = sum(lost(o['verdict']) for o in C.values())
# under the EV rule, each originally CANNOT-ASK issue takes its EV verdict
for label, rule in [('EV, both coders say lost (conservative)', lambda i: lost(E1[i]['verdict']) and lost(E2[i]['verdict'])),
                    ('EV, either coder says lost', lambda i: lost(E1[i]['verdict']) or lost(E2[i]['verdict']))]:
    tot = sum(lost(o['verdict']) for i, o in C.items() if i not in E1) + sum(rule(i) for i in ids)
    lo, hi = wilson(tot, n); print(f'{label}: {tot} of {n} = {100 * tot / n:.0f}% [{lo}, {hi}]')
lo, hi = wilson(base_lost, n); print(f'strict (no forecasting): {base_lost} of {n} = {100 * base_lost / n:.0f}% [{lo}, {hi}]')
# right for the right reason under EV (conservative: SAME only if both coders say SAME)
rr = sum(o['verdict'] == 'SAME' for i, o in C.items() if i not in E1) + sum(E1[i]['verdict'] == 'SAME' and E2[i]['verdict'] == 'SAME' for i in ids)
rr_any = sum(o['verdict'] == 'SAME' for i, o in C.items() if i not in E1) + sum(E1[i]['verdict'] == 'SAME' or E2[i]['verdict'] == 'SAME' for i in ids)
print(f'right for the right reason under EV: {rr} (both coders) to {rr_any} (either) of {n}')
# consensus verdicts for the 63 (where they agree), and the false-certainty count
agree = [i for i in ids if E1[i]['verdict'] == E2[i]['verdict']]
print('EV consensus where coders agree (n=%d):' % len(agree), collections.Counter(E1[i]['verdict'] for i in agree))
print('disagreements:', [(i, E1[i]['verdict'][:8], E2[i]['verdict'][:8]) for i in ids if E1[i]['verdict'] != E2[i]['verdict']])
for i in ('19', '126', '220'):
    print(i, 'EV:', E1[i]['verdict'], '/', E2[i]['verdict'], '|', E1[i]['ev_analysis'][:110])
