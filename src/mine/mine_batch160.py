# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch160 = 【中性化设置轴】零新腿、零新字段、表达式一字不改，只动 settings.neutralization
#
# 动机（0916 晚，李工加压后立即执行，不留到明天）：
#   ① leg_lab 搜索已饱和：池子 73 条后，max corr ≤0.50 且 S≥2.25 只剩 5 个；
#   ② 换字段无效（batch155：/cap 把所有锚归一成同一个"市值"因子）；
#   ③ 换分组只小幅改善单腿 corr（batch159：Q_cfoV 0.6355 vs L_cfo 0.8024），低相关空间没打开。
#   ④ 查已提交 73 条的中性化分布 → SUBINDUSTRY 48 / INDUSTRY 26 / NONE 0 / MARKET 0 / SECTOR 0。
#      **这是唯一一个"池子里完全不存在"的 PnL 几何轴**（STATISTICAL 平台不可用，已踩 400）。
#
# 假设：手上 5 条候选表达式质量已达标（SF 4.25~5.68），卡的是 corr 0.716~0.768。
#   它们在 SUBINDUSTRY 外层底下再去均值 → PnL 与池子高度贴合；
#   换成 MARKET / NONE / SECTOR，**去均值的维度变了 → 同样的信号在不同维度上重新投影**，
#   组合权重不变、字段不变，但 PnL 几何应当错开 → corr 有希望掉到 0.70 以下。
#
# 判据（不是"跑出来了"就算成果）：
#   SF ≥ 4.0（S+F） + tS ≥ 1.25 + 无 FAIL + 本地 corr ≤ 0.685 → 才提交。
#   若 SF 掉到 4.0 以下只说明"中性化换来 corr 但赔了质量"，也算结论，照实记。
#
# 18 条 = 5 条卡住候选 × 3 中性化 + 1 条冠军配方(pwRwWoJ3) × 3 中性化做对照。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'


def BASE(neut, delay=10, trunc=0.08):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1,
            'decay': delay, 'neutralization': neut, 'truncation': trunc,
            'pasteurization': 'ON', 'unitHandling': 'VERIFY', 'nanHandling': 'ON',
            'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


# 5 条卡住候选（表达式原样搬，一行不改）
STUCK = {
    'N1a18988': '1.5*group_rank(fnd6_newqv1300_dpactq/cap, subindustry) + group_rank(ts_av_diff(cash/assets,45), subindustry) + group_rank(-ts_rank(returns, 20), subindustry) + group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)',
    'MPaPVYpM': '1.5*group_rank(fnd6_newa1v1300_aol2/cap, subindustry) + 0.75*group_rank(-ts_delta(close, 2), subindustry) + 0.75*group_rank(volume/ts_mean(volume, 120), subindustry) + 0.75*group_rank(-ts_rank(returns, 20), subindustry)',
    'd5b5voEJ': '1.5*group_rank(fn_accrued_liab_curr_a/assets, subindustry) + group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry) + group_rank(fnd6_xrent/assets, subindustry) + 1.5*group_rank(-ts_delta(close, 20), subindustry) + 1.5*group_rank(volume/ts_mean(volume, 60), subindustry) + 1.5*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)',
    '58z8eK91': '1.5*group_rank(ts_av_diff(cash/assets,45), subindustry) + group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry) + 0.75*group_rank(volume/ts_mean(volume, 90), subindustry) + 0.75*group_rank(-ts_rank(returns, 20), subindustry) + 0.75*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)',
    'qMxMV8NA': '1.5*group_rank(fnd6_pstkl/cap, subindustry) + group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry) + group_rank(fnd6_xrent/assets, subindustry) + 0.75*group_rank(-ts_delta(close, 20), subindustry) + 0.75*group_rank(-ts_rank(returns, 20), subindustry) + 0.75*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)',
    # 冠军配方对照（SF 6.91，corr 0.6474 已入池）—— 用它验证"换中性化是升还是降"
    'pwRwWoJ3': '1.5*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry) + group_rank(fn_accrued_liab_curr_a/assets, subindustry) + group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry) + group_rank(fnd6_xrent/assets, subindustry) + 1.5*group_rank(-ts_rank(returns, 20), subindustry) + 1.5*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)',
}

NEUTS = ['MARKET', 'NONE', 'SECTOR']

C = []
for aid, expr in STUCK.items():
    for neut in NEUTS:
        C.append((f'n160_{aid}_{neut[:3]}', expr, BASE(neut)))

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
                print(cid, 'skip(已存在)', flush=True); return
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
    d['_neut'] = st['neutralization']
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    print(f"{cid} {aid} neut={st['neutralization']:11s} S={S:.2f} F={(b.get('fitness') or 0):.2f} "
          f"SF={S+(b.get('fitness') or 0):.2f} T={b.get('turnover')} tS={te.get('sharpe')} FAIL={fa}", flush=True)


if __name__ == '__main__':
    print(f'共 {len(C)} 条：{len(STUCK)} 表达式 × {len(NEUTS)} 中性化', flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch160 done', flush=True)
