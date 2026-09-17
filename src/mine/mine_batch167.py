# -*- coding: utf-8 -*-
"""mine_batch167.py —— 擦线候选定向抢救（只动价量腿，保住质量引擎）

背景：batch162 的 12 条中性化变体全部撞墙（corr 0.686~0.877），但其中两条
只差 0.0014/0.0024 就过线：
  - QPbZ5pZW (SECTOR) corr=0.6870 撞 kqoq0zed，SF=4.16 tS=1.55
  - 9qjZ9o3q (MARKET) corr=0.6864 撞 mLmwpAKK，SF=4.04 tS=1.28

这两条撞的对象里都含有与它们共享的价量腿（ret5/ret20/cash45）。按已验证有效的
「换价量腿」（w60_h/w64_h/w68_b/w77_a 配方）与「腿系数降权改 PNL 构成」
（w85_a 配方）做定向变体 —— **质量引擎腿（fnd6 锚 + cash45）一律保留**，
因为去引擎腿会把 SF 从 4.x 打到 3.4（已证）。

只做 8 条，8 分钟出结论。产出 data/alpha_quality_analysis/mined/x167_{cid}.json
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

G = lambda e: f'group_rank({e}, subindustry)'          # noqa: E731  统一包装（与源一致）
AOL2 = G('fnd6_newa1v1300_aol2/cap')
CASH45 = G('ts_av_diff(cash/assets, 45)')
ACCR = G('fn_accrued_liab_curr_a/assets')
PSTK = G('fnd6_pstkl/cap')
INTG = G('-annual_intangible_assets_net_carrying_value/assets')
XRENT = G('fnd6_xrent/assets')

RET5 = G('-ts_rank(returns, 5)')
RET10 = G('-ts_rank(returns, 10)')
RET20 = G('-ts_rank(returns, 20)')
AMIHUD = G('-ts_mean(abs(returns)/volume, 20)')
DCLOSE = G('-ts_delta(close, 20)')
V60 = G('volume/ts_mean(volume, 60)')

# 源 A（SECTOR）：1.5*aol2 + cash45 + accr + 1.5*ret5
A = [
    ('A1_swap_ret10', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{RET10}'),
    ('A2_swap_amihud', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{AMIHUD}'),
    ('A3_downweight_pv', f'2.0*{AOL2} + 0.5*{CASH45} + 2.0*{ACCR} + 0.5*{RET5}'),
    ('A4_swap_delta', f'1.5*{AOL2} + {CASH45} + {ACCR} + 1.5*{DCLOSE}'),
]
# 源 B（MARKET）：1.5*pstkl + intg + xrent + 1.25*ret20
B = [
    ('B1_swap_ret10', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{RET10}'),
    ('B2_swap_amihud', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{AMIHUD}'),
    ('B3_downweight_pv', f'2.0*{PSTK} + {INTG} + 2.0*{XRENT} + 0.5*{RET20}'),
    ('B4_swap_v60', f'1.5*{PSTK} + {INTG} + {XRENT} + 1.25*{V60}'),
]
TODO = [(f'x167_{n}', e, 'SECTOR') for n, e in A] + [(f'x167_{n}', e, 'MARKET') for n, e in B]
print(f'擦线抢救变体 {len(TODO)} 条', flush=True)

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
    print(f'{flag} {cid:18s} {neut:7s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, TODO))
print('batch167 done', flush=True)
