# -*- coding: utf-8 -*-
"""mine_batch177.py —— analyst4 二次开采：PEAD 盈余惊喜轴 + 0 阶扫描

背景（0917）：
  - 本地库存全杠杆闭合（x175 0/34、x176 decay 证伪 +0.02），当日产出必须来自新轴。
  - analyst4 1105 个 MATRIX 字段只用过 13 条表达式；过滤后 597 个未测（coverage>=0.6）。
  - 关键发现：`actual_eps_value_quarterly`（实际值）与 `anl4_afv4_eps_mean`（预期值）都在
    → **盈余惊喜 PEAD 轴**（(实际-预期)/|预期|），池内零条，且是经典异象（公告后漂移）。

三组实验：
  A. PEAD 惊喜轴：eps / sales / netincome 的 (actual-estimate)/|estimate|，
     四种包装（backfill 直用 / ts_av_diff 修正动量 / 60 日漂移窗 / 与覆盖数交互）。
  B. 0 阶扫描：甜档（100<=aC<=3000）按 coverage 排序前 30 个未测字段，
     `group_rank(ts_backfill(f,120), subindustry)`。
  C. 覆盖数延伸：*number 字段（f171 唯一存活轴 cov_ep 的兄弟）做 ts_av_diff 45。

产出 data/alpha_quality_analysis/mined/f177_{tag}.json
"""
import os as _os, pathlib as _pl, sys, json, time, re
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3
NSCAN = int(sys.argv[sys.argv.index('--nscan') + 1]) if '--nscan' in sys.argv else 30

G = lambda e: f'group_rank({e}, subindustry)'   # noqa: E731
BF = lambda e: f'ts_backfill({e}, 120)'          # noqa: E731

IDX = {x['id']: x for x in json.load(open('data/alpha_quality_analysis/analyst4_matrix_all.json', encoding='utf-8'))
       if x.get('type') == 'MATRIX' and (x.get('coverage') or 0) >= 0.6}

# ---------- A. PEAD 惊喜轴 ----------
pairs = []
for met, pat_act, pat_est in [
    ('eps', r'^actual_eps_value_quarterly$', r'^anl4_afv4_eps_mean$'),
    ('epsq', r'^actual_eps_value_quarterly$', r'^anl4_qfv4_eps_mean$'),
    ('sales', r'^actual_sales_value_quarterly$', r'anl4_afv4_(sal|sales)_mean$'),
    ('ni', r'^actual_netincome_value_quarterly$', r'anl4_afv4_(netincome|ni)_mean$'),
]:
    act = next((k for k in IDX if re.search(pat_act, k)), None)
    est = next((k for k in IDX if re.search(pat_est, k) and k != act), None)
    if act and est:
        pairs.append((met, act, est))
        print(f'PEAD 配对 {met}: {act} - {est}', flush=True)
    else:
        print(f'PEAD 配对 {met}: 缺字段 act={act} est={est}', flush=True)

todo = []
for met, act, est in pairs:
    surprise = f'({act} - {est})/abs({est})'
    tags = [
        ('sup',   G(BF(surprise))),
        ('mom',   G(BF(f'ts_av_diff({surprise}, 45)'))),
        ('drift', G(BF(f'ts_decay_linear({surprise}, 60)'))),
        ('zc',    G(BF(surprise.replace(act, f'ts_backfill({act},120)').replace(est, f'ts_backfill({est},120)')))),
    ]
    for tag, expr in tags:
        todo.append((f'f177_{met}_{tag}', expr, 'SUBINDUSTRY'))

# ---------- B. 0 阶扫描 ----------
tested_tail = ('epsr_number', 'netprofit_number', 'ptp_number', 'ebit_high', 'ebit_low', 'ebit_mean',
               'netprofit_high', 'netprofit_low', 'netprofit_mean', 'ptp_high', 'ptp_low', 'ptp_mean',
               'maxguidance', 'minguidance')
used = {c[4] if len(c) > 4 else '' for c in []}
scan = [x for x in IDX.values()
        if 100 <= (x.get('alphaCount') or 0) <= 3000
        and not x['id'].endswith(tested_tail)
        and not re.search(r'currency|flag$|^anl4_afv4_(eps|sal|sales|netincome|ni)_mean$', x['id'])]
scan.sort(key=lambda x: -(x.get('coverage') or 0))
for x in scan[:NSCAN]:
    f = x['id']
    todo.append((f'f177_z0_{f}'[:60], G(BF(f)), 'SUBINDUSTRY'))

# ---------- C. 覆盖数延伸 ----------
for k in sorted(IDX):
    if k.endswith('_number') and re.search(r'(sales|sal|netincome|ni|revenue|ebitda|cfo|ptp)', k) \
            and 100 <= (IDX[k].get('alphaCount') or 0) <= 3000:
        todo.append((f'f177_cov_{re.sub(r"^anl4_[a-z0-9]+_", "", k)[:24]}',
                     G(BF(f'ts_av_diff({k}, 45)')), 'SUBINDUSTRY'))

todo = [(cid, expr, neut) for cid, expr, neut in todo if not _os.path.exists(f'{OUT}/{cid}.json')]
print(f'\nbatch177 变体共 {len(todo)} 条（PEAD {len(pairs)*4} + 0阶 {min(NSCAN,len(scan))} + 覆盖数 {len(todo)-len(pairs)*4-min(NSCAN,len(scan))}）', flush=True)
for t in todo[:200]:
    print('   ', t[0], flush=True)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def BASE(neut):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
            'neutralization': neut, 'truncation': 0.08, 'pasteurization': 'ON',
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
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None


def run_one(item):
    cid, expr, neut = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(neut), 'regular': expr}, cid)
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
    d['_cid'] = cid; d['_neut'] = neut
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 3.0 and (te.get('sharpe') or 0) >= 1.0 and not fa) else ' fail '
    print(f'{flag} {cid:44s} {aid} S={S:5.2f} F={F:5.2f} SF={S+F:5.2f} T={b.get("turnover")} tS={te.get("sharpe")} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch177 done', flush=True)
