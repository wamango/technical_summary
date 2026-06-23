#!/usr/bin/env python3
"""
Generate 5 SSQ tickets biased to the last 8 issues.

Constraints per ticket:
  - At least 1 red is shared with the most recent issue (26059)
  - At least 1 red is shared with the 2nd most recent issue (26058)
  - At least 4 of 6 reds come from the union of the last 8 issues
  - Blue ball is picked from the blue balls of the last 8 issues
  - All 5 tickets are distinct
"""
import json
import secrets

draws = json.load(open('/workspace/analysis/draws.json'))
last8 = draws[-8:]

print('参考最近 8 期：')
for d in last8:
    reds = ' '.join(f'{r:02d}' for r in d['reds'])
    print(f"  {d['issue']} {d['date']}  Red: {reds}  Blue: {d['blue']:02d}")

latest = set(last8[-1]['reds'])
second = set(last8[-2]['reds'])
last8_reds = sorted({r for d in last8 for r in d['reds']})
last8_blues = sorted({d['blue'] for d in last8})

print(f"\n最近 8 期已出红号池({len(last8_reds)}个): {last8_reds}")
print(f"最近 8 期已出蓝号池({len(last8_blues)}个): {last8_blues}")
print(f"最新一期(26059)红球: {sorted(latest)}")
print(f"次新一期(26058)红球: {sorted(second)}")

def rand_choice(seq):
    return seq[secrets.randbelow(len(seq))]

def sample_no_replace(pool, k):
    pool = list(pool)
    out = []
    while len(out) < k and pool:
        x = pool.pop(secrets.randbelow(len(pool)))
        out.append(x)
    return out

def pick_ticket():
    reds = set()
    # 1 red from issue 26059 (most recent)
    reds.add(rand_choice(list(latest)))
    # 1 red from issue 26058 (avoid dup with one already picked)
    candidates = list(second - reds)
    reds.add(rand_choice(candidates))
    # 2 more reds from the union of last 8 issues (not yet picked)
    pool = [r for r in last8_reds if r not in reds]
    reds.update(sample_no_replace(pool, 2))
    # 2 more reds: 50/50 either from last-8 pool or from "any 1-33" to add freshness
    while len(reds) < 6:
        if secrets.randbelow(2) == 0:
            pool = [r for r in last8_reds if r not in reds]
        else:
            pool = [r for r in range(1, 34) if r not in reds]
        reds.add(rand_choice(pool))
    blue = rand_choice(last8_blues)
    return tuple(sorted(reds)), blue

tickets = set()
while len(tickets) < 5:
    tickets.add(pick_ticket())

print('\n生成 5 注（每注至少与最近 1 期和次新 1 期各有 1 个红球相同）：\n')
print(f'{"注号":<5}{"红球":<28}{"蓝球":<5}{"与26059相同":<14}{"与26058相同"}')
print('-' * 75)
for i, (reds, blue) in enumerate(sorted(tickets), 1):
    red_s = ' '.join(f'{r:02d}' for r in reds)
    s_latest = sorted(set(reds) & latest)
    s_second = sorted(set(reds) & second)
    print(f' {i}   {red_s}    {blue:02d}    '
          f'{str(s_latest):<14}{s_second}')
