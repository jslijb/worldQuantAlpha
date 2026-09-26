# -*- coding: utf-8 -*-
"""核实刚提交的 alpha 是否真入池 + 台账口径"""
import os as _os, pathlib as _pl, json, collections
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
S = requests.Session()
S.auth = tuple(json.load(open('brain_credentials.txt')))
S.post('https://api.worldquantbrain.com/authentication')

ids = []
for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    a = ln.split(',')[0].strip('"')
    if a and a not in ids:
        ids.append(a)
out = [f'台账总行数(含表头): {len(open(LED, encoding="utf-8-sig").read().splitlines())}',
       f'唯一 id 数: {len(ids)}', '']
# 今天(美东 09-20)提交的
import csv as _csv
rows = list(_csv.reader(open(LED, encoding='utf-8-sig')))
hdr = rows[0]
di = hdr.index('dateSubmitted') if 'dateSubmitted' in hdr else 8
today = [r for r in rows[1:] if len(r) > di and r[di].startswith('2026-09-20')]
out.append(f'美东 09-20 提交行数: {len(today)}')
for r in today:
    out.append('   ' + r[0] + '  S=' + (r[2] if len(r) > 2 else '?') + '  F=' + (r[3] if len(r) > 3 else '?') + '  ' + r[di])
out.append('')
# 逐个核实最近 8 条状态
for aid in ids[-8:]:
    d = S.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    o = d.get('is') or {}
    out.append(f'{aid}  status={d.get("status")}  grade={d.get("grade")}  S={o.get("sharpe")}  F={o.get("fitness")}  dateSubmitted={d.get("dateSubmitted")}')
open('_autologs/verify_0920c.out', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
