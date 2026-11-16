# -*- coding: utf-8 -*-
"""w305 —— 母件 3qVkVR8X 深挖：SF 3.72 → 4.2（1010断层诊断后的定向打击）

═══ 断层诊断（今日实测 85 条 f2 系列，写在此处供后续追溯）═══
全局 SF 天花板 = **3.72**（母件 3qVkVR8X），门槛 4.2，缺 0.48。
全局 tS 天花板 = **1.49**（同一条母件），门槛 1.3，已过。
全局corr 最优 = **0.5447**（同一条母件），阈值 0.70，余量 0.155。

★ 核心发现：**母件 3qVkVR8X 是今日唯一 SF/tS/corr 三项同时最优的**，
  我后续加的所有配腿（lease_cur / lease_fut / sbp_nonvst / intang / accr）**全在拖 SF**：
    3qVkVR8X（oci×3.0 + e_cfo×0.5）           SF=3.72 tS=1.49 corr=0.5447
    w303 最好的 oci+lease_cur 组合                SF=3.49 tS=0.88 corr=0.6574
  ⇒ 符合 MEMORY 配方七「腿稀释」：**配腿的边际贡献为负**。

★ 为什么偏偏是 e_cfo 配出了效果：
  oci     = 其他综合收益/资产  →  **存量**（资产负债表某科目的水平）
  e_cfo   = ts_av_diff(cashflow_op/EV, 45) → **流量**（经营现金流的 45 日变化）
  一个存量、一个流量，经济含义完全正交 ⇒ 叠加才有增量信息。
  而 lease_cur / sbp_nonvst 都是**存量型会计科目**，跟 oci 同质 ⇒ 叠加只是稀释。

⇒ **本批的设计原则（照此枚举，不要再犯同质叠加的错）**：
  主腿 oci（存量，已验证 corr 0.5447/tS 1.49）
  ＋ **流量型配腿**（现金流/收入/利润/应计的**变化量**，不是水平）
  ＋ 弱量价腿（低权重只保 corr 不撞）

枚举：
  A. 流量腿库（全部是 ts_ 变化量，与 oci 正交）：
     cfo 变化（已验证最强）、收入变化、净利润变化、capex 变化、
     折旧摊销变化、营运资本变化、应计变化
  B. 流量腿权重扫（0.3~1.5，母件用 0.5 是最优区间）
  C. 分组轴（subindustry 已验证 0.5447，industry/market 作对照）
  D. decay 轴收口（TO 只有 2.2%，decay 10→20/40/80 看SF 是否随衰减改善）

用法：python src/mine/mine_w305_flow.py
输出：src/mine/w305_batches.json
"""
import os as _os, io, json, itertools
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

G = lambda x, g: f'group_rank({x}, {g})'
OCI = 'other_comprehensive_income_net_tax/assets'

# ★ 流量腿库：全部是「变化量」，与 oci（存量）正交
FLOW = {
    # 母件已验证的最优腿
    'f_cfo':    'ts_av_diff(cashflow_op/enterprise_value, 45)',
    'f_cfo_d':  'ts_delta(cashflow_op, 45)/enterprise_value',
    'f_rev':    'ts_av_diff(revenue/enterprise_value, 45)',
    'f_rev_d':  'ts_delta(revenue, 90)/enterprise_value',
    'f_ni':     'ts_av_diff(net_income/enterprise_value, 45)',
    'f_capex':  'ts_delta(capital_expenditure, 90)/assets',
    'f_dep':    'ts_delta(depreciation_and_amortization, 90)/assets',
    'f_ocf':    'ts_delta(cashflow_op, 45)/assets',
    'f_accr':   'ts_delta(fn_accrued_liab_curr_a, 90)/assets',
    'f_wc':     'ts_delta(working_capital, 90)/assets',
    'f_gross':  'ts_delta(gross_profit, 90)/assets',
    'f_eps':    'ts_delta(eps_basic, 90)/close',
}
# 量价腿（低权重，只保不撞 corr）
PRICE = {
    'p_vol':  'volume/ts_mean(volume, 90)',
    'p_rev5': '-ts_delta(close, 5)',
    'p_rk5':  '-ts_rank(returns, 5)',
    'p_illq': 'ts_mean(abs(returns)/volume, 20)',
}
GRP = ['subindustry', 'industry']
MAIN_W = [3.0]
FLOW_W = [0.3, 0.5, 0.75, 1.0, 1.5]

def build():
    out, seen = [], set()
    # 形态 A/B：oci + 单个流量腿（权重重扫）
    for fname, f in FLOW.items():
        for g in GRP:
            for mw in MAIN_W:
                for fw in FLOW_W:
                    cid = 'w305_%s_%s_%s_%s' % (fname, g, mw, fw)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    out.append(dict(cid=cid, form=fname, grp=g, mw=mw, fw=fw,
                                    code='%s*%s + %s*%s' % (mw, G(OCI, g), fw, G(f, g))))
    # 形态 C：oci + 流量腿 + 弱量价腿（三腿，测能否再补一点 SF）
    for fname, f in list(FLOW.items())[:6]:
        for pname, p in PRICE.items():
            for g in ('subindustry',):
                for fw in (0.5, 0.75):
                    for pw in (0.2, 0.3, 0.5):
                        cid = 'w305x_%s_%s_%s_%s_%s' % (fname, pname, g, fw, pw)
                        if cid in seen:
                            continue
                        seen.add(cid)
                        out.append(dict(cid=cid, form=fname + '+' + pname, grp=g, mw=3.0, fw=fw,
                                        code='3.0*%s + %s*%s + %s*%s'
                                             % (G(OCI, g), fw, G(f, g), pw, G(p, g))))
    return out

if __name__ == '__main__':
    out = build()
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w305_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条 → %s' % (len(out), p))
    print('流量腿库(%d):' % len(FLOW), list(FLOW))
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    print()
    print('★ 母件（今日唯一三项全优，目标 SF+0.48）：')
    print('  3qVkVR8X  SF=3.72 tS=1.49 平台corr=0.5447')
    print('  3.0*group_rank(other_comprehensive_income_net_tax/assets, subindustry)')
    print('  + 0.5*group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), subindustry)')
    print()
    print('★ 设计原则：oci=存量，配腿只用**流量**（变化量）——同质存量叠加只会稀释')
    for x in out[:3]:
        print(' ', x['cid'])
        print('   ', x['code'])