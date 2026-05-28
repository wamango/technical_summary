#!/usr/bin/env python3
"""
"My recommended" 5 SSQ tickets, combining insights from all earlier analyses.

Per-ticket structure (6 reds + 1 blue):
  - 1~2 reds from the most recent issue (26059)        --> 承接近期
  - 1~2 hot reds (top-10 by 100-issue frequency)        --> 适度借势
  - 1~2 long-omission reds (missing >= 10 issues)       --> 押冷号回补
  - rest fill from the full 1-33 pool

Form filter (each accepted ticket must satisfy):
  - sum in [70, 130]
  - odd-count in [2, 4]
  - three-zone (1-11/12-22/23-33) split: every zone has 1..3 reds
  - span (max-min) >= 12
  - not identical to any draw in the last 100 issues
  - all 5 tickets distinct

Blue ball: chosen with weight = sqrt(frequency + 1) over 1..16 (slightly favors
recent activity but still spreads).
"""
import json
import math
import secrets
from collections import Counter

draws = json.load(open('/workspace/analysis/draws.json'))
red_freq = Counter()
blue_freq = Counter()
for d in draws:
    for r in d['reds']: red_freq[r] += 1
    blue_freq[d['blue']] += 1

N = len(draws)
latest = draws[-1]['reds']           # issue 26059
hot_reds = [n for n, _ in sorted(red_freq.items(), key=lambda x: (-x[1], x[0]))[:10]]

last_seen = {n: -1 for n in range(1, 34)}
for i, d in enumerate(draws):
    for r in d['reds']:
        last_seen[r] = i
omissions = {n: (N - 1 - last_seen[n] if last_seen[n] >= 0 else N) for n in range(1, 34)}
cold_omission_reds = [n for n in range(1, 34) if omissions[n] >= 10]

print('参考池：')
print(f'  最新一期(26059)红球 : {sorted(latest)}')
print(f'  100期热号 top10     : {sorted(hot_reds)}')
print(f'  当前遗漏≥10期的红球: {sorted(cold_omission_reds)}  (含遗漏值)')
print('   ', [(n, omissions[n]) for n in sorted(cold_omission_reds, key=lambda x: -omissions[x])])

prev_combos = {tuple(d['reds']) for d in draws}

def rand_choice(seq):
    return seq[secrets.randbelow(len(seq))]

def weighted_blue():
    weights = [math.sqrt(blue_freq.get(b, 0) + 1) for b in range(1, 17)]
    total = sum(weights)
    r = secrets.randbelow(10**9) / 10**9 * total
    acc = 0
    for b, w in zip(range(1, 17), weights):
        acc += w
        if r <= acc:
            return b
    return 16

def valid(reds_tuple):
    reds = list(reds_tuple)
    s = sum(reds)
    if not (70 <= s <= 130): return False
    odd = sum(1 for r in reds if r % 2 == 1)
    if not (2 <= odd <= 4): return False
    z1 = sum(1 for r in reds if r <= 11)
    z2 = sum(1 for r in reds if 12 <= r <= 22)
    z3 = sum(1 for r in reds if r >= 23)
    if not (1 <= z1 <= 3 and 1 <= z2 <= 3 and 1 <= z3 <= 3): return False
    if max(reds) - min(reds) < 12: return False
    if reds_tuple in prev_combos: return False
    return True

def pick_one():
    while True:
        reds = set()
        # 1~2 from latest issue
        k1 = 1 + secrets.randbelow(2)
        cand = list(latest)
        for _ in range(k1):
            n = cand.pop(secrets.randbelow(len(cand)))
            reds.add(n)
        # 1~2 hot reds (not yet picked)
        k2 = 1 + secrets.randbelow(2)
        cand = [n for n in hot_reds if n not in reds]
        for _ in range(min(k2, len(cand))):
            n = cand.pop(secrets.randbelow(len(cand)))
            reds.add(n)
        # 1~2 long-omission cold reds
        k3 = 1 + secrets.randbelow(2)
        cand = [n for n in cold_omission_reds if n not in reds]
        for _ in range(min(k3, len(cand))):
            n = cand.pop(secrets.randbelow(len(cand)))
            reds.add(n)
        # fill remaining from full 1-33
        cand = [n for n in range(1, 34) if n not in reds]
        while len(reds) < 6:
            n = cand.pop(secrets.randbelow(len(cand)))
            reds.add(n)
        t = tuple(sorted(reds))
        if valid(t):
            return t, weighted_blue()

tickets = []
seen = set()
while len(tickets) < 5:
    t, b = pick_one()
    if t in seen: continue
    seen.add(t)
    tickets.append((t, b))

print('\n精选 5 注：\n')
hdr = f'{"#":<3}{"红球":<26}{"蓝":<4}{"和":<5}{"奇:偶":<8}{"3区(小:中:大)":<14}{"含最新":<8}{"含热":<6}{"含冷"}'
print(hdr)
print('-' * len(hdr) * 2)
for i, (reds, blue) in enumerate(tickets, 1):
    s = sum(reds)
    odd = sum(1 for r in reds if r % 2 == 1)
    z1 = sum(1 for r in reds if r <= 11)
    z2 = sum(1 for r in reds if 12 <= r <= 22)
    z3 = sum(1 for r in reds if r >= 23)
    incl_latest = sorted(set(reds) & set(latest))
    incl_hot = sorted(set(reds) & set(hot_reds))
    incl_cold = sorted(set(reds) & set(cold_omission_reds))
    red_s = ' '.join(f'{r:02d}' for r in reds)
    print(f' {i}  {red_s}    {blue:02d}  {s:<5}{odd}:{6-odd:<6}'
          f'({z1}:{z2}:{z3}){"":<8}{str(incl_latest):<8}{str(incl_hot):<6}{incl_cold}')
