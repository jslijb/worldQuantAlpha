# -*- coding: utf-8 -*-
"""mine_batch166.py —— 补测 socialmedia12 的 12 个 MATRIX 字段（唯一尾账）

背景：batch165 用 `dataset.id=socialmedia12` 查字段返回空 → socialmedia12 一条没测。
但 `data/alpha_quality_analysis/socialmedia12_matrix_all.json` 里明明有 12 个
MATRIX 字段（scl12_buzz / scl12_sentiment / snt_buzz / snt_value ... 覆盖 0.97~1.0）。
本批直接按名单跑「我们验证过的最强包装」的 0 阶单腿：
    group_rank(ts_backfill(<field>, 120), subindustry)
达标线 SF >= 3.0 记为「可入腿库候选」；<=0 或 FAIL 即判死该数据集。

产出：data/alpha_quality_analysis/mined/f166_{field}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
SRC = 'data/alpha_quality_analysis/socialmedia12_matrix_all.json'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

raw = json.load(open(SRC, encoding='utf-8'))
fs = [f for f in raw if f.get('type') == 'MATRIX' and (f.get('coverage') or 0) >= 0.6]
fs.sort(key=lambda f: -(f.get('coverage') or 0))
todo = [(f'f166_{f["id"]}'[:60],
         f'group_rank(ts_backfill({f["id"]}, 120), subindustry)',
         f['id'], f.get('coverage'), f.get('alphaCount')) for f in fs]
print(f'socialmedia12 MATRIX 字段 {len(todo)} 条单腿待测', flush=True)


def BASE():
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
            'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON',
            'unitHandling': 'VERIFY', 'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


def post_retry(payload, cid):
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:200], flush=True); return None
    return None


def run_one(item):
    cid, expr, fid, cov, ac = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(), 'regular': expr}, cid)
    if r is None: return
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
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_field'] = fid; d['_ds'] = 'socialmedia12'; d['_cov'] = cov; d['_aC'] = ac
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '***强' if S + F >= 3.0 else (' 中' if S + F >= 2.2 else '  弱')
    print(f"{flag} {fid:34s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get('turnover')} tS={te.get('sharpe')} cov={cov} aC={ac} FAIL={fa}", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch166 done', flush=True)
