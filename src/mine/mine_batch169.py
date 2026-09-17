# -*- coding: utf-8 -*-
"""mine_batch169.py —— 换「缩放基准」（分母）抢救近门槛候选

背景：0916 晚二轮实测 —— 池子 76 条已把「/cap + /assets 缩放 + 现有价量腿几何」
这一族吃干（x162 12/12 撞墙、w166 2/2 撞墙，corr 0.686~0.877）。

李工项目已验证的杠杆优先级：**缩放基准 > 分组粒度 > 锚选择**。
池子里的锚腿全部是 `/cap` 或 `/assets`；本批把分母换成 **sales / revenue / ebit / ebitda**
（未开采的缩放基准），看能否在保住质量的同时把 corr 压下去。

源：两条只差 0.0014/0.0024 的擦线候选
  A = 1.5*group_rank(fnd6_newa1v1300_aol2/cap) + cash45 + accr + 1.5*ret5   (SECTOR, corr 0.6870)
  B = 1.5*group_rank(fnd6_pstkl/cap) + intg + xrent + 1.25*ret20           (MARKET,  corr 0.6864)

产出 data/alpha_quality_analysis/mined/x169_{cid}.json
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
RET5 = G('-ts_rank(returns, 5)')
RET20 = G('-ts_rank(returns, 20)')
INTG = G('-annual_intangible_assets_net_carrying_value/assets')

A = [
    ('A9_aol2_sales', f'1.5*{G("fnd6_newa1v1300_aol2/sales")} + {CASH45} + {G("fn_accrued_liab_curr_a/assets")} + 1.5*{RET5}'),
    ('A10_aol2_revt', f'1.5*{G("fnd6_newa1v1300_aol2/revenue")} + {CASH45} + {G("fn_accrued_liab_curr_a/assets")} + 1.5*{RET5}'),
    ('A11_aol2_ebit', f'1.5*{G("fnd6_newa1v1300_aol2/ebit")} + {CASH45} + {G("fn_accrued_liab_curr_a/assets")} + 1.5*{RET5}'),
    ('A12_accr_sales', f'1.5*{G("fnd6_newa1v1300_aol2/cap")} + {CASH45} + {G("fn_accrued_liab_curr_a/sales")} + 1.5*{RET5}'),
]
B = [
    ('B9_pstkl_sales', f'1.5*{G("fnd6_pstkl/sales")} + {INTG} + {G("fnd6_xrent/assets")} + 1.25*{RET20}'),
    ('B10_pstkl_revt', f'1.5*{G("fnd6_pstkl/revenue")} + {INTG} + {G("fnd6_xrent/assets")} + 1.25*{RET20}'),
    ('B11_pstkl_ebitda', f'1.5*{G("fnd6_pstkl/ebitda")} + {INTG} + {G("fnd6_xrent/assets")} + 1.25*{RET20}'),
    ('B12_intg_sales', f'1.5*{G("fnd6_pstkl/cap")} + {G("-annual_intangible_assets_net_carrying_value/sales")} + {G("fnd6_xrent/assets")} + 1.25*{RET20}'),
]
TODO = [(f'x169_{n}', e, 'SECTOR') for n, e in A] + [(f'x169_{n}', e, 'MARKET') for n, e in B]
print(f'换缩放基准变体 {len(TODO)} 条', flush=True)

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
print('batch169 done', flush=True)
