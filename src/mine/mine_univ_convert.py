# -*- coding: utf-8 -*-
"""mine_univ_convert.py —— 通用「换池转换器」：把达标候选换 universe 重跑

为什么需要它（0921 实证，本项目最重要的一次发现）：
  官方评分四子项之一 **Universe（smaller universes get more score）** —— 我们
  97.9% 的产出是 TOP3000，等于一直在拿该项最低分。
  同时实测发现：**换小池直接破相关性墙**。
    · 账号 76 条非 TOP3000 里 41 条本地 corr 干净（其中 10 条 TOP1000 的
      corr_max = 0，与 107 条 TOP3000 池**完全正交**）；
    · 铁证 npdO71xw（TOP1000）对池子的 corr 分布：max 0.4806 / p90 0.3892 /
      中位 0.2834，**超过 0.50 的 0 条**；
    · 而**同样骨架在 TOP3000 的版本全部被墙封死**（corr 0.70~0.99）。
  ⇒ 换池 = 一箭双雕（Universe 子项加分 + 相关性下移），且零新字段成本。

一个池子只能吃一口：TOP1000 版入池后，同族的其它 TOP1000 版必撞它。

用法：
  python src/mine/mine_univ_convert.py --top 20 --unis TOP1000,TOP500 --pfx u
  python src/mine/mine_univ_convert.py --ids XgbgNwna,qMxM5j1A --unis TOP1000 --pfx u
  python src/mine/mine_univ_convert.py --from-api --top 10 --unis TOP1000 --dry

候选来源：平台 all_unsubmitted.json（默认）或 --ids 显式指定
"""
import os as _os, pathlib as _pl, sys, json, glob, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
API = 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'


def opt(name, default=None):
    a = sys.argv
    for x in a:
        if x == name: return a[a.index(x) + 1]
        if x.startswith(name + '='): return x.split('=', 1)[1]
    return default


IDS = [x.strip() for x in (opt('--ids', '') or '').split(',') if x.strip()]
UNIS = [u.strip().upper() for u in (opt('--unis', 'TOP1000,TOP500').split(',') if opt('--unis') else ['TOP1000', 'TOP500'])]
PFX = opt('--pfx', 'u')
TOP = int(opt('--top', 20))
MIN_SF = float(opt('--min-sf', 4.0))
MIN_TS = float(opt('--min-ts', 1.25))
MIN_F = float(opt('--min-f', 2.0))
MAX_TO = float(opt('--max-to', 0.20))
WORKERS = int(opt('--workers', 4))
DRY = '--dry' in sys.argv

submitted = {l.split(',')[0].strip('"') for l in
             open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig').read().splitlines()[1:]}


def g(d, *p, default=None):
    cur = d
    for k in p:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


data = json.load(open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])

pool = []
for a in data:
    st = a.get('settings') or {}
    if a.get('id') in submitted:
        continue
    if IDS:
        if a.get('id') not in IDS:
            continue
    else:
        if st.get('universe') != 'TOP3000':
            continue
        ch = g(a, 'is', 'checks', default=[]) or []
        fa = [c.get('name') for c in ch if c and c.get('result') == 'FAIL']
        S = g(a, 'is', 'sharpe') or 0; F = g(a, 'is', 'fitness') or 0
        TO = g(a, 'is', 'turnover'); tS = g(a, 'test', 'sharpe') or 0
        if fa or S + F < MIN_SF or tS < MIN_TS or F < MIN_F or (TO or 9) > MAX_TO:
            continue
    code = g(a, 'regular', 'code') or ''
    if not code:
        continue
    pool.append(dict(id=a.get('id'), code=code, st=st,
                     S=g(a, 'is', 'sharpe'), F=g(a, 'is', 'fitness'),
                     TO=g(a, 'is', 'turnover'), tS=g(a, 'test', 'sharpe')))

pool.sort(key=lambda x: -(x['F'] or 0))
if IDS:
    pass
else:
    pool = pool[:TOP]

# 表达式去重（同表达式只跑一次）
seen = set(); todo = []
for c in pool:
    if c['code'] in seen:
        continue
    seen.add(c['code'])
    for u in UNIS:
        todo.append((f"{PFX}_{str(c['id'])[:8]}_{u[:4]}", c['code'], u, c))

LOG = _os.path.join('_autologs', '_univ_run.txt')


def say(m):
    """既打 stdout 也自己落盘 —— 本机 PowerShell 管道会掐进程，必须有独立日志。"""
    try:
        print(m, flush=True)
    except Exception:
        pass
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(m + '\n')
    except Exception:
        pass


say('源候选 %d 个（去重表达式 %d）× %d 池 = %d 条待跑'
    % (len(pool), len(seen), len(UNIS), len(todo)))
for c in pool[:TOP]:
    say("  src %-11s S=%.2f F=%.2f TO=%.3f tS=%.2f  %s"
        % (c['id'], c['S'] or 0, c['F'] or 0, c['TO'] or 0, c['tS'] or 0, c['code'][:90]))
if DRY:
    sys.exit(0)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
_ok = False
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            _ok = True; break
    except Exception as e:
        print('auth retry', _a, str(e)[:60], flush=True)
    time.sleep(3 * (_a + 1))
assert _ok


def BASE(uni, src_st):
    """只改 universe，其余设置原样沿用源 alpha —— 保持单一变量。"""
    s = {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': uni, 'delay': 1, 'decay': 10,
         'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON',
         'unitHandling': 'VERIFY', 'nanHandling': 'ON', 'language': 'FASTEXPR',
         'visualization': False, 'startDate': '2019-01-01', 'endDate': '2023-12-31',
         'testPeriod': 'P1Y'}
    for k in ('delay', 'decay', 'neutralization', 'truncation', 'pasteurization',
              'unitHandling', 'nanHandling', 'region', 'instrumentType'):
        if src_st.get(k) is not None:
            s[k] = src_st[k]
    s['universe'] = uni
    return s


def post_retry(payload, cid):
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', str(e)[:80], flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:200], flush=True); return None
    return None


def run_one(item):
    cid, expr, uni, src = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(uni, src['st']), 'regular': expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try:
            p = sess.get(loc)
        except Exception as e:
            print(cid, 'NET-poll', str(e)[:80], flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(float(ra)); continue
        break
    try:
        jj = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:160], flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:220]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_univ'] = uni; d['_src'] = src['id']
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print("%s %s %-9s SF=%.2f S=%.2f F=%.2f T=%.3f tS=%s FAIL=%s [%s]"
          % (cid, aid, uni, S + F, S, F, b.get('turnover') or 0, te.get('sharpe'), fa, ok), flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('mine_univ_convert done', flush=True)
