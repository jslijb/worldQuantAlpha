# -*- coding: utf-8 -*-
"""探查未开发数据集（news/model/option/pv）的可用字段，为下一批破墙实验选料"""
import requests, json, os, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
print('auth:', s.post('https://api.worldquantbrain.com/authentication').status_code)

out = []

# 1. 先拿全部数据集清单
r = s.get('https://api.worldquantbrain.com/data-sets',
          params={'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'limit': 50})
j = r.json()
ds = j if isinstance(j, list) else (j.get('results') or [])
out.append(f'可用数据集数: {len(ds)}  (类型样例: {type(ds[0]).__name__ if ds else "空"})')
out.append('')

# 兼容两种返回：字符串 ID 列表 / 对象列表
if ds and isinstance(ds[0], str):
    out.append(f'数据集 ID 列表: {", ".join(ds)}')
    detail = []
    for did in ds:
        try:
            rr = s.get(f'https://api.worldquantbrain.com/data-sets/{did}',
                       params={'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1})
            if rr.status_code == 200:
                dd = rr.json()
                detail.append(dd)
        except Exception:
            pass
        time.sleep(0.3)
    ds = detail
    out.append('')
    out.append(f"{'id':22} {'字段数':>7} {'alpha数':>9}  名称")
    for d in sorted(ds, key=lambda x: -(x.get('fieldCount') or 0)):
        out.append(f"{d.get('id'):22} {str(d.get('fieldCount')):>7} {str(d.get('alphaCount')):>9}  {d.get('name')}")
else:
    out.append(f"{'id':22} {'字段数':>7} {'alpha数':>9}  名称")
    for d in sorted(ds, key=lambda x: -(x.get('fieldCount') or 0)):
        out.append(f"{d.get('id'):22} {str(d.get('fieldCount')):>7} {str(d.get('alphaCount')):>9}  {d.get('name')}")

out.append('')
out.append('=== 重点数据集的字段抽样（低 alphaCount 优先）===')
WANT = ['news12', 'news', 'fundamental2', 'pv13', 'option8', 'model51', 'analyst4', 'fundamental6']
have = {d.get('id') for d in ds}
ids = [w for w in WANT if w in have] or [d.get('id') for d in ds[:6]]

for did in ids:
    for typ in ('MATRIX', 'VECTOR'):
        rows = []
        off = 0
        while off < 120:
            rr = s.get('https://api.worldquantbrain.com/data-fields',
                       params={'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000',
                               'delay': 1, 'dataset.id': did, 'type': typ, 'limit': 50, 'offset': off})
            if rr.status_code != 200:
                break
            jj = rr.json()
            res = jj.get('results') or []
            rows += res
            off += 50
            if off >= min(jj.get('count', 0), 120) or not res:
                break
            time.sleep(0.35)
        if not rows:
            continue
        rows.sort(key=lambda x: (x.get('alphaCount') if isinstance(x.get('alphaCount'), int) else 99999))
        out.append(f'--- {did} / {typ}: 共 {len(rows)} 个（抽样 120）---')
        for x in rows[:18]:
            out.append(f"   {x.get('id'):52} aC={str(x.get('alphaCount')):>6} "
                       f"u={str(x.get('userCount')):>5} | {str(x.get('description'))[:50]}")
        out.append('')

open('_autologs/datasets_recon.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:60]))
