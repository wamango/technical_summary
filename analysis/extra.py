#!/usr/bin/env python3
"""Extra pattern checks for SSQ."""
import json
from collections import Counter
from itertools import combinations

draws = json.load(open('/workspace/analysis/draws.json'))
N = len(draws)

# Most common red-pairs that appear together in a draw
pair_count = Counter()
for d in draws:
    for a, b in combinations(d['reds'], 2):
        pair_count[(a, b)] += 1
print('Top 15 red pairs co-appearing in a single draw:')
for p, c in pair_count.most_common(15):
    print(f'  {p}: {c}')

# Most common red triples
triple_count = Counter()
for d in draws:
    for t in combinations(d['reds'], 3):
        triple_count[t] += 1
print('\nTop 10 red triples co-appearing:')
for t, c in triple_count.most_common(10):
    print(f'  {t}: {c}')

# How often does the same red appear N consecutive draws in a row
# For each red, find its longest run of consecutive draws containing it
print('\nLongest run of consecutive draws containing each red:')
runs = []
for n in range(1, 34):
    longest = cur = 0
    for d in draws:
        if n in d['reds']:
            cur += 1; longest = max(longest, cur)
        else:
            cur = 0
    runs.append((n, longest))
for n, lg in sorted(runs, key=lambda x: -x[1])[:10]:
    print(f'  {n:02d}: {lg}')

# Last-N-issues breakdown: same red repeating in N+1 (consecutive)
# vs randomly drawn pair: prob shared red >=1 = 1 - C(27,6)/C(33,6) ~ 0.5938
import math
def C(n,k): return math.comb(n,k)
p0 = C(27,6)/C(33,6)
print(f'\nTheoretical prob of 0 shared reds between two indep draws: {p0:.4f}')
p1 = 6*C(27,5)/C(33,6)
p2 = C(6,2)*C(27,4)/C(33,6)
p3 = C(6,3)*C(27,3)/C(33,6)
print(f'  P(=1) {p1:.4f}, P(=2) {p2:.4f}, P(=3) {p3:.4f}')

# For each draw, how many of its reds equal a recent hot red (top 10 freq)?
hot10 = [13,2,3,24,9,30,1,25,22,10]
hot_in_draw = []
for d in draws:
    hot_in_draw.append(len(set(d['reds']) & set(hot10)))
print(f'\nReds drawn from top-10 hot set (per draw): avg = {sum(hot_in_draw)/N:.2f}')
print(f'  distribution: {dict(sorted(Counter(hot_in_draw).items()))}')

# Repeats with offset 1, 2, 3
print('\nAvg reds shared between draws at offset k:')
for k in range(1, 8):
    cnts = []
    for i in range(k, N):
        cnts.append(len(set(draws[i-k]['reds']) & set(draws[i]['reds'])))
    print(f'  offset {k}: avg {sum(cnts)/len(cnts):.2f}  '
          f' (theoretical for independent draws: {1.0909:.2f})')

# Lookback: out of the last 10 draws, fraction of reds also in the previous draw
print('\nRecent 10 draws: how many reds appeared in the immediate previous draw?')
for i in range(N-10, N):
    common = sorted(set(draws[i-1]['reds']) & set(draws[i]['reds']))
    print(f"  {draws[i]['issue']} reds={draws[i]['reds']}  shared with prev: {common}  ({len(common)})")
