# -*- coding: utf-8 -*-
"""mine_batch180.py —— 两条新腿的单腿模拟（供 leg_lab 入库）
  x180_leg_int : group_rank(-ts_rank(close/open - 1, 20), subindustry)   日内收益腿
  x180_leg_cov : group_rank(ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120), subindustry)  分析师覆盖数变化腿
复用 mine_neut_convert 的模拟框架；断点续跑（os.path.exists 跳过）。
"""
import os as _os, pathlib as _pl, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

OUT = 'data/alpha_quality_analysis/mined'
LEGS = [
    ('x180_leg_int', 'group_rank(-ts_rank(close/open - 1, 20), subindustry)'),
    ('x180_leg_cov', 'group_rank(ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120), subindustry)'),
]

BASE = {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
        'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
        'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
        'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

for cid, expr in LEGS:
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); continue
    r = None
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json={'type': 'REGULAR', 'settings': BASE, 'regular': expr})
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            break
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); r = None; break
    if r is None or r.status_code not in (200, 201):
        continue
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try:
            p = sess.get(loc)
        except Exception as e:
            print(cid, 'NET-poll', e, flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(float(ra)); continue
        break
    try:
        jj = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); continue
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:300]}', flush=True); continue
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_neut'] = 'SUBINDUSTRY'; d['_leg'] = True
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}
    print(f"{cid} {aid} S={b.get('sharpe')} F={b.get('fitness')} T={b.get('turnover')}", flush=True)
    time.sleep(1)
print('mine_batch180 done', flush=True)
