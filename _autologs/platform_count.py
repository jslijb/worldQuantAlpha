# -*- coding: utf-8 -*-
"""盘点平台侧已提交 alpha 数量 + Super Alpha 资格"""
import os as _os, pathlib as _pl, json, collections
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
s.post('https://api.worldquantbrain.com/authentication')

out = []
tot = None
allres = []
off = 0
while True:
    r = s.get('https://api.worldquantbrain.com/users/self/alphas',
              params={'limit': 100, 'offset': off, 'order': '-dateSubmitted'})
    if r.status_code != 200:
        out.append(f'GET alphas {r.status_code} {r.text[:200]}')
        break
    j = r.json()
    tot = j.get('count')
    res = j.get('results') or []
    allres += res
    if len(allres) >= (tot or 0) or not res:
        break
    off += 100

out.append(f'平台 alpha 总数: {tot}')
st = collections.Counter(a.get('status') for a in allres)
out.append(f'状态分布: {dict(st)}')
sub = [a for a in allres if a.get('dateSubmitted')]
ids = []
for a in sub:
    if a.get('id') not in ids:
        ids.append(a.get('id'))
out.append(f'有 dateSubmitted 的条数: {len(sub)}  唯一 id: {len(ids)}')
today = [a for a in sub if (a.get('dateSubmitted') or '').startswith('2026-09-20')]
out.append(f'美东 09-20 提交: {len(today)}')
for a in sorted(today, key=lambda x: x.get('dateSubmitted')):
    i = a.get('is') or {}
    out.append(f"  {a.get('id')}  S={i.get('sharpe')}  F={i.get('fitness')}  {a.get('dateSubmitted')}  {a.get('grade')}  {a.get('name')}")

# Super Alpha 资格
for ep in ['/users/self/super-alphas', '/users/self/competitions']:
    try:
        rr = s.get('https://api.worldquantbrain.com' + ep)
        out.append(f'{ep} -> {rr.status_code} {rr.text[:300]}')
    except Exception as e:
        out.append(f'{ep} -> ERR {e}')

open('_autologs/platform_count.out', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
