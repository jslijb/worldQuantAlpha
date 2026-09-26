# -*- coding: utf-8 -*-
"""acct_probe.py —— 探测 /users/self/alphas 的分页上限，找出拉到全量（3534 条）的方式

背景：官方 UI 的 Unsubmitted 计数是 3534，而此前脚本在 offset>=1100 就 400 退出，
被误读成"账号可视窗只有 1100 条"。本脚本逐项探测参数组合与 count 字段。
输出 _autologs/_acct_probe.txt
"""
import os, io, json, requests

os.chdir('D:/Python/worldquant')
s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201

U = 'https://api.worldquantbrain.com/users/self/alphas'
L = []

def show(tag, r):
    if r.status_code != 200:
        L.append('%-40s -> HTTP %s  %s' % (tag, r.status_code, r.text[:160].replace('\n', ' ')))
        return
    j = r.json()
    ks = sorted(j.keys())
    L.append('%-40s -> keys=%s' % (tag, ks))
    for k in ('count', 'total', 'next', 'previous'):
        if k in j and j[k] is not None:
            L.append('       %s = %s' % (k, j[k]))
    L.append('       results = %d' % len(j.get('results') or []))

L.append('== A. 参数组合探测 ==')
show('no-params', s.get(U))
show('limit=100', s.get(U, params={'limit': 100}))
show('limit=100&status=UNSUBMITTED', s.get(U, params={'limit': 100, 'status': 'UNSUBMITTED'}))
show('limit=100&stage=IS', s.get(U, params={'limit': 100, 'stage': 'IS'}))
show('limit=100&hidden=true', s.get(U, params={'limit': 100, 'hidden': 'true'}))
show('limit=100&hidden=false', s.get(U, params={'limit': 100, 'hidden': 'false'}))
show('limit=500', s.get(U, params={'limit': 500}))
show('limit=1000', s.get(U, params={'limit': 1000}))

L.append('')
L.append('== B. offset 边界扫描（limit=100）==')
for off in (0, 500, 900, 1000, 1050, 1090, 1100, 1101, 1150, 1200, 1500, 2000, 3000, 3400, 3500):
    show('offset=%d' % off, s.get(U, params={'limit': 100, 'offset': off}))

L.append('')
L.append('== C. UNSUBMITTED 过滤 + 大 offset ==')
for off in (0, 1000, 1100, 2000, 3000, 3500):
    show('UNSUBMITTED offset=%d' % off,
         s.get(U, params={'limit': 100, 'offset': off, 'status': 'UNSUBMITTED'}))

L.append('')
L.append('== D. 其他可能突破的参数 ==')
for p in ({'limit': 100, 'order': '-dateCreated'}, {'limit': 100, 'order': 'dateCreated'},
          {'limit': 100, 'type': 'REGULAR'}, {'limit': 100, 'hidden': 'true', 'status': 'UNSUBMITTED'}):
    show(str(p), s.get(U, params=p))

io.open('_autologs/_acct_probe.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
