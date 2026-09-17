# -*- coding: utf-8 -*-
"""mine_batch172.py —— 量产动作：受阻库存 + 第 5 条「新几何腿」稀释

来源（0916 晚二轮实证）：
  58znv2Y1 = A1（SF 4.47 / 本地 corr 0.6928，卡死）**+ 0.75*隔夜收益拆分腿**
           → SF 4.58 / 本地 corr **0.6706** → 提交实测 selfCorr 0.6726 **ACCEPTED**
即：**在受阻候选上挂一条池子里没有的几何腿，做 0.75 权重稀释**，能实打实把
corr 从 0.69 压到 0.67 以下，而且质量不降（SF 4.47→4.58）。

本批把这一动作套到 `_autologs/_blocked_cands.json`（22 条 SF 4.22~6.05 却因 corr 未提交）
里 **pred 最低的 12 条**上（pred 是 leg_lab 预测值，系统性低估 0.05~0.19，故按升序取）。
第 5 条腿在三种新几何间轮换，避免新候选之间互相撞：
  ON_P    = -ts_rank(open/ts_delay(close,1) - 1, 20)     隔夜收益拆分
  IN_P    = -ts_rank(close/open - 1, 20)                 日内收益拆分
  TURN_D  = -ts_rank(volume/ts_mean(volume,120), 20)     换手距离
质量引擎腿原样保留，中性化沿用各自原设置。

产出 data/alpha_quality_analysis/mined/x172_{cid}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
TOPN = int(sys.argv[sys.argv.index('--topn') + 1]) if '--topn' in sys.argv else 12

G = lambda e: f'group_rank({e}, subindustry)'   # noqa: E731
LEGS = [
    ('OVN', G('-ts_rank(open/ts_delay(close, 1) - 1, 20)')),
    ('INTRA', G('-ts_rank(close/open - 1, 20)')),
    ('TURND', G('-ts_rank(volume/ts_mean(volume, 120), 20)')),
]

blocked = json.load(open('_autologs/_blocked_cands.json', encoding='utf-8'))
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
submitted = set(l.split(',')[0].strip('"') for l in open(LED, encoding='utf-8-sig').read().splitlines()[1:])

cands = [(aid, v) for aid, v in blocked.items() if aid not in submitted and v.get('SF', 0) >= 4.5]
cands.sort(key=lambda kv: kv[1].get('pred') or 9)
todo = []
for i, (aid, v) in enumerate(cands[:TOPN]):
    cid = v['cid']
    src = f'{OUT}/{cid}.json'
    if not _os.path.exists(src):
        print(f'{cid} 源 json 缺失，跳过', flush=True); continue
    d = json.load(open(src, encoding='utf-8'))
    expr = (d.get('regular') or {}).get('code')
    neut = (d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'
    if not expr:
        print(f'{cid} 无表达式，跳过', flush=True); continue
    lname, leg = LEGS[i % len(LEGS)]
    todo.append((f'x172_{cid}_{lname}'[:60], f'{expr} + 0.75*{leg}', neut, cid, aid))

print(f'受阻库存稀释变体 {len(todo)} 条（源 {len(cands)} 条候选中取 pred 最低的 {TOPN}）', flush=True)
for t in todo:
    print('   ', t[0], t[2], flush=True)

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
    cid, expr, neut, src_cid, src_aid = item
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
    d['_cid'] = cid; d['_neut'] = neut; d['_src'] = src_cid; d['_src_aid'] = src_aid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' fail '
    print(f'{flag} {cid:26s} {neut:11s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch172 done', flush=True)
