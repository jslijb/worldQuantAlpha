# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 只做 corr 预检，不提交（看地形用）
import requests, json, time, glob, sys
OUT='data/alpha_quality_analysis/mined'
pre=sys.argv[1] if len(sys.argv)>1 else 'w114_'
sess=requests.Session(); sess.auth=tuple(json.load(open('brain_credentials.txt')))
sess.post('https://api.worldquantbrain.com/authentication')

def quality_ok(d):
    b=d.get('is') or {}; te=d.get('test') or {}
    S=b.get('sharpe') or 0; F=b.get('fitness') or 0; tS=te.get('sharpe') or 0
    if S+F<4.0 or tS<1.25: return False
    for c in b.get('checks',[]):
        if c.get('result')=='FAIL': return False
    return True

for f in sorted(glob.glob(f'{OUT}/{pre}*.json')):
    d=json.load(open(f)); aid=d.get('id')
    if not aid: continue
    if not quality_ok(d):
        b=d.get('is') or {}
        print(d.get('_cid'), aid, 'SKIP(质量不达标)', flush=True); continue
    got=False
    for _ in range(70):
        r=sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
        if r.status_code==200 and r.headers.get('Retry-After'):
            time.sleep(float(r.headers['Retry-After'])); continue
        if r.status_code!=200: time.sleep(15); continue
        try: j=r.json()
        except Exception: time.sleep(10); continue
        recs=j.get('records') or []
        if not recs: time.sleep(10); continue
        mc=0; mid=''; hotS=0; hid=''
        for rec in recs:
            c=rec[5] if len(rec)>5 else 0; s_=rec[6] if len(rec)>6 else 0
            if c>mc: mc, mid = c, rec[0]
            if c>=0.7 and s_>hotS: hotS, hid = s_, rec[0]
        b=d.get('is') or {}
        verdict='PASS' if mc<0.7 else ('EXEMPT' if (b.get('sharpe') or 0) >= 1.10*hotS else 'BLOCK')
        print(f"{d.get('_cid')} {aid} S={b.get('sharpe'):.2f} corr={mc:.4f}(vs {mid}) 热S={hotS} 线={1.10*hotS:.3f} -> {verdict}", flush=True)
        got=True; break
    if not got: print(d.get('_cid'), aid, 'TIMEOUT', flush=True)
print('precheck done', flush=True)
