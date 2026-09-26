# -*- coding: utf-8 -*-
"""fields_of.py —— 任意数据集的可用字段盘点（MATRIX 优先，cov>=0.7）

用法：
  python _autologs/fields_of.py news18 option8 option9 socialmedia8 socialmedia12
输出：_autologs/_fields_of.txt
"""
import os as _os, io, sys, json, time
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import requests

OUT = io.open(ROOT / '_autologs' / '_fields_of.txt', 'w', encoding='utf-8')
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
            time.sleep(min(float(r.headers.get('Retry-After') or 6), 20)); continue
        return r
    return None


MINCOV = 0.7
for did in sys.argv[1:]:
    fields = []
    off = 0
    while True:
        r = get('https://api.worldquantbrain.com/data-fields',
                instrumentType='EQUITY', region='USA', universe='TOP3000', delay=1,
                **{'dataset.id': did}, limit=50, offset=off)
        if r is None or r.status_code != 200:
            w('[%s] HTTP %s' % (did, r.status_code if r else 'ERR')); break
        j = r.json()
        rows = j.get('results') or []
        if not rows:
            break
        fields.extend(rows)
        if len(rows) < 50 or len(fields) >= (j.get('count') or 0):
            break
        off += 50
        time.sleep(0.2)
    w('=' * 122)
    good = [f for f in fields if (f.get('coverage') or 0) >= MINCOV]
    mats = [f for f in good if f.get('type') == 'MATRIX']
    vecs = [f for f in good if f.get('type') == 'VECTOR']
    w('[%s] 字段总数=%d  cov>=%.1f 共 %d（MATRIX %d / VECTOR %d）'
      % (did, len(fields), MINCOV, len(good), len(mats), len(vecs)))
    for tag, lst in (('M', mats), ('V', vecs)):
        for f in sorted(lst, key=lambda x: -(x.get('coverage') or 0))[:70]:
            w('   %s %-46s cov=%.3f  %s' % (tag, f.get('id'), f.get('coverage') or 0,
                                            (f.get('description') or '')[:60]))
    w('')

OUT.close(); print('done')
