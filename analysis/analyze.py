#!/usr/bin/env python3
"""Analyze 100 issues of China's Double Color Ball (SSQ) lottery."""
import re
import json
from collections import Counter, defaultdict
from itertools import combinations

html = open('/workspace/analysis/raw.html').read()
html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
rows = re.findall(r'<tr[^>]*class="t_tr1"[^>]*>(.*?)</tr>', html, re.DOTALL)

draws = []  # list of dict {issue, reds(sorted list of 6 ints), blue(int), date}
for r in rows:
    tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
    tds = [re.sub(r'<.*?>', '', x).replace('&nbsp;', '').strip() for x in tds]
    issue = None
    nums = []
    date = ''
    for x in tds:
        if re.fullmatch(r'\d{5}', x) and issue is None:
            issue = x
        elif re.fullmatch(r'\d{1,2}', x) and 1 <= int(x) <= 33 and len(nums) < 7:
            nums.append(int(x))
        elif re.fullmatch(r'\d{4}-\d{2}-\d{2}', x):
            date = x
    if issue and len(nums) >= 7:
        reds = sorted(nums[:6])
        blue = nums[6]
        draws.append({'issue': issue, 'reds': reds, 'blue': blue, 'date': date})

draws.sort(key=lambda d: d['issue'])
print(f'Total draws parsed: {len(draws)}')
print(f'Range: {draws[0]["issue"]} ({draws[0]["date"]}) -> {draws[-1]["issue"]} ({draws[-1]["date"]})')

with open('/workspace/analysis/draws.json', 'w') as f:
    json.dump(draws, f, ensure_ascii=False, indent=1)

# ---------- 1. Frequency analysis ----------
red_freq = Counter()
blue_freq = Counter()
for d in draws:
    for r in d['reds']:
        red_freq[r] += 1
    blue_freq[d['blue']] += 1

print('\n=== 1. Number frequency (Reds 1-33) ===')
items = [(n, red_freq.get(n, 0)) for n in range(1, 34)]
for i in range(0, 33, 3):
    chunk = items[i:i+3]
    print('  | '.join(f'{n:02d}: {c:2d}' for n, c in chunk))

print('\nTop10 Hot reds  :', sorted(red_freq.items(), key=lambda x:(-x[1], x[0]))[:10])
print('Bottom10 Cold reds:', sorted(red_freq.items(), key=lambda x:(x[1], x[0]))[:10])

print('\n=== Blue 1-16 freq ===')
items = [(n, blue_freq.get(n, 0)) for n in range(1, 17)]
for i in range(0, 16, 4):
    chunk = items[i:i+4]
    print('  | '.join(f'{n:02d}: {c:2d}' for n, c in chunk))
print('Top5 Hot blues:', sorted(blue_freq.items(), key=lambda x:(-x[1], x[0]))[:5])
print('Bottom5 Cold blues:', sorted(blue_freq.items(), key=lambda x:(x[1], x[0]))[:5])

# ---------- 2. Repeats between consecutive draws ----------
print('\n=== 2. Repeated red numbers between consecutive issues ===')
repeat_counts = Counter()
repeat_pairs = []
for i in range(1, len(draws)):
    prev = set(draws[i-1]['reds'])
    cur = set(draws[i]['reds'])
    common = sorted(prev & cur)
    repeat_counts[len(common)] += 1
    repeat_pairs.append((draws[i-1]['issue'], draws[i]['issue'], common))

print('Distribution of #repeated-reds between issue N-1 and N (99 pairs total):')
total = sum(repeat_counts.values())
exp = {0: 0.4060, 1: 0.4422, 2: 0.1383, 3: 0.0131, 4: 0.000401, 5: 3.5e-6, 6: 7e-9}
for k in sorted(repeat_counts):
    print(f'  {k} repeated red(s): {repeat_counts[k]:2d} times '
          f' ({repeat_counts[k]/total*100:5.1f}%) '
          f' theoretical: {exp[k]*100:5.1f}%')

at_least_one = sum(c for k, c in repeat_counts.items() if k >= 1)
print(f'  => At least 1 red repeated: {at_least_one}/99 = {at_least_one/99*100:.1f}%  (theory ~59.4%)')

blue_repeat = sum(1 for i in range(1, len(draws)) if draws[i-1]['blue'] == draws[i]['blue'])
print(f'\nBlue ball repeated in consecutive issues: {blue_repeat}/99 = {blue_repeat/99*100:.1f}%  (theory 1/16=6.25%)')

# Show longest streaks of "having at least one repeat"
streak = max_streak = 0
for n_rep in (len(set(draws[i-1]['reds']) & set(draws[i]['reds'])) for i in range(1, len(draws))):
    if n_rep >= 1:
        streak += 1
        max_streak = max(max_streak, streak)
    else:
        streak = 0
print(f'Longest streak of consecutive pairs each sharing >=1 red: {max_streak}')

# ---------- 3. Repeats within window N ----------
print('\n=== 3. Reds also appearing in previous N issues ===')
for N in [2, 3, 5, 10]:
    counts = []
    for i in range(N, len(draws)):
        prev = set()
        for j in range(i-N, i):
            prev |= set(draws[j]['reds'])
        cur = set(draws[i]['reds'])
        counts.append(len(cur & prev))
    avg = sum(counts) / len(counts)
    none_share = sum(1 for c in counts if c == 0)
    print(f'  Window N={N}: avg reds also in prior {N} issues = {avg:.2f}/6   '
          f' (#draws sharing NONE: {none_share}/{len(counts)})')

# ---------- 4. Sum / Odd-Even / Big-Small ----------
print('\n=== 4. Reds sum / odd-even / big-small ===')
sums = [sum(d['reds']) for d in draws]
print(f'  Reds sum  -> min {min(sums)}, max {max(sums)}, avg {sum(sums)/len(sums):.1f}, median {sorted(sums)[50]}')
sum_buckets = Counter()
for s in sums:
    sum_buckets[(s//20)*20] += 1
for k in sorted(sum_buckets):
    bar = "#" * sum_buckets[k]
    print(f'    {k:3d}-{k+19:3d}: {bar} ({sum_buckets[k]})')

odd_dist = Counter()
big_dist = Counter()
for d in draws:
    odd = sum(1 for r in d['reds'] if r % 2 == 1)
    big = sum(1 for r in d['reds'] if r >= 17)
    odd_dist[odd] += 1
    big_dist[big] += 1
print('  Odd-count distribution (odd reds in 6):', dict(sorted(odd_dist.items())))
print('  Big-count distribution (>=17 in 6)   :', dict(sorted(big_dist.items())))

print('\n  Three-zone distribution (1-11 / 12-22 / 23-33) top 10 patterns:')
zone_dist = Counter()
for d in draws:
    z = (sum(1 for r in d['reds'] if r <= 11),
         sum(1 for r in d['reds'] if 12 <= r <= 22),
         sum(1 for r in d['reds'] if r >= 23))
    zone_dist[z] += 1
for z, c in sorted(zone_dist.items(), key=lambda x: -x[1])[:10]:
    print(f'    {z}: {c}')

# ---------- 5. Span ----------
spans = [max(d['reds']) - min(d['reds']) for d in draws]
print(f'\n=== 5. Span ===\n  Span (max-min) -> min {min(spans)}, max {max(spans)}, avg {sum(spans)/len(spans):.1f}')

# ---------- 6. Consecutive within a draw ----------
print('\n=== 6. Consecutive pairs within a single draw ===')
cons_count_dist = Counter()
for d in draws:
    r = d['reds']
    cnt = sum(1 for a, b in zip(r, r[1:]) if b - a == 1)
    cons_count_dist[cnt] += 1
print('  #consecutive-pairs per draw:', dict(sorted(cons_count_dist.items())))
has_cons = sum(c for k, c in cons_count_dist.items() if k >= 1)
print(f'  => at least one consecutive pair: {has_cons}/100 = {has_cons}%  (theory ~59%)')

# ---------- 7. Omission ----------
print('\n=== 7. Current "missing streak" per red number (newest issue is the right side) ===')
last_seen = {}
for i, d in enumerate(draws):
    for r in d['reds']:
        last_seen[r] = i
N = len(draws)
omissions = []
for n in range(1, 34):
    if n in last_seen:
        omissions.append((n, N - 1 - last_seen[n]))
    else:
        omissions.append((n, N))
omissions.sort(key=lambda x: -x[1])
print('  10 reds with the longest current absence:')
for n, gap in omissions[:10]:
    print(f'    {n:02d}: not seen for {gap} issues')
print('  10 reds with shortest absence (recently appeared):')
for n, gap in sorted(omissions, key=lambda x: x[1])[:10]:
    print(f'    {n:02d}: not seen for {gap} issues')

# ---------- 8. Last 10 draws ----------
print('\n=== 8. Last 10 draws (oldest -> newest) ===')
for d in draws[-10:]:
    reds = ' '.join(f'{r:02d}' for r in d['reds'])
    print(f"  {d['issue']} {d['date']}  Red: {reds}  Blue: {d['blue']:02d}")
