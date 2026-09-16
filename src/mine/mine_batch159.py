# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch159 = 【换分组/换算子腿库批】同一批字段，换"数理处理方法"
#
# 动机（0916 晚，池子 73 条后用尽）：
#   leg_lab 搜索显示「L 锚 + P 价量」几何已接近饱和——max corr ≤0.50 且 S≥2.25 的组合只剩 5 个。
#   继续靠换字段/换权重收益递减（换字段无效已被 batch155 证实：/cap 把所有锚归一成同一个"市值"因子）。
#   0914 研报结论里唯一没试过的杠杆正是**"不同数理方法处理同一数据"**。
#   实证支持：K_cfoI = group_rank(ts_av_diff(cashflow_op/enterprise_value,45), **industry**)
#     单腿 SF 3.36 / 无 FAIL，与 subindustry 版（L_cfo SF 3.57）指标相近但几何不同 → 池子里没有。
#   → 本批 24 条腿 = 同样的字段，换分组粒度（industry / sector / cap 分桶 / 波动分桶 / 量分桶）
#     + 换顶层算子（zscore / vec_avg 分析师评级轴）。
#   全部 base 设置一致（decay10/subindustry/trunc0.08/delay1），供 leg_lab 离线拼装。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
GS = lambda x: f'group_rank({x}, sector)'
GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'
GL = lambda x: f'group_rank({x}, bucket(rank(volume), range="0.1, 1, 0.1"))'

# 复用的核心字段（池子里最常用的几条 —— 换的只是分组）
XR  = 'fnd6_xrent/assets'
PST = 'fnd6_pstkl/cap'
CFO = 'ts_av_diff(cashflow_op/enterprise_value,45)'
ACC = 'fn_accrued_liab_curr_a/assets'

LEGS = {
 # ---- A. 换分组粒度（同字段，不同分组） ----
 'Q_xrI':   GI(XR),   'Q_pstI':  GI(PST),  'Q_cfoI': GI(CFO),  'Q_accI': GI(ACC),
 'Q_xrS':   GS(XR),   'Q_cfoS':  GS(CFO),  'Q_accS': GS(ACC),
 'Q_xrC':   GC(XR),   'Q_cfoC':  GC(CFO),  'Q_accC': GC(ACC),
 'Q_xrV':   GV(XR),   'Q_cfoV':  GV(CFO),  'Q_accV': GV(ACC),
 'Q_xrL':   GL(XR),   'Q_cfoL':  GL(CFO),  'Q_accL': GL(ACC),
 # ---- B. 顶层算子变体（同字段，换算子） ----
 'Q_xrZ':   'zscore(' + XR + ')',
 'Q_cfoQ':  'quantile(' + CFO + ')',
 'Q_accR':  'rank(' + ACC + ')',
 'Q_pstZ':  'zscore(' + PST + ')',
 # ---- C. 分析师评级轴（VECTOR 必须 vec_avg，池中从未用过） ----
 'Q_rate1': G('vec_avg(anl4_basicdetailrec_ratingvalue)'),
 'Q_rate2': G('vec_avg(anl4_fs_detail_rec_v4_nd_estimate)'),
 'Q_rate3': G('vec_avg(anl4_total_rec)'),
 'Q_rate4': G('-vec_avg(anl4_eaz2lrec_ratingvalue)'),
}

C = [(cid, expr, BASE()) for cid, expr in LEGS.items()]

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


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
    cid, expr, st = item
    of = f'{OUT}/{cid}.json'
    if os.path.exists(of):
        try:
            d = json.load(open(of))
            if (d.get('is') or {}).get('sharpe') is not None:
                return
        except Exception:
            pass
    r = post_retry({'type': 'REGULAR', 'settings': st, 'regular': expr}, cid)
    if not r:
        return
    loc = r.headers.get('Location')
    jj = None
    for _ in range(90):
        try:
            p = sess.get(loc)
        except Exception:
            time.sleep(10); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 10)); continue
        try: jj = p.json()
        except Exception: time.sleep(5); continue
        break
    if not jj:
        print(f'{cid} TIMEOUT', flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} R={b.get('returns')} tS={te.get('sharpe')} FAIL={fa}", flush=True)
    time.sleep(1)


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch159 done', flush=True)
