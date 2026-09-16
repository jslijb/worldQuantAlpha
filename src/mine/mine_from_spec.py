# -*- coding: utf-8 -*-
"""mine_from_spec.py —— 把 leg_lab 搜索出的组合直接跑真实模拟

用法：
  python src/mine/mine_from_spec.py _autologs/search_combos.json [--limit 16] [--workers 2]

spec json 形如：
  {"w158_00": {"expr": "...", "S": 2.31, "maxcorr": 0.6123, "nearest": "xxx"}, ...}

产出：data/alpha_quality_analysis/mined/{cid}.json + 控制台一行摘要
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
SPEC = sys.argv[1] if len(sys.argv) > 1 else '_autologs/search_combos.json'
LIMIT = 16
if '--limit' in sys.argv:
    LIMIT = int(sys.argv[sys.argv.index('--limit') + 1])
WORKERS = 2
if '--workers' in sys.argv:
    WORKERS = int(sys.argv[sys.argv.index('--workers') + 1])


def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': delay,
            'neutralization': neut, 'truncation': trunc, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
            'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


TAG = ''
if '--tag' in sys.argv:
    TAG = sys.argv[sys.argv.index('--tag') + 1]

# ---- 设置轴覆盖（0916 新增）：同一套组合换中性化/decay 重跑 = 换 PnL 投影维度 ----
NEUT = ''
if '--neut' in sys.argv:
    NEUT = sys.argv[sys.argv.index('--neut') + 1].upper()
DECAY = None
if '--decay' in sys.argv:
    DECAY = int(sys.argv[sys.argv.index('--decay') + 1])


def base_settings():
    st = BASE()
    if NEUT:
        st['neutralization'] = NEUT
    if DECAY is not None:
        st['decay'] = DECAY
    return st

spec = json.load(open(SPEC, encoding='utf-8'))
_raw = list(spec.items())[:LIMIT]
# 加 --tag 时用新编号，避免与上一批同名 json 撞车被当成"已有产出"跳过（0916 踩过）
items = [(f'{TAG}_{i:02d}', meta) for i, (_, meta) in enumerate(_raw)] if TAG else _raw
print(f'spec {len(spec)} 条，本次跑 {len(items)} 条', flush=True)

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
    cid, meta = item
    expr = meta['expr'] if isinstance(meta, dict) else meta
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': base_settings(), 'regular': expr}, cid)
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
    d['_cid'] = cid
    d['_pred'] = meta if isinstance(meta, dict) else {}
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    pd = (meta.get('maxcorr') if isinstance(meta, dict) else None)
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} R={b.get('returns')} tS={te.get('sharpe')} "
          f"FAIL={fa} [pred corr={pd}] [{ok}]", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, items))
print('mine_from_spec done', flush=True)
