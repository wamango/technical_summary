#!/usr/bin/env python3
"""Randomly generate 5 SSQ tickets (6 reds from 1-33, 1 blue from 1-16)."""
import secrets

def pick():
    reds = []
    pool = list(range(1, 34))
    while len(reds) < 6:
        n = pool[secrets.randbelow(len(pool))]
        pool.remove(n)
        reds.append(n)
    reds.sort()
    blue = 1 + secrets.randbelow(16)
    return reds, blue

print('随机生成 5 注双色球（红球 6/33，蓝球 1/16，使用密码学安全随机源）：\n')
print(f'{"注号":<6}{"红球":<28}{"蓝球":<6}')
print('-' * 42)
for i in range(1, 6):
    reds, blue = pick()
    red_s = ' '.join(f'{r:02d}' for r in reds)
    print(f' {i}    {red_s}    {blue:02d}')
