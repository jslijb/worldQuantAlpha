# -*- coding: utf-8 -*-
"""mine_batch162.py —— 中性化轴靶向扩产（0916 晚）

背景：w162/w164/w165 跑出一批 SF 4.3~5.9 / 无 FAIL 的候选，全部 SUBINDUSTRY，
      被 corr 0.71~0.84 挡住无法提交。已测出「同一表达式换 MARKET 中性化 =
      对该表达式与池子的相关性做一次下移（实测 -0.14 ~ -0.23）」。
      本批把这些表达式换成 MARKET / SECTOR 重跑 —— 同表达式、不同投影维度，
      表达式间相似度不变，但「表达式 ↔ 池」的关系被平移。

产出：data/alpha_quality_analysis/mined/x162_{src}_{neut}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
MINED = _pl.Path(OUT)

# 被 corr 挡住、但表达式本身达标（SF>=4.0 且 tS>=1.25 且无 FAIL）的候选
SRCS = ['w162_00', 'w162_01', 'w162_02', 'w162_03', 'w162_04', 'w162_05', 'w162_06', 'w162_07', 'w162_08', 'w162_09',
        'w164_00', 'w164_01', 'w164_02', 'w164_03', 'w164_04', 'w164_05', 'w164_06',
        'w165_00', 'w165_01', 'w165_02', 'w165_04', 'w165_05', 'w165_08',
        'w169_00', 'w169_01', 'w169_02', 'w169_03', 'w169_04']
NEUTS = ['MARKET', 'SECTOR']
LIMIT = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 999
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
EXPR_SRC = _pl.Path('_autologs/b162_expr.json')


def BASE(neut, delay=10, trunc=0.08):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': delay,
            'neutralization': neut, 'truncation': trunc, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
            'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


# 1) 从 mined 收集达标的表达式（跳过已提交过的）
submitted = set()
for ln in open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig').read().splitlines()[1:]:
    submitted.add(ln.split(',')[0].strip('"'))

todo = []
seen_expr = set()
for cid in SRCS:
    f = MINED / f'{cid}.json'
    if not f.exists():
        continue
    d = json.load(open(f, encoding='utf-8'))
    aid = d.get('id')
    if aid in submitted:
        print(f'{cid} 已入池，跳过'); continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if not (S + F >= 4.0 and (t.get('sharpe') or 0) >= 1.25 and not fa):
        print(f'{cid} 不够格（SF={S+F:.2f} tS={t.get("sharpe")} FAIL={fa}），跳过'); continue
    ex = (d.get('regular') or {}).get('code') or ''
    if not ex or ex in seen_expr:
        continue
    seen_expr.add(ex)
    dec = (d.get('settings') or {}).get('decay', 10)
    for nt in NEUTS:
        todo.append((f'x162_{cid}_{nt[:3]}', ex, nt, dec))

todo = todo[:LIMIT]
print(f'待跑 {len(todo)} 条（源 {len(seen_expr)} 个表达式 × {len(NEUTS)} 中性化）', flush=True)
json.dump({c: {'expr': e, 'neut': n, 'decay': dc} for c, e, n, dc in todo},
          open(EXPR_SRC, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


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
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None


def run_one(item):
    cid, expr, neut, dec = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(neut, dec), 'regular': expr}, cid)
    if r is None:
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
    d['_cid'] = cid; d['_neut'] = neut; d['_src'] = cid.split('_')[1]
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} {neut:6s} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get('turnover')} tS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch162 done', flush=True)
