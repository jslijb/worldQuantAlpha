# -*- coding: utf-8 -*-
"""mine_batch175.py —— 拆解并复用「获胜腿组」（x174 唯一成功条目的机制）

x174 实测（11 条近门槛候选各挂两条新腿）：
  ✓ gJbkQ31Q  源 w164_05_TURND (base corr 0.6860)  + OTM + INT → **0.6037** 提交成功
  ✗ 其余 10 条 → 0.70~0.81（部分反而升高）

结论：**腿稀释效力不可外推，必须逐条实测**。但 gJbkQ31Q 掉幅 −0.082 说明
「加重隔夜腿 + 挂一条日内腿」这个组合对**这一族几何**（CFEV45+ACCR+XRENT+RET20/RET5）特别有效。

本批做两件事：
  1) **拆解**：在 gJbkQ31Q 的源候选上单独挂 INT / 单独挂 OTM，定位是哪条腿起的作用。
  2) **复用**：把获胜腿组套到筛查里 corr 0.70~0.78 的其余近门槛候选上（按 corr 升序取 14 条）。

变体（自动跳过候选里已存在的腿）：
  _I    = + 0.75*INT                              单独日内腿
  _B    = + 0.5*OTM + 0.5*INT                     获胜腿对
  _BIT  = + 0.5*OTM + 0.5*INT + 0.5*TURND         三腿加压

产出 data/alpha_quality_analysis/mined/x175_{cid}_{tag}.json
"""
import os as _os, pathlib as _pl, sys, json, time, csv
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3
TOPN = int(sys.argv[sys.argv.index('--topn') + 1]) if '--topn' in sys.argv else 15

G = lambda e: f'group_rank({e}, subindustry)'   # noqa: E731

OTM = G('-ts_mean(open/ts_delay(close, 1) - 1, 5)')   # 隔夜收益（与已有 OVN 同式，属加重）
INT = G('-ts_rank(close/open - 1, 20)')               # 日内收益（秩版）
TUR = G('-ts_rank(volume/ts_mean(volume, 120), 20)')  # 换手距离

SCR = 'data/alpha_quality_analysis/screened_mined.csv'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
submitted = set(l.split(',')[0].strip('"') for l in open(LED, encoding='utf-8-sig').read().splitlines()[1:])

rows = [r for r in csv.DictReader(open(SCR, encoding='utf-8-sig'))]
rows = [r for r in rows if r['id'] not in submitted and float(r['corr']) <= 0.78]
rows.sort(key=lambda r: float(r['corr']))
picks = rows[:TOPN]

todo = []
for r in picks:
    cid = r['cid']
    src = f'{OUT}/{cid}.json'
    if not _os.path.exists(src):
        print(f'{cid} 源 json 缺失，跳过', flush=True); continue
    d = json.load(open(src, encoding='utf-8'))
    expr = (d.get('regular') or {}).get('code')
    neut = (d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'
    if not expr:
        print(f'{cid} 无表达式，跳过', flush=True); continue
    has_int = 'close/open' in expr
    variants = []
    if not has_int:
        variants.append(('I', f'{expr} + 0.75*{INT}'))
        variants.append(('B', f'{expr} + 0.5*{OTM} + 0.5*{INT}'))
    variants.append(('BIT', f'{expr} + 0.5*{OTM} + 0.5*{INT} + 0.5*{TUR}'))
    for tag, new in variants:
        todo.append((f'x175_{cid}_{tag}'[:64], new, neut, cid, r['id'], float(r['corr'])))

print(f'拆解+复用变体 {len(todo)} 条（源 {len(picks)} 条 corr 0.70~0.78 候选）', flush=True)
for t in todo:
    print(f'   {t[0]:48s} {t[2]:11s} base={t[5]:.4f}', flush=True)

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
    cid, expr, neut, src_cid, src_aid, base_corr = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
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
    d['_cid'] = cid; d['_neut'] = neut; d['_src'] = src_cid; d['_src_aid'] = src_aid; d['_base_corr'] = base_corr
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' fail '
    print(f'{flag} {cid:46s} {neut:11s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} base={base_corr:.4f} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch175 done', flush=True)
