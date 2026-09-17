# -*- coding: utf-8 -*-
"""mine_batch170.py —— 近门槛簇的最后一推：加腿稀释 + 换缩放基准

实测（0916 晚二轮）：同一族候选的本地 max corr 全部挤在 0.6864~0.6928，
距直通线 0.685 只差 0.001~0.008 —— 说明差的不是方向而是**一点点构成差异**。

两条已验证杠杆合并使用：
  ① 加腿稀释（w60_h .6548 / w64_h .6605 / w68_b .6948 / w77_a .6598 配方）
     —— 第 5 条腿用池子里没有的几何（换手距离 / 隔夜收益拆分）
  ② 换缩放基准（李工已验证的 #1 杠杆：/cap → /sales）
     —— 池子 76 条的锚腿全是 /cap 或 /assets，/sales 从未用过

基座（本地 corr 实测）：
  A1 = 1.5*aol2/cap + cash45 + accr + 1.5*ret10         SECTOR 0.6928  SF 4.47
  B0 = 1.5*pstkl/cap + intg + xrent + 1.25*ret20        MARKET 0.6864  SF 4.04

产出 data/alpha_quality_analysis/mined/x170_{cid}.json
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
CASH45 = G('ts_av_diff(cash/assets, 45)')
RET10 = G('-ts_rank(returns, 10)')
RET20 = G('-ts_rank(returns, 20)')
INTG = G('-annual_intangible_assets_net_carrying_value/assets')
XRENT = G('fnd6_xrent/assets')
TURN_D = G('-ts_rank(volume/ts_mean(volume, 120), 20)')
ON_P = G('-ts_rank(open/ts_delay(close, 1) - 1, 20)')

A1 = f'1.5*{G("fnd6_newa1v1300_aol2/cap")} + {CASH45} + {G("fn_accrued_liab_curr_a/assets")} + 1.5*{RET10}'
B0 = f'1.5*{G("fnd6_pstkl/cap")} + {INTG} + {XRENT} + 1.25*{RET20}'

A = [
    ('P1_a1_turndist', f'{A1} + 0.75*{TURN_D}'),
    ('P2_a1_overnite', f'{A1} + 0.75*{ON_P}'),
    ('P3_aol2_sales',  f'1.5*{G("fnd6_newa1v1300_aol2/sales")} + {CASH45} + {G("fn_accrued_liab_curr_a/assets")} + 1.5*{RET10}'),
    ('P4_accr_sales',  f'1.5*{G("fnd6_newa1v1300_aol2/cap")} + {CASH45} + {G("fn_accrued_liab_curr_a/sales")} + 1.5*{RET10}'),
]
B = [
    ('P5_b0_turndist', f'{B0} + 0.75*{TURN_D}'),
    ('P6_b0_overnite', f'{B0} + 0.75*{ON_P}'),
    ('P7_pstkl_sales', f'1.5*{G("fnd6_pstkl/sales")} + {INTG} + {XRENT} + 1.25*{RET20}'),
    ('P8_intg_sales',  f'1.5*{G("fnd6_pstkl/cap")} + {G("-annual_intangible_assets_net_carrying_value/sales")} + {XRENT} + 1.25*{RET20}'),
]
TODO = [(f'x170_{n}', e, 'SECTOR') for n, e in A] + [(f'x170_{n}', e, 'MARKET') for n, e in B]
print(f'近门槛推一把 {len(TODO)} 条', flush=True)

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
print('batch170 done', flush=True)
