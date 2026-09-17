# -*- coding: utf-8 -*-
"""mine_batch174.py —— 「双新腿稀释」抢救 x172 未过线的 9 条近门槛候选

起点（0916 全库存筛查 src/analysis/screen_mined.py，560 条达标未提交候选）：
  只有 2 条基础 corr ≤0.70，9 条 ≤0.72，其余 549 条 ≥0.70。
  最接近的 9 条集中在 0.6860~0.7126，**全部共用同两条腿**：
    CFEV45 = group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)   （9 条里 7 条）
    RET5   = group_rank(-ts_rank(returns,5), subindustry)                            （9 条里 6 条）
  单腿稀释（x172）实测效力仅 **−0.02**，故本批改**一次挂两条新几何腿**，目标 −0.04。

四条稀释腿全部取自「池子里零条」的几何：
  OVN_TM = -ts_mean(open/ts_delay(close,1) - 1, 5)                       隔夜收益（均值版）
  INTRA  = -ts_rank(close/open - 1, 20)                                   日内收益（秩版）
  AMIH   = -ts_mean(abs(returns)/volume, 20)                              Amihud 流动性
  COV    = ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number,45),120)
                                                                          分析师 EPS 覆盖机构数变化
                                                                          （f171 唯一存活轴，池内零条）

每条候选挂 3 组腿对（自动跳过候选里已有的腿），权重 0.5。
中性化沿用各自原设置，质量引擎腿原样不动。

产出 data/alpha_quality_analysis/mined/x174_{cid}_{pair}.json
"""
import os as _os, pathlib as _pl, sys, json, time, csv
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2

G = lambda e: f'group_rank({e}, subindustry)'   # noqa: E731

# (短名, 完整腿表达式, 判定"已存在"的探测串)
LEGS = [
    ('OTM', G('-ts_mean(open/ts_delay(close, 1) - 1, 5)'), 'open/ts_delay(close, 1)'),
    ('AMI', G('-ts_mean(abs(returns)/volume, 20)'),        'abs(returns)/volume'),
    ('INT', G('-ts_rank(close/open - 1, 20)'),             'close/open'),
    ('COV', G('ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120)'), 'anl4_'),
]
W = 0.5

# --- 输入：全库存筛查结果里 corr 最低的 9 条 ---
SCR = 'data/alpha_quality_analysis/screened_mined.csv'
rows = list(csv.DictReader(open(SCR, encoding='utf-8-sig')))
rows.sort(key=lambda r: float(r['corr']))
picks = rows[:9]

LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
submitted = set(l.split(',')[0].strip('"') for l in open(LED, encoding='utf-8-sig').read().splitlines()[1:])

todo = []
for r in picks:
    if r['id'] in submitted:
        print(f"跳过已提交 {r['id']}", flush=True); continue
    cid = r['cid']
    src = f'{OUT}/{cid}.json'
    if not _os.path.exists(src):
        print(f'{cid} 源 json 缺失，跳过', flush=True); continue
    d = json.load(open(src, encoding='utf-8'))
    expr = (d.get('regular') or {}).get('code')
    neut = (d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'
    if not expr:
        print(f'{cid} 无表达式，跳过', flush=True); continue
    avail = [L for L in LEGS if L[2] not in expr]
    if len(avail) < 2:
        print(f'{cid} 可用新腿不足（{len(avail)}），跳过', flush=True); continue
    pairs = [(avail[0], avail[1])]
    if len(avail) >= 3:
        pairs += [(avail[1], avail[2]), (avail[0], avail[2])]
    for a, b in pairs:
        tag = f'{a[0]}{b[0]}'
        new = f'{expr} + {W}*{a[1]} + {W}*{b[1]}'
        todo.append((f'x174_{cid}_{tag}'[:64], new, neut, cid, r['id'], float(r['corr'])))

print(f'双新腿稀释变体 {len(todo)} 条（源 {len(picks)} 条近门槛候选）', flush=True)
for t in todo:
    print(f'   {t[0]:44s} {t[2]:11s} 基础corr={t[5]:.4f}', flush=True)

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
    print(f'{flag} {cid:44s} {neut:11s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} base={base_corr:.4f} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch174 done', flush=True)
