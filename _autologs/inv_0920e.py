# -*- coding: utf-8 -*-
"""库存盘点：未提交、达标(S+F>=4.0,tS>=1.25,无FAIL)的候选，按 SF 排序"""
import os as _os, pathlib as _pl, json, glob, collections

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

MINED = 'data/alpha_quality_analysis/mined'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

sub = set()
for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    a = ln.split(',')[0].strip('"')
    if a:
        sub.add(a)

rows = []
batch = collections.Counter()
for f in glob.glob(f'{MINED}/*.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid or aid in sub:
        continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < 4.0 or (t.get('sharpe') or 0) < 1.25 or fa:
        continue
    cid = d.get('_cid') or _pl.Path(f).stem
    pg = cid.split('_')[0] if '_' in cid else cid
    batch[pg] += 1
    rows.append((S + F, S, F, t.get('sharpe'), aid, cid))

rows.sort(reverse=True)
out = []
out.append(f'未提交达标候选总数: {len(rows)}')
out.append(f'按批次前缀: {dict(batch.most_common(20))}')
out.append('')
out.append('SF     S      F      tS     id          cid')
for r in rows[:60]:
    out.append(f'{r[0]:5.2f}  {r[1]:5.2f}  {r[2]:5.2f}  {r[3]:5.2f}  {r[4]:11s} {r[5]}')
open('_autologs/inv_0920e.out', 'w', encoding='utf-8').write('\n'.join(out))
print('done', len(rows))
