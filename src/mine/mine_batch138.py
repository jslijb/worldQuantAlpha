# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch138 = 「中性化设置」轴（全新，未开采）
# 依据：mined 1175 条里 neutralization 分布 SUBINDUSTRY 1088 / INDUSTRY 117 / MARKET 14 / SECTOR 9 / NONE 2
#   → NONE、STATISTICAL、SECTOR 是空白区。中性化直接决定 PnL 的截面残差结构，
#     是比"换锚"更底层的几何变量（0916 已证：缩放基准 > 分组 > 锚）。
# 同时带上：/sales /EV 基准的 INDUSTRY 版、冷变量分桶分组、未用过的冷锚组。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=6, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
GBK= lambda x, b: f'group_rank({x}, {b})'

TXA='fnd6_txtubadjust'; AOL='fnd6_newa1v1300_aol2'; DPQ='fnd6_newqv1300_dpactq'
PST='fnd6_pstkl'; TXS='fnd6_txs'; MIB='fnd6_mfmq_mibtq'; TXP='fnd6_txtubposinc'
INV='fnd6_newqv1300_invrmq'; NOP='fnd6_newa2v1300_nopi'; RDI='fnd6_newqv1300_rdipdq'
LQP='fnd6_lqpl1'; STK='fnd6_stkcpa'; OPT='fnd6_optlifeq'

PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')
BK_PST = 'bucket(rank(fnd6_pstkl), range="0.1, 1, 0.1")'
BK_TXS = 'bucket(rank(fnd6_txs), range="0.1, 1, 0.1")'

def an(size):
    return (f'1.5*{G(TXA+"/"+size)} + {G(AOL+"/"+size)} + {G(DPQ+"/"+size)} + 0.75*{PVD5} + 0.75*{VOL12}')

C = [
 # ① 缩放基准不变（/cap，已知 floor 3.85），只换中性化 → 单独标定中性化的净效果
 ('w138_a', an('cap'), BASE(neut='NONE')),
 ('w138_b', an('cap'), BASE(neut='STATISTICAL')),
 ('w138_c', an('cap'), BASE(neut='SECTOR')),
 # ② /sales 与 /EV 基准配 INDUSTRY
 ('w138_d', an('sales'), BASE(neut='INDUSTRY')),
 ('w138_e', an('enterprise_value'), BASE(neut='NONE')),
 # ③ 冷变量分桶分组（分组变量本身换掉 → 截面划分完全不同）
 ('w138_f', ' + '.join([GBK(TXA+'/cap', BK_PST), GBK(AOL+'/cap', BK_PST), GBK(DPQ+'/cap', BK_PST), f'0.75*{PVD5}', f'0.75*{VOL12}']), BASE()),
 ('w138_g', ' + '.join([GBK(TXA+'/cap', BK_TXS), GBK(AOL+'/cap', BK_TXS), GBK(DPQ+'/cap', BK_TXS), f'0.75*{PVD5}', f'0.75*{VOL12}']), BASE()),
 # ④ 全新锚组（白名单里未被池子用过的冷字段）+ /cap
 ('w138_h', f'1.5*{G(RDI+"/cap")} + {G(LQP+"/cap")} + {G(STK+"/cap")} + {G(OPT+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE()),
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
    print('batch138 done', flush=True)
