# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch140 = 「换结构」批（不是换数据、不是换参数）
# 依据链：
#   ① 池子 62 个 alpha 的表达式**全是加法式 group_rank/rank 求和**（骨架同源）→ 结构本身同质
#   ② batch139 实证：换数据（option8/model51/socialmedia12 冷数据集）质量不够（2.78~3.50）
#   ③ 换参数（decay/权重/PV 窗口）已被 batch131~136 证明是无效杠杆（天花板 3.99）
#   → 本批换**算子结构**与**中性化设置**，从"小改"到"大改"梯度排布，用来定位
#     "质量保住" 与 "几何错开" 的分界点。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=6, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'
GZ = lambda x: f'group_zscore({x}, subindustry)'
GBK= lambda x, b: f'group_rank({x}, {b})'

TXA='fnd6_txtubadjust'; AOL='fnd6_newa1v1300_aol2'; DPQ='fnd6_newqv1300_dpactq'
PST='fnd6_pstkl'; TXS='fnd6_txs'; TXP='fnd6_txtubposinc'
MIB='fnd6_mfmq_mibtq'; LQP='fnd6_lqpl1'; CIT='fnd6_newqv1300_citotalq'

PVR  = '-ts_delta(vwap, 5)'
VOLR = 'volume/ts_mean(volume, 120)'
BK_TS= 'bucket(rank(fnd6_txs), range="0.1, 1, 0.1")'

C = [
 # ── 小改：只换中性化设置（1175 条 mined 里 NONE 仅 2 条、STATISTICAL 0 条） ──
 ('w140_a', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.75*{G(PVR)} + 0.75*{G(VOLR)}', BASE(neut='NONE')),
 ('w140_b', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.75*{G(PVR)} + 0.75*{G(VOLR)}', BASE(neut='STATISTICAL')),
 ('w140_c', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.75*{G(PVR)} + 0.75*{G(VOLR)}', BASE(neut='SECTOR')),
 # ── 中改：换包裹算子（group_zscore）／换分组变量（冷字段分桶） ──
 ('w140_d', f'1.5*{GZ(TXA+"/cap")} + {GZ(AOL+"/cap")} + {GZ(DPQ+"/cap")} + 0.75*{GZ(PVR)} + 0.75*{GZ(VOLR)}', BASE()),
 ('w140_e', ' + '.join([GBK(TXA+'/cap', BK_TS), GBK(AOL+'/cap', BK_TS), GBK(DPQ+'/cap', BK_TS),
                        f'0.75*{GBK(PVR, BK_TS)}', f'0.75*{GBK(VOLR, BK_TS)}']), BASE()),
 ('w140_f', f'1.5*{G(PST+"/cap")} + {G(TXS+"/cap")} + {G(MIB+"/cap")} + 1.5*({G(PVR)}*{G(VOLR)})', BASE()),
 # ── 大改：整条表达式不再用 group_rank 求和 ──
 ('w140_g', f'1.5*zscore({TXA}/cap) + zscore({AOL}/cap) + zscore({DPQ}/cap) + 0.75*zscore({PVR}) + 0.75*zscore({VOLR})', BASE()),
 ('w140_h', f'1.5*{G("ts_rank("+TXA+"/cap, 60)")} + {G("ts_rank("+AOL+"/cap, 60)")} + {G("ts_rank("+DPQ+"/cap, 60)")} + 0.75*{G(PVR)} + 0.75*{G(VOLR)}', BASE()),
 ('w140_i', f'{G("("+TXA+"-"+LQP+")/cap")} + {G(TXS+"/cap")} + {G(CIT+"/cap")} + 0.75*{G(PVR)} + 0.75*{G(VOLR)}', BASE()),
 ('w140_j', f'1.5*{G("winsorize("+TXA+"/cap, std=4)")} + {G(AOL+"/cap")} + {G("signed_power("+DPQ+"/cap, 0.5)")} + 0.75*{G(PVR)} + 0.75*{G(VOLR)}', BASE()),
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
        print(f'{cid} SIM-FAIL {json.dumps(j)[:300]}', flush=True); return
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
    print('batch140 done', flush=True)
