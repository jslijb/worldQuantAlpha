# -*- coding: utf-8 -*-
"""acct_probe2.py —— 确认 dateCreated 时区格式 + 数值区间过滤，为自动分片做准备
输出 _autologs/_acct_probe2.txt
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
        L.append('%-54s -> HTTP %s  %s' % (tag, r.status_code, r.text[:110].replace('\n', ' ')))
        return None
    j = r.json()
    L.append('%-54s -> count=%s' % (tag, j.get('count')))
    return j.get('count')

L.append('== dateCreated 带时区格式 ==')
for d in ('2026-09-01T00:00:00-04:00', '2026-08-01T00:00:00-04:00', '2026-07-01T00:00:00-04:00',
          '2026-06-01T00:00:00-04:00', '2026-05-01T00:00:00-04:00', '2026-04-01T00:00:00-04:00',
          '2026-03-01T00:00:00-05:00', '2026-01-01T00:00:00-05:00', '2025-09-01T00:00:00-04:00'):
    q('>= %s' % d, 'limit=1&dateCreated%3E%3D' + d)
for d in ('2026-10-01T00:00:00-04:00', '2026-09-01T00:00:00-04:00', '2026-08-01T00:00:00-04:00',
          '2026-07-01T00:00:00-04:00', '2026-06-01T00:00:00-04:00'):
    q('<  %s' % d, 'limit=1&dateCreated%3C' + d)

L.append('')
L.append('== 月区间切片大小（UNSUBMITTED）==')
MON = [('2026-09-01T00:00:00-04:00', '2026-10-01T00:00:00-04:00'),
       ('2026-08-01T00:00:00-04:00', '2026-09-01T00:00:00-04:00'),
       ('2026-07-01T00:00:00-04:00', '2026-08-01T00:00:00-04:00'),
       ('2026-06-01T00:00:00-04:00', '2026-07-01T00:00:00-04:00'),
       ('2026-05-01T00:00:00-04:00', '2026-06-01T00:00:00-04:00'),
       ('2026-04-01T00:00:00-04:00', '2026-05-01T00:00:00-04:00'),
       ('2026-03-01T00:00:00-05:00', '2026-04-01T00:00:00-04:00'),
       ('2026-02-01T00:00:00-05:00', '2026-03-01T00:00:00-05:00'),
       ('2026-01-01T00:00:00-05:00', '2026-02-01T00:00:00-05:00'),
       ('2025-12-01T00:00:00-05:00', '2026-01-01T00:00:00-05:00'),
       ('2025-11-01T00:00:00-04:00', '2025-12-01T00:00:00-05:00'),
       ('2025-10-01T00:00:00-04:00', '2025-11-01T00:00:00-04:00'),
       ('2025-09-01T00:00:00-04:00', '2025-10-01T00:00:00-04:00')]
tot = 0
for a, b in MON:
    c = q('%s ~ %s' % (a[:10], b[:10]),
          'limit=1&status=UNSUBMITTED&dateCreated%3E%3D' + a + '&dateCreated%3C' + b)
    if c:
        tot += c
L.append('  月区间合计 %d' % tot)

L.append('')
L.append('== 数值区间过滤 ==')
q('is.sharpe>=2 & is.fitness>=1.8', 'limit=1&status=UNSUBMITTED&is.sharpe%3E%3D2&is.fitness%3E%3D1.8')
q('is.sharpe>=2.5', 'limit=1&status=UNSUBMITTED&is.sharpe%3E%3D2.5')
q('is.sharpe>=3', 'limit=1&status=UNSUBMITTED&is.sharpe%3E%3D3')
q('is.sharpe<2', 'limit=1&status=UNSUBMITTED&is.sharpe%3C2')
q('is.turnover<=0.2', 'limit=1&status=UNSUBMITTED&is.turnover%3C%3D0.2')

io.open('_autologs/_acct_probe2.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
