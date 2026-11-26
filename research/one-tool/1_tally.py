#!/usr/bin/env python3
"""Tally the one-tool coding: verdict counts with 95% Wilson intervals, failure modes, and
agreement between the primary coder and the independent reliability coder (Cohen's kappa,
on the 4-way verdict and on the 2-way 'did the decision survive?')."""
import json, glob, math, os, collections
H = os.path.dirname(os.path.abspath(__file__))
prim = {}
for f in sorted(glob.glob(os.path.join(H, 'codes', 'coder[ABCD].jsonl'))):
    for l in open(f):
        if l.strip(): o = json.loads(l); prim[str(o['issue'])] = o
rel = {}
for l in open(os.path.join(H, 'codes', 'coderE.jsonl')) if os.path.exists(os.path.join(H, 'codes', 'coderE.jsonl')) else []:
    if l.strip(): o = json.loads(l); rel[str(o['issue'])] = o
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(100 * (c - h)), round(100 * (c + h))
n = len(prim); V = collections.Counter(o['verdict'] for o in prim.values())
print(f'issues coded: {n}')
for v in ('SAME', 'SAME-WRONG-REASON', 'CHANGED', 'CANNOT-ASK'):
    lo, hi = wilson(V[v], n); print(f'  {v:<18}{V[v]:>4}  {100 * V[v] / n:>3.0f}%  [{lo}, {hi}]')
lost = V['CHANGED'] + V['CANNOT-ASK']; lo, hi = wilson(lost, n)
print(f'  decision changed or lost: {lost} of {n} = {100 * lost / n:.0f}% [{lo}, {hi}]')
wrong = lost + V['SAME-WRONG-REASON']; lo, hi = wilson(wrong, n)
print(f'  not right for the right reason: {wrong} of {n} = {100 * wrong / n:.0f}% [{lo}, {hi}]')
print('failure modes:', collections.Counter(o['failure_mode'] for o in prim.values() if o['verdict'] != 'SAME').most_common())
print('by question type (changed or lost / n):')
T = collections.defaultdict(lambda: [0, 0])
for o in prim.values(): T[o['question_type']][1] += 1; T[o['question_type']][0] += o['verdict'] in ('CHANGED', 'CANNOT-ASK')
for k, (a, b) in sorted(T.items(), key=lambda x: -x[1][1]): print(f'  {k:<20}{a:>3}/{b:<3}')
def kappa(pairs):
    cats = sorted({x for p in pairs for x in p}); N = len(pairs)
    po = sum(a == b for a, b in pairs) / N
    pe = sum((sum(a == c for a, _ in pairs) / N) * (sum(b == c for _, b in pairs) / N) for c in cats)
    return po, (po - pe) / (1 - pe) if pe < 1 else 1.0
both = [i for i in rel if i in prim]
if both:
    po, k = kappa([(prim[i]['verdict'], rel[i]['verdict']) for i in both])
    surv = lambda v: v in ('SAME', 'SAME-WRONG-REASON')
    po2, k2 = kappa([(surv(prim[i]['verdict']), surv(rel[i]['verdict'])) for i in both])
    print(f'\nreliability, {len(both)} issues coded twice: 4-way agreement {po:.0%} (kappa {k:.2f}); survived-or-not agreement {po2:.0%} (kappa {k2:.2f})')
    for i in both:
        if prim[i]['verdict'] != rel[i]['verdict']: print(f'  #{i}: {prim[i]["verdict"]} vs {rel[i]["verdict"]}')
