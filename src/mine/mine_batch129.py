# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch129 = 白名单新骨架组矿（batch128 覆盖验证之后）
# 结构：3 个白名单锚（全权，符号按单锚 S 修正）+ 2 条非拥挤价量腿 0.5 降权
#   价量腿用 vwap/ts_delta5 + vol120（w68_b 实证 corr 0.6948 的换腿组合，避开 close2/vol60 拥挤腿）
#   禁腿：cash/assets45、cashflow_op/ev45、ts_delta(close,2)、volume/ts_mean(volume,60)
import requests, json, time, os, csv
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WL  = 'data/alpha_quality_analysis/COLD_FIELD_WHITELIST.csv'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

# 1) 读白名单，按 |S| 排序取前 9
rows = [r for r in csv.DictReader(open(WL, encoding='utf-8-sig')) if r['hasData'] == 'Y']
rows.sort(key=lambda r: -abs(float(r['S'])))
top = [(r['field'], float(r['S'])) for r in rows[:9]]
print('白名单 top9:', [(f, s) for f, s in top], flush=True)

def A(field, s):
    e = f'{field}/assets'
    return f'-{e}' if s < 0 else e

def G(x): return f'group_rank({x}, subindustry)'

PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')

names = [f for f, _ in top]
signed = {f: s for f, s in top}
i = names.__getitem__

TRIPLES = [
    (0, 1, 2), (0, 1, 3), (0, 3, 4), (1, 3, 5),
    (1, 4, 5), (0, 4, 6), (2, 3, 7), (1, 5, 8),
]

C = []
for n, idx in enumerate(TRIPLES):
    anchors = [G(A(names[k], signed[names[k]])) for k in idx]
    expr = ' + '.join(anchors + [f'0.5*{PVD5}', f'0.5*{VOL12}'])
    C.append((f'w129_{chr(97+n)}', expr, BASE()))
# 第 9 条：top-4 锚 + VOLB 桶变体
anchors4 = [G(A(names[k], signed[names[k]])) for k in range(4)]
C.append(('w129_i', ' + '.join(anchors4 + [f'0.5*{PVD5}', f'0.5*{VOL12}']), BASE()))
for cid, expr, s in C:
    print(cid, '::', expr[:150], flush=True)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def post_retry(payload, cid):
    for att in range(8):
        try: r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201): return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None

def run_one(item):
    cid, expr, s = item
    of = f'{OUT}/{cid}.json'
    if os.path.exists(of):
        print(f'{cid}已有产出，跳过', flush=True); return
    r = post_retry({'type':'REGULAR','settings':s,'regular':expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try: p = sess.get(loc)
        except Exception as e:
            print(cid,'NET-poll',e,flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra: time.sleep(float(ra)); continue
        break
    try: j = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = j.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(j)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch129 done', flush=True)
