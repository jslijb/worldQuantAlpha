# -*- coding: utf-8 -*-
"""super_now.py — 发起 SUPER 模拟并按需提交
用法: super_now.py <selection> <combo> <limit> <decay> [--submit]
"""
import io, json, os, sys, time
os.chdir('D:/Python/worldquant')
sys.path.insert(0, '.')
from src.core.session import Brain

API = 'https://api.worldquantbrain.com'
SEL, COMBO, LIMIT, DECAY = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
DO_SUBMIT = '--submit' in sys.argv

payload = {
    'type': 'SUPER',
    'settings': {
        'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1,
        'decay': DECAY, 'neutralization': 'SUBINDUSTRY', 'truncation': 0.08,
        'pasteurization': 'ON', 'unitHandling': 'VERIFY', 'nanHandling': 'ON',
        'selectionHandling': 'POSITIVE', 'selectionLimit': LIMIT,
        'componentActivation': 'IS', 'language': 'FASTEXPR', 'visualization': False,
    },
    'combo': COMBO, 'selection': SEL,
}
b = Brain()
print('SUPER: sel=%r combo=%r limit=%d decay=%d submit=%s' % (SEL, COMBO, LIMIT, DECAY, DO_SUBMIT), flush=True)
r = b.s.post(API + '/simulations', json=payload, timeout=120)
print('  HTTP', r.status_code, (r.text or '')[:300], flush=True)
if r.status_code not in (200, 201):
    raise SystemExit('未受理')
loc = r.headers.get('Location')
if loc and loc.startswith('/'):
    loc = API + loc
print('  Location:', loc, flush=True)
if not loc:
    raise SystemExit('无 Location')

for i in range(60):
    time.sleep(20)
    try:
        rr = b.s.get(loc, timeout=60)
        j = rr.json() if (rr.text or '').strip() else {}
    except Exception as e:
        print('  poll err', str(e)[:60], flush=True); continue
    stt, aid = j.get('status'), j.get('alpha')
    print('  [%2d] %s prog=%s alpha=%s %s' % (i + 1, stt, j.get('progress'), aid, str(j.get('message') or '')[:70]), flush=True)
    if stt == 'ERROR':
        print('  ERROR:', str(j)[:400], flush=True); break
    if not aid:
        continue
    a = b.alpha(aid)
    isd = a.get('is') or {}
    print('  === id=%s S=%s F=%s TO=%s selfC=%s prodC=%s' % (
        aid, isd.get('sharpe'), isd.get('fitness'), isd.get('turnover'),
        isd.get('selfCorrelation'), isd.get('prodCorrelation')), flush=True)
    fails = []
    for c in (isd.get('checks') or []):
        print('    %-40s %-8s val=%s lim=%s' % (c.get('name'), c.get('result'), c.get('value'), c.get('limit')), flush=True)
        if c.get('result') == 'FAIL':
            fails.append(c.get('name'))
    io.open('_autologs/_super_%s.json' % aid, 'w', encoding='utf-8').write(json.dumps(a, ensure_ascii=False, indent=1))
    print('  FAILS:', fails, flush=True)
    if DO_SUBMIT:
        if fails:
            print('  !! 有 FAIL，拒绝提交', flush=True)
        else:
            sr = b.s.post(API + '/alphas/%s/submit' % aid, timeout=60)
            print('  SUBMIT ->', sr.status_code, (sr.text or '')[:300], flush=True)
    break
