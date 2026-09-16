# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch139 = 「冷数据集新轴」批（项目首次动用 model51 / option8 / socialmedia12）
# 依据链：
#   ① 池子 62 个 alpha 的腿几乎全是 fnd6 基本面 + pv1；唯一例外 0mR2K6lr 用了 news_short_interest，而它是全池最强（S=3.45）
#   ② 今天新拉的三个数据集字段 alphaCount 极低：
#        model51: systematic_risk_last_30_days aC=1070 / correlation_last_30_days_spy 1395 / beta_last_30_days_spy 1827
#        option8: implied_volatility_mean_skew_20 aC=869 / skew_10 945
#        socialmedia12: snt_buzz_bfl_fast_d1 aC=281 / scl12_sentiment 4463
#      —— 比池内 fnd6 字段（aC 十万级）冷两个数量级，是教科书级的"独有成分腿"
#   ③ 已知质量天花板约在 4.0：本批用「冷锚 + 新数据轴腿」双轮换 + PV 引擎，赌质量与几何同时改善
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

# 冷锚（COLD_FIELD_WHITELIST，与 kqoq0zed 使用的 TXA/AOL/DPQ 完全不重叠）
TXP='fnd6_txtubposinc'; PST='fnd6_pstkl'; TXS='fnd6_txs'; MIB='fnd6_mfmq_mibtq'
INV='fnd6_newqv1300_invrmq'; CIT='fnd6_newqv1300_citotalq'; NOP='fnd6_newa2v1300_nopi'
LQP='fnd6_lqpl1'; STK='fnd6_stkcpa'; AOLQ='fnd6_newqv1300_aol2q'

# 新数据集腿（本批核心）
IVS20 = 'implied_volatility_mean_skew_20'
IVS60 = 'implied_volatility_mean_skew_60'
BETA30= 'beta_last_30_days_spy'
SYSR30= 'systematic_risk_last_30_days'
UNSY360='unsystematic_risk_last_360_days'
CORR30= 'correlation_last_30_days_spy'
SENT  = 'scl12_sentiment'
SBLF  = 'snt_buzz_bfl_fast_d1'
NEWSI = 'news_short_interest'

PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')
PVD10 = G('-ts_delta(close, 10)')
VOL90 = G('volume/ts_mean(volume, 90)')

C = [
 # A 组：期权隐含波动率偏斜（波动率偏斜溢价）作新轴
 ('w139_a', f'1.5*{G(TXP+"/cap")} + {G(PST+"/cap")} + {G(TXS+"/cap")} + {G(IVS20)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
 ('w139_b', f'1.5*{G(TXP+"/cap")} + {G(MIB+"/cap")} + {G(IVS60)} + {G(BETA30)} + 0.75*{PVD10} + 0.75*{VOL90}', BASE()),
 # B 组：系统性/非系统性风险（低 beta 异象）
 ('w139_c', f'1.5*{G(PST+"/cap")} + {G(CIT+"/cap")} + {G(NOP+"/cap")} + {G(SYSR30)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
 ('w139_d', f'1.5*{G(TXS+"/cap")} + {G(LQP+"/cap")} + {G(UNSY360)} + {G(CORR30)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
 # C 组：社交媒体情绪（池内零使用）
 ('w139_e', f'1.5*{G(TXP+"/cap")} + {G(STK+"/cap")} + {G(AOLQ+"/cap")} + {G(SENT)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
 ('w139_f', f'1.5*{G(MIB+"/cap")} + {G(INV+"/cap")} + {G(SBLF)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
 # D 组：新闻轴（池内唯一用过它的 0mR2K6lr 是全池最强）+ 全新锚组
 ('w139_g', f'1.5*{G(PST+"/cap")} + {G(TXS+"/cap")} + {G(NEWSI)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
 # E 组：双新轴叠加（波动率偏斜 + 情绪），换 industry 分组
 ('w139_h', f'1.5*{GI(TXP+"/sales")} + {GI(LQP+"/sales")} + {GI(IVS20)} + {GI(SENT)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
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
    print('batch139 done', flush=True)
