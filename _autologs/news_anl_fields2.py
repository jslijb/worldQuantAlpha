# -*- coding: utf-8 -*-
"""news_anl_fields2.py —— 盘点 News / Analyst 的**可用字段**（MATRIX 直用 + VECTOR 可聚合）

修正 news_anl_fields.py 的分页 bug（上一版把 analyst4 重复打了 10 次）：
  · 数据集列表必须**分页**拉（limit<=50），否则只拿到第一页
  · 字段列表也分页（offset），limit<=50
  · /data-fields 必带 instrumentType，否则 400
  · 429 要退避

输出：_autologs/_news_anl_fields2.txt（按类目分组，只留 cov>=0.7，MATRIX 优先）
"""
import os as _os, io, json, time
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import requests

OUT = io.open(ROOT / '_autologs' / '_news_anl_fields2.txt', 'w', encoding='utf-8')
def w(s=''):
    OUT.write(str(s) + '\n'); OUT.flush()

s = requests.Session()
s.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
for _a in range(6):
    try:
        if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        time.sleep(3)


def get(url, **params):
    for att in range(6):
        try:
            r = s.get(url, params=params, timeout=90)
        except Exception:
            time.sleep(3); continue
        if r.status_code == 429:
            time.sleep(6 * (att + 1)); continue
        return r
    return None


# ---------- 1. 数据集全量 ----------
sets = []
off = 0
while True:
    r = get('https://api.worldquantbrain.com/data-sets',
            instrumentType='EQUITY', region='USA', universe='TOP3000', delay=1,
            limit=50, offset=off)
    if r is None or r.status_code != 200:
        w('data-sets HTTP %s @offset %d' % (r.status_code if r else 'ERR', off)); break
    j = r.json()
    rows = j.get('results') or []
    if not rows:
        break
    sets.extend(rows)
    if len(rows) < 50 or len(sets) >= (j.get('count') or 0):
        break
    off += 50
w('数据集共 %d 个' % len(sets))

from collections import defaultdict
by = defaultdict(list)
for d in sets:
    by[((d.get('category') or {}).get('name')) or '?'].append(d)
w('类目分布：' + ', '.join('%s(%d)' % (k, len(v)) for k, v in sorted(by.items())))

TARGET = ['Analyst', 'News']
w('本次盘点：%s' % TARGET)
w('')

for cat in TARGET:
    for d in sorted(by.get(cat, []), key=lambda x: x.get('id') or ''):
        did = d.get('id')
        fields = []
        off = 0
        while True:
            r = get('https://api.worldquantbrain.com/data-fields',
                    instrumentType='EQUITY', region='USA', universe='TOP3000', delay=1,
                    **{'dataset.id': did}, limit=50, offset=off)
            if r is None or r.status_code != 200:
                w('[%s] %s 字段 HTTP %s' % (cat, did, r.status_code if r else 'ERR')); break
            j = r.json()
            rows = j.get('results') or []
            if not rows:
                break
            fields.extend(rows)
            tot = j.get('count') or 0
            if len(rows) < 50 or len(fields) >= tot:
                break
            off += 50
            time.sleep(0.15)
        w('=' * 122)
        w('[%s] %-20s 字段总数=%d  %s' % (cat, did, len(fields), d.get('name')))
        good = [f for f in fields if (f.get('coverage') or 0) >= 0.7]
        mats = [f for f in good if f.get('type') == 'MATRIX']
        vecs = [f for f in good if f.get('type') == 'VECTOR']
        w('  cov>=0.7 共 %d（MATRIX %d / VECTOR %d），全部类型：%s'
          % (len(good), len(mats), len(vecs),
             ', '.join(sorted({str(f.get('type')) for f in fields}))))
        for tag, lst in (('M', mats), ('V', vecs)):
            for f in sorted(lst, key=lambda x: -(x.get('coverage') or 0))[:60]:
                w('   %s %-42s cov=%.3f  %s' % (tag, f.get('id'), f.get('coverage') or 0,
                                                (f.get('description') or '')[:58]))
        w('')

OUT.close()
print('done')
