# -*- coding: utf-8 -*-
"""mine_batch168.py —— 用「全新价量几何」替换共享 PV 腿（破腿库饱和）

背景（0916 晚二轮）：x162 中性化变体 12/12 撞墙、w166 2/2 撞墙，说明
「SUBINDUSTRY + 现有价量腿几何」这一族已经被池子 76 条吃干 —— 只要新候选
仍用 -ts_rank(returns,5/10/20)、-ts_mean(abs(returns)/volume,20)、
-ts_delta(close,20)、volume/ts_mean(volume,60/120) 这几条腿，corr 必 0.69+。

本批改用**池子里从未出现过的价量几何**（来自球队硬币帖可移植 4 招，至今未用）：
  ON      = open / ts_delay(close, 1) - 1          隔夜收益拆分
  INTRA   = close / open - 1                       日内收益拆分
  TURN_D  = ts_rank(volume / ts_mean(volume,120), 20)  换手距离
质量引擎腿（fnd6 锚 + cash45）保留不动 —— 去引擎腿会把 SF 从 4.x 打到 3.4（已证）。
隔夜腿方向未定，正负两版都测。

产出 data/alpha_quality_analysis/mined/x168_{cid}.json
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

G = lambda e: f'group_rank({e}, subindustry)'   # noqa: E731
AOL2 = G('fnd6_newa1v1300_aol2/cap')
CASH45 = G('ts_av_diff(cash/assets, 45)')
ACCR = G('fn_accrued_liab_curr_a/assets')
PSTK = G('fnd6_pstkl/cap')
INTG = G('-annual_intangible_assets_net_carrying_value/assets')
XRENT = G('fnd6_xrent/assets')

ON_P = G('-ts_rank(open/ts_delay(close, 1) - 1, 20)')
ON_M = G('ts_rank(open/ts_delay(close, 1) - 1, 20)')
IN_P = G('-ts_rank(close/open - 1, 20)')
IN_M = G('ts_rank(close/open - 1, 20)')
TURN_D = G('-ts_rank(volume/ts_mean(volume, 120), 20)')

A = [
    ('A5_ovn_pos', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{ON_P}'),
    ('A6_ovn_neg', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{ON_M}'),
    ('A7_intra_pos', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{IN_P}'),
    ('A8_turndist', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{TURN_D}'),
]
B = [
    ('B5_ovn_pos', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{ON_P}'),
    ('B6_ovn_neg', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{ON_M}'),
    ('B7_intra_pos', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{IN_P}'),
    ('B8_turndist', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{TURN_D}'),
]
TODO = [(f'x168_{n}', e, 'SECTOR') for n, e in A] + [(f'x168_{n}', e, 'MARKET') for n, e in B]
print(f'全新几何变体 {len(TODO)} 条', flush=True)

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
    d['_cid'] = cid; d['_neut'] = neut
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' fail '
    print(f'{flag} {cid:16s} {neut:7s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, TODO))
print('batch168 done', flush=True)
