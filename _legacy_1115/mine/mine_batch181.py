# -*- coding: utf-8 -*-
"""mine_batch181.py —— leg_lab 搜索组合的批量执行器
读取 --combos <json>（leg_lab search --emit 产出），逐条真跑模拟。
断点续跑：os.path.exists 跳过；429/CONCURRENT 退避重试。
用法：python src/mine/mine_batch181.py --combos _autologs/search_combos_w180.json --workers 3
"""
import os as _os, pathlib as _pl, json, time, sys
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
COMBOS_F = sys.argv[sys.argv.index('--combos') + 1] if '--combos' in sys.argv else '_autologs/search_combos.json'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3
LIMIT = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 9999

COMB = json.load(open(COMBOS_F, encoding='utf-8'))
items = list(COMB.items())[:LIMIT]

BASE = {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
        'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
        'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
        'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def run_one(item):
    cid, meta = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    expr = meta['expr'] if isinstance(meta, dict) else meta
    meta = meta if isinstance(meta, dict) else {}
    st = dict(BASE)
    for k in ('neutralization', 'decay', 'universe', 'truncation', 'region', 'delay'):
        if meta.get(k) is not None:
            st[k] = meta[k]
    r = None
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json={'type': 'REGULAR', 'settings': st, 'regular': expr})
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            break
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return
    if r is None or r.status_code not in (200, 201):
        return
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
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:300]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_neut'] = st['neutralization']; d['_decay'] = st['decay']
    d['_trunc'] = st['truncation']; d['_note'] = meta.get('_note')
    d['_pred_S'] = meta.get('S'); d['_base_corr'] = meta.get('maxcorr')
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} SF={S+F:.2f} S={S:.2f} F={F:.2f} T={b.get('turnover')} tS={te.get('sharpe')} pred_corr={meta.get('maxcorr')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, items))
print('mine_batch181 done', flush=True)
