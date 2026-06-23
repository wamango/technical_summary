#!/usr/bin/env python3
"""
Generate 5 SSQ tickets biased toward COLD numbers (low frequency in last 100 issues).

Strategy:
  - Compute red/blue frequency over last 100 issues.
  - Cold red pool = bottom-16 reds (those with frequency <= median).
  - Cold blue pool = bottom-8 blues.
  - Each ticket: 4-5 reds from cold pool, 1-2 from any 1-33, blue from cold pool.
  - All 5 tickets are distinct.
"""
import json
import secrets
from collections import Counter

draws = json.load(open('/workspace/analysis/draws.json'))
red_freq = Counter()
blue_freq = Counter()
for d in draws:
    for r in d['reds']: red_freq[r] += 1
    blue_freq[d['blue']] += 1

red_sorted = sorted(range(1, 34), key=lambda n: (red_freq.get(n, 0), n))
blue_sorted = sorted(range(1, 17), key=lambda n: (blue_freq.get(n, 0), n))

cold_red_pool = red_sorted[:16]   # bottom 16 reds
cold_blue_pool = blue_sorted[:8]  # bottom 8 blues

print('最近 100 期统计——冷号池：')
print(f'  冷红球(16) : {sorted(cold_red_pool)}')
print(f'    频次     : {[(n, red_freq[n]) for n in sorted(cold_red_pool, key=lambda x:(red_freq[x], x))]}')
print(f'  冷蓝球(8)  : {sorted(cold_blue_pool)}')
print(f'    频次     : {[(n, blue_freq[n]) for n in sorted(cold_blue_pool, key=lambda x:(blue_freq[x], x))]}')

def rand_choice(seq):
    return seq[secrets.randbelow(len(seq))]

def pick_ticket():
    reds = set()
    # k reds from cold pool, k in {4, 5}
    k_cold = 4 + secrets.randbelow(2)
    pool = list(cold_red_pool)
    while len([r for r in reds if r in cold_red_pool]) < k_cold:
        n = pool.pop(secrets.randbelow(len(pool)))
        reds.add(n)
    # remaining: from full 1-33 (still likely a cold-ish since pool is random)
    full = [n for n in range(1, 34) if n not in reds]
    while len(reds) < 6:
        n = full.pop(secrets.randbelow(len(full)))
        reds.add(n)
    blue = rand_choice(cold_blue_pool)
    return tuple(sorted(reds)), blue

tickets = set()
while len(tickets) < 5:
    tickets.add(pick_ticket())

print('\n生成 5 注冷门组合（红球 4~5 个来自冷红池，蓝球来自冷蓝池）：\n')
print(f'{"注号":<5}{"红球":<28}{"蓝球":<5}{"冷红命中":<10}{"和值"}')
print('-' * 60)
for i, (reds, blue) in enumerate(sorted(tickets), 1):
    red_s = ' '.join(f'{r:02d}' for r in reds)
    in_cold = len(set(reds) & set(cold_red_pool))
    print(f' {i}   {red_s}    {blue:02d}    {in_cold}/6       {sum(reds)}')
