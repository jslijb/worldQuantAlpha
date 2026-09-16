# -*- coding: utf-8 -*-
"""mine_neut_convert.py —— 通用「中性化转换器」：把一批达标候选换成其它中性化重跑

用途：候选表达式本身达标（S+F / tS / 无 FAIL 都过），但被 corr 封死无法提交。
      换中性化 = 换 PnL 的投影维度，对「表达式 ↔ 池子」的相关性做一次下移
      （0916 实测 −0.14 ~ −0.27），零新字段成本。
      一个表达式只能吃一口（MARKET 版入池后 SUB/SECTOR 版必撞它）。

用法：
  python src/mine/mine_neut_convert.py --cids w162_00,w162_01 --neuts MARKET,SECTOR --pfx x162
  python src/mine/mine_neut_convert.py --list _autologs/_backlog456.json --corr-max 0.78 --pfx x163
  python src/mine/mine_neut_convert.py --cids w172 --glob 'w172_*' --neuts MARKET

候选来源三选一：--cids a,b,c ｜ --glob 'w172_*' ｜ --list <json>（元素含 cid 字段 + 可选 corr）
过滤：--min-sf 4.0 --min-ts 1.25 --corr-max 0.78（--list 模式下按 corr 预筛）
自动跳过：已入池（台账）、表达式重复、已有同名产出
"""
import os as _os, pathlib as _pl, sys, json, glob, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
MINED = _pl.Path(OUT)


def opt(name, default=None):
    a = sys.argv
    for x in a:
        if x == name: return a[a.index(x) + 1]
        if x.startswith(name + '='): return x.split('=', 1)[1]
    return default


CIDSLIST = opt('--cids', '')
GLOBP = opt('--glob', '')
LISTJ = opt('--list', '')
NEUTS = [n.strip().upper() for n in opt('--neuts', 'MARKET,SECTOR').split(',') if n.strip()]
PFX = opt('--pfx', 'x')
MIN_SF = float(opt('--min-sf', 4.0))
MIN_TS = float(opt('--min-ts', 1.25))
CORR_MAX = float(opt('--corr-max', 1.01))
WORKERS = int(opt('--workers', 2))
LIMIT = int(opt('--limit', 9999))

# ---- 候选清单 ----
cids = []
if LISTJ:
    for it in json.load(open(LISTJ, encoding='utf-8')):
        cid = it.get('cid') if isinstance(it, dict) else it
        cr = (it or {}).get('corr') if isinstance(it, dict) else None
        if cid and (cr is None or cr <= CORR_MAX):
            cids.append(cid)
elif GLOBP:
    cids = sorted(_pl.Path(f).stem for f in glob.glob(f'{OUT}/{GLOBP}.json'))
elif CIDSLIST:
    cids = [c.strip() for c in CIDSLIST.split(',') if c.strip()]

submitted = {l.split(',')[0].strip('"') for l in
             open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig').read().splitlines()[1:]}

todo = []
seen = set()
for cid in cids:
    f = MINED / f'{cid}.json'
    if not f.exists():
        print(f'{cid} 无 mined 记录，跳过'); continue
    d = json.load(open(f, encoding='utf-8'))
    aid = d.get('id')
    if aid in submitted:
        print(f'{cid} ({aid}) 已入池，跳过'); continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < MIN_SF or (t.get('sharpe') or 0) < MIN_TS or fa:
        print(f'{cid} 不够格（SF={S+F:.2f} tS={t.get("sharpe")} FAIL={fa}），跳过'); continue
    ex = (d.get('regular') or {}).get('code') or ''
    if not ex or ex in seen:
        print(f'{cid} 表达式缺失/重复，跳过'); continue
    seen.add(ex)
    dec = (d.get('settings') or {}).get('decay', 10)
    for nt in NEUTS:
        todo.append((f'{PFX}_{cid.replace("_", "")}_{nt[:3]}', ex, nt, dec, cid))

todo = todo[:LIMIT]
print(f'候选表达式 {len(seen)} 个 × {len(NEUTS)} 中性化 = {len(todo)} 条待跑', flush=True)


def BASE(neut, delay):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': delay,
            'neutralization': neut, 'truncation': 0.08, 'pasteurization': 'ON', 'unitHandling': 'VERIFY',
            'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


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
    cid, expr, neut, dec, src = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(neut, dec), 'regular': expr}, cid)
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
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:300]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_neut'] = neut; d['_src'] = src
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} {neut:6s} SF={S+F:.2f} S={S:.2f} F={F:.2f} T={b.get('turnover')} tS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('mine_neut_convert done', flush=True)
