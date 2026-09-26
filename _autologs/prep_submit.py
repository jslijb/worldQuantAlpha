# -*- coding: utf-8 -*-
"""prep_submit.py —— 提交前体检：状态/设置/表达式/指标/FAIL 一次看清"""
import os as _os, pathlib as _pl, sys, json, io
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

ids = sys.argv[1].split(',')
sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass

L = []
led_ids = set()
for ln in io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig'):
    p = ln.split(',')
    if p:
        led_ids.add(p[0].strip().strip('"'))

for aid in ids:
    d = sess.get('https://api.worldquantbrain.com/alphas/' + aid).json()
    st = d.get('settings') or {}
    b = d.get('is') or {}
    te = d.get('test') or {}
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    L.append('=' * 96)
    L.append('%s  status=%s stage=%s  台账已收录=%s'
             % (aid, d.get('status'), d.get('stage'), aid in led_ids))
    L.append('  池=%s 中性=%s delay=%s decay=%s trunc=%s nan=%s'
             % (st.get('universe'), st.get('neutralization'), st.get('delay'),
                st.get('decay'), st.get('truncation'), st.get('nanHandling')))
    L.append('  S=%.4f F=%.4f TO=%.4f R=%.4f DD=%.4f margin=%.4gbp tS=%.4f'
             % (b.get('sharpe') or 0, b.get('fitness') or 0, b.get('turnover') or 0,
                b.get('returns') or 0, b.get('drawdown') or 0,
                (b.get('margin') or 0) * 10000, te.get('sharpe') or 0))
    L.append('  FAIL=%s' % fa)
    L.append('  expr: %s' % ((d.get('regular') or {}).get('code') or '')[:600])
    io.open('_autologs/_prep_%s.txt' % aid, 'w', encoding='utf-8').write('\n'.join(L) + '\n')

io.open('_autologs/_prep.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
