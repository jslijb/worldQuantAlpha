# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 一次性 corr 快扫：每条候选只发 1 次请求（限速 1.4s），找出服务端已算完的候选
# 就绪（返回 records）的写入 _autologs/corr_ready_0915.txt，供提交器定向提交
import requests, json, time, csv, glob

OUT = 'data/alpha_quality_analysis/mined'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

done = set()
for row in csv.DictReader(open(LEDGER, encoding='utf-8-sig')):
    if row.get('id'): done.add(row['id'].strip())

def quality_ok(d):
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0; tS = te.get('sharpe') or 0
    if S + F < 4.0 or tS < 1.25: return False
    for c in b.get('checks', []):
        if c.get('result') == 'FAIL': return False
    return True

cands = []
for pre in ['w122_', 'w124_', 'w121_', 'w120_']:
    for f in sorted(glob.glob(f'{OUT}/{pre}*.json')):
        try: d = json.load(open(f))
        except Exception: continue
        aid = d.get('id')
        if aid and aid not in done and quality_ok(d):
            cands.append((d.get('_cid'), aid))
print(f'待扫 {len(cands)} 条', flush=True)

ready = []
for cid, aid in cands:
    try:
        r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
    except Exception as e:
        print(f'{cid} {aid} NET {e}', flush=True); time.sleep(1.4); continue
    if r.status_code == 200 and not r.headers.get('Retry-After'):
        try: recs = r.json().get('records') or []
        except Exception: recs = []
        if recs:
            mc = max((rec[5] for rec in recs if len(rec) > 5), default=0)
            print(f'{cid} {aid} READY max_corr={mc:.4f}', flush=True)
            ready.append((cid, aid, mc))
        else:
            print(f'{cid} {aid} 200-EMPTY(仍在算)', flush=True)
    else:
        print(f'{cid} {aid} {r.status_code} RA={r.headers.get("Retry-After")}(排队中)', flush=True)
    time.sleep(1.4)

with open('_autologs/corr_ready_0915.txt', 'w') as f:
    for cid, aid, mc in ready:
        f.write(f'{cid} {aid} {mc}\n')
print(f'=== 就绪 {len(ready)} 条 ===', flush=True)
