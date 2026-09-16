# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch135 = /cap 几何破墙族的「质量补强」批
# 核心假设（本批唯一目的）：batch131~134 的 /cap 家族 SF 天花板 3.93，
#   是因为把质量引擎腿（cash45 / cfoev45）丢掉了。
#   → 把质量引擎腿以 /cap 尺度放回来，看 SF 能否越 4.0，同时保住 corr<0.70 的几何。
# 正交变化：缩放基准(/cap,/sales,/enterprise_value) × 中性化(SUBINDUSTRY/INDUSTRY) × 锚组(三组互不重叠)
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=6, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'

# 锚（均出自 COLD_FIELD_WHITELIST.csv，hasData=Y）
TXA='fnd6_txtubadjust'; AOL='fnd6_newa1v1300_aol2'; DPQ='fnd6_newqv1300_dpactq'
TXP='fnd6_txtubposinc'; PST='fnd6_pstkl'; TXS='fnd6_txs'; MIB='fnd6_mfmq_mibtq'
INV='fnd6_newqv1300_invrmq'; RDI='fnd6_newqv1300_rdipdq'; NOP='fnd6_newa2v1300_nopi'
CIT='fnd6_newqv1300_citotalq'; OPT='fnd6_optlifeq'; ANO='fnd6_newa1v1300_ano'
AOLQ='fnd6_newqv1300_aol2q'

# 质量引擎腿（老池高 S 因子的共同来源），换成 /cap 尺度
ENG_CASH = 'ts_av_diff(cash/cap, 45)'
ENG_CFO  = 'ts_av_diff(cashflow_op/cap, 45)'
ENG_CASH_A = 'ts_av_diff(cash/assets, 45)'      # 对照：老尺度
ENG_CFO_A  = 'ts_av_diff(cashflow_op/enterprise_value, 45)'

# PV 腿（换个花样，避免与本族已入池的 kqoq0zed 撞 PnL 尾部）
PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')
PVD10 = G('-ts_delta(close, 10)')
VOL60 = G('volume/ts_mean(volume, 60)')

sc = lambda f, d: f'{f}/{d}'

C = [
 # A 组：/cap + 质量引擎（本批主假设）
 ('w135_a', f'1.5*{G(sc(TXA,"cap"))} + {G(sc(AOL,"cap"))} + {G(sc(DPQ,"cap"))} + 0.5*{G(ENG_CASH)} + 0.5*{G(ENG_CFO)} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='SUBINDUSTRY')),
 ('w135_b', f'1.5*{G(sc(TXA,"cap"))} + {G(sc(AOL,"cap"))} + {G(sc(DPQ,"cap"))} + 0.5*{G(ENG_CASH)} + 0.5*{G(ENG_CFO)} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='INDUSTRY')),
 # 对照：老 /assets 尺度 + 质量引擎（老骨架，应撞墙，用来标定 /cap 的净效果）
 ('w135_c', f'1.5*{G(sc(TXA,"assets"))} + {G(sc(AOL,"assets"))} + {G(sc(DPQ,"assets"))} + 0.5*{G(ENG_CASH_A)} + 0.5*{G(ENG_CFO_A)} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='SUBINDUSTRY')),
 # B 组：换锚组 + /cap + 质量引擎
 ('w135_d', f'1.5*{G(sc(TXP,"cap"))} + {G(sc(PST,"cap"))} + {G(sc(TXS,"cap"))} + 0.5*{G(ENG_CASH)} + 0.5*{G(ENG_CFO)} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='SUBINDUSTRY')),
 ('w135_e', f'1.5*{G(sc(AOLQ,"cap"))} + {G(sc(MIB,"cap"))} + {G(sc(OPT,"cap"))} + {G(sc(ANO,"cap"))} + 0.5*{G(ENG_CASH)} + 0.75*{PVD10} + 0.75*{VOL60}',
  BASE(neut='SUBINDUSTRY')),
 # C 组：换缩放基准（不是 /cap 也不是 /assets）
 ('w135_f', f'1.5*{G(sc(TXA,"sales"))} + {G(sc(AOL,"sales"))} + {G(sc(DPQ,"sales"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='SUBINDUSTRY')),
 ('w135_g', f'1.5*{G(sc(TXA,"enterprise_value"))} + {G(sc(AOL,"enterprise_value"))} + {G(sc(DPQ,"enterprise_value"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='SUBINDUSTRY')),
 # D 组：industry 分组 + /cap + 质量引擎
 ('w135_h', f'1.5*{GI(sc(TXA,"cap"))} + {GI(sc(AOL,"cap"))} + {GI(sc(DPQ,"cap"))} + 0.5*{GI(ENG_CASH)} + 0.5*{GI(ENG_CFO)} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE(neut='INDUSTRY')),
]

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def post_retry(payload, cid):
    for att in range(8):
        try: r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201): return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None

def run_one(item):
    cid, expr, s = item
    of = f'{OUT}/{cid}.json'
    if os.path.exists(of):
        print(f'{cid}已有产出，跳过', flush=True); return
    r = post_retry({'type':'REGULAR','settings':s,'regular':expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try: p = sess.get(loc)
        except Exception as e:
            print(cid,'NET-poll',e,flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra: time.sleep(float(ra)); continue
        break
    try: j = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = j.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(j)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch135 done', flush=True)
