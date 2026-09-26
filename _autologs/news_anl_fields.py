# -*- coding: utf-8 -*-
"""news_anl_fields.py —— 盘点 News / Analyst 类可用字段（下一个材质轴）

背景（0921 定论）：换池/换桶/换 decay 三条路今天全部撞自己入池的两条 TOP1000。
继续出量只能**换材质** —— 材料一直是 assets/close/cashflow_op/enterprise_value/cash/xrent/pstkl
这十来个字段。News 24 个数据集我们只用过 2 次、Analyst 12 个只用过几条。
本脚本把这两类的**字段名 + 覆盖率**拉出来，供组装"主腿 1.5~2.0 + 低共享锚"的批次。
"""
import os as _os, pathlib as _pl, json, io, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
for _a in range(6):
    try:
        if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        time.sleep(3)

L = []
ds = s.get('https://api.worldquantbrain.com/data-sets', params={'limit': 50}).json()
rows = ds if isinstance(ds, list) else (ds.get('results') or [])
if rows and isinstance(rows[0], str):
    rows = []
cat = {}
for d in rows:
    c = ((d.get('category') or {}).get('name')) or '?'
    cat.setdefault(c, []).append(d)
L.append('数据集类目：' + ', '.join('%s(%d)' % (k, len(v)) for k, v in sorted(cat.items())))

want = [c for c in cat if c in ('News', 'Analyst')]
L.append('本次盘点类目：%s' % want)
L.append('')

for c in want:
    for d in sorted(cat[c], key=lambda x: x.get('id') or ''):
        did = d.get('id')
        # ⚠ 必带 instrumentType，否则 400 Invalid query；限流要退避（429）
        r = None
        for att in range(5):
            r = s.get('https://api.worldquantbrain.com/data-fields',
                      params={'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000',
                              'delay': 1, 'dataset.id': did, 'limit': 50, 'order': '-coverage'})
            if r.status_code == 429:
                time.sleep(6 * (att + 1)); continue
            break
        if r is None or r.status_code != 200:
            L.append('%s/%s 字段拉取 HTTP%s' % (c, did, r.status_code if r is not None else 'ERR'))
            continue
        j = r.json()
        fs = j.get('results') or []
        L.append('=' * 110)
        L.append('[%s] %-22s 字段数=%s  名称=%s' % (c, did, j.get('count'), d.get('name')))
        for f in fs[:14]:
            L.append('   %-34s cov=%.2f  类型=%-8s  %s'
                     % (f.get('id'), f.get('coverage') or 0, f.get('type'),
                        (f.get('description') or '')[:64]))
        if len(fs) > 14:
            L.append('   … 其余 %d 个' % (len(fs) - 14))
        time.sleep(0.3)

io.open('_autologs/_news_anl_fields.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
