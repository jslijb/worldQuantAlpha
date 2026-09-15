# -*- coding: utf-8 -*-
"""本轮（0915 17:30 起）收尾汇总：台账 / 积压 / w122 终态。只读。"""
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import json, glob, csv, collections, os, requests

rows = list(csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
done = {r['id'].strip() for r in rows if r.get('id')}
print('台账 行数=%d 唯一id=%d' % (len(rows), len(done)))
print('美东按日:', dict(sorted(collections.Counter(r['dateSubmitted'][:10] for r in rows).items())))

tot = 0
bypre = collections.Counter()
qual = []
for f in sorted(glob.glob('data/alpha_quality_analysis/mined/*.json')):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid or aid in done:
        continue
    b = d.get('is') or {}
    te = d.get('test') or {}
    S = b.get('sharpe') or 0
    F = b.get('fitness') or 0
    tS = te.get('sharpe') or 0
    fails = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F >= 4.0 and tS >= 1.25 and not fails:
        tot += 1
        cid = d.get('_cid') or os.path.basename(f)[:-5]
        bypre[cid.split('_')[0]] += 1
        qual.append((cid, aid, round(S + F, 2), tS, S))
print('全局达标未提交候选 =', tot, dict(sorted(bypre.items())))
print('w122_ 达标未提交:', [q for q in qual if q[0].startswith('w122_')])

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201
for aid in ['883wqwVX', 'KPO1elgN', 'akLp3pzW']:
    d = s.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    ch = {c.get('name'): c.get('result') for c in (d.get('is') or {}).get('checks') or []}
    print('复查', aid, 'status=', d.get('status'), 'SELF_CORRELATION=', ch.get('SELF_CORRELATION'),
          'selfCorr=', (d.get('is') or {}).get('selfCorrelation'))
