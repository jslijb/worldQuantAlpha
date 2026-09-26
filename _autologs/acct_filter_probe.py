# -*- coding: utf-8 -*-
"""acct_filter_probe.py —— 找出可用的过滤器分片，绕开 offset<=1000 硬上限

平台报错原文：Cannot display more than the first 1,000 alphas. Apply filters to narrow results.
思路：用 dateCreated 区间 / settings.* / is.* 过滤，把 3545 条切成每片 <1000。
判据：看返回的 count 是否随过滤条件变化。
输出 _autologs/_acct_filter_probe.txt
"""
import os, io, json, requests

os.chdir('D:/Python/worldquant')
s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201

U = 'https://api.worldquantbrain.com/users/self/alphas'
L = []

def q(tag, qs):
    r = s.get(U + '?' + qs)
    if r.status_code != 200:
        L.append('%-52s -> HTTP %s  %s' % (tag, r.status_code, r.text[:120].replace('\n', ' ')))
        return
    j = r.json()
    L.append('%-52s -> count=%s results=%d' % (tag, j.get('count'), len(j.get('results') or [])))

L.append('== 基线 ==')
q('limit=1', 'limit=1')
q('limit=1&status=UNSUBMITTED', 'limit=1&status=UNSUBMITTED')

L.append('')
L.append('== dateCreated 区间（>= 用 %3E%3D，< 用 %3C）==')
for d in ('2026-09-01', '2026-08-01', '2026-07-01', '2026-06-01', '2026-01-01', '2025-06-01'):
    q('dateCreated>=%s' % d, 'limit=1&dateCreated%3E%3D' + d)
for d in ('2026-09-01', '2026-08-01', '2026-01-01'):
    q('dateCreated<%s' % d, 'limit=1&dateCreated%3C' + d)
q('dateCreated 8月区间', 'limit=1&dateCreated%3E%3D2026-08-01&dateCreated%3C2026-09-01')

L.append('')
L.append('== settings.* 过滤 ==')
q('settings.region=USA', 'limit=1&settings.region=USA')
q('settings.universe=TOP3000', 'limit=1&settings.universe=TOP3000')
q('settings.delay=1', 'limit=1&settings.delay=1')
q('settings.neutralization=SUBINDUSTRY', 'limit=1&settings.neutralization=SUBINDUSTRY')

L.append('')
L.append('== is 指标过滤 ==')
q('is.sharpe>=2', 'limit=1&is.sharpe%3E%3D2')
q('is.fitness>=2', 'limit=1&is.fitness%3E%3D2')

L.append('')
L.append('== 组合分片试算（目标每片<1000）==')
combos = [
    ('UNSUB + 2026-08', 'limit=1&status=UNSUBMITTED&dateCreated%3E%3D2026-08-01&dateCreated%3C2026-09-01'),
    ('UNSUB + 2026-09', 'limit=1&status=UNSUBMITTED&dateCreated%3E%3D2026-09-01'),
    ('UNSUB + region=USA', 'limit=1&status=UNSUBMITTED&settings.region=USA'),
    ('UNSUB + delay=1', 'limit=1&status=UNSUBMITTED&settings.delay=1'),
    ('UNSUB + delay=0', 'limit=1&status=UNSUBMITTED&settings.delay=0'),
]
for tag, qs in combos:
    q(tag, qs)

io.open('_autologs/_acct_filter_probe.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
