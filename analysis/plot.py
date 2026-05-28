#!/usr/bin/env python3
"""Generate frequency/repeat-pattern charts for SSQ analysis."""
import json
import math
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

draws = json.load(open('/workspace/analysis/draws.json'))

red_freq = Counter()
blue_freq = Counter()
for d in draws:
    for r in d['reds']: red_freq[r] += 1
    blue_freq[d['blue']] += 1

fig, axes = plt.subplots(2, 2, figsize=(14, 9))

ax = axes[0, 0]
xs = list(range(1, 34))
ys = [red_freq.get(n, 0) for n in xs]
avg = sum(ys) / 33
bars = ax.bar(xs, ys, color='#d62728')
for i, v in enumerate(ys):
    if v >= max(ys) - 2:
        bars[i].set_color('#8B0000')
ax.axhline(avg, color='gray', linestyle='--', label=f'avg={avg:.1f}')
ax.set_title('Red ball frequency (last 100 issues)')
ax.set_xlabel('Red number'); ax.set_ylabel('count')
ax.set_xticks(xs); ax.set_xticklabels([f'{n}' for n in xs], fontsize=7)
ax.legend()

ax = axes[0, 1]
xs = list(range(1, 17))
ys = [blue_freq.get(n, 0) for n in xs]
avg = sum(ys) / 16
ax.bar(xs, ys, color='#1f77b4')
ax.axhline(avg, color='gray', linestyle='--', label=f'avg={avg:.1f}')
ax.set_title('Blue ball frequency (last 100 issues)')
ax.set_xlabel('Blue number'); ax.set_ylabel('count')
ax.set_xticks(xs); ax.legend()

ax = axes[1, 0]
rep_counts = Counter()
for i in range(1, len(draws)):
    rep_counts[len(set(draws[i-1]['reds']) & set(draws[i]['reds']))] += 1
def C(n,k): return math.comb(n,k)
total33 = C(33, 6)
theo = {k: C(6, k)*C(27, 6-k)/total33 * 99 for k in range(7)}
ks = sorted(set(list(rep_counts) + list(range(5))))
actual = [rep_counts.get(k, 0) for k in ks]
expected = [theo[k] for k in ks]
w = 0.4
ax.bar([k - w/2 for k in ks], actual, w, label='actual', color='#d62728')
ax.bar([k + w/2 for k in ks], expected, w, label='theoretical', color='#777777')
ax.set_title('# reds shared with previous draw (99 pairs)')
ax.set_xlabel('# of shared reds'); ax.set_ylabel('pair count')
ax.legend()
for k, a, e in zip(ks, actual, expected):
    ax.text(k - w/2, a + 0.5, f'{a}', ha='center', fontsize=8)
    ax.text(k + w/2, e + 0.5, f'{e:.1f}', ha='center', fontsize=8)

ax = axes[1, 1]
last_seen = {n: -1 for n in range(1, 34)}
for i, d in enumerate(draws):
    for r in d['reds']:
        last_seen[r] = i
N = len(draws)
xs = list(range(1, 34))
ys = [N - 1 - last_seen[n] if last_seen[n] >= 0 else N for n in xs]
ax.bar(xs, ys, color='#2ca02c')
ax.set_title('Current missing streak per red (# of issues since last seen)')
ax.set_xlabel('Red number'); ax.set_ylabel('issues missing')
ax.set_xticks(xs); ax.set_xticklabels([f'{n}' for n in xs], fontsize=7)
for i, v in enumerate(ys):
    if v >= 10:
        ax.text(xs[i], v + 0.5, str(v), ha='center', fontsize=8)

plt.tight_layout()
out = '/workspace/analysis/ssq_overview.png'
plt.savefig(out, dpi=120, bbox_inches='tight')
print('saved', out)
