# -*- coding: utf-8 -*-
"""w303 —— oci 主腿 + 多腿提 SF（2026-10-10）

突破基础（1010 实测，非推测）：
  ★ `3qVkVR8X` = 3.0*group_rank(other_comprehensive_income_net_tax/assets, subindustry)
                + 0.5*group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), subindustry)
    平台 selfCorr = **0.5447**（硬阈值 0.70，余量 0.155）← 全项目 corr 最低
    S=2.19 F=1.53 **SF=3.72** / TO=2.2% / **tS=1.49** / 无 FAIL
    ⇒ 它是今天唯一同时「低 corr + 样本外稳」的一条，**唯一缺口是 SF 差 0.48**。
  对照：存量池最低 corr 只到 0.7754（差 0.23），f2 无人区方向完全证实。

为什么 OCI（other_comprehensive_income_net_tax）这个信号有货：
  OCI = 其他综合收益，是**绕过利润表直接进权益的会计科目**：
  外币折算差额（汇率变动对海外子公司报表的影响）、养老金 actuarial gain/loss、
  权益法投资被投方OCI 的份额、现金流套期储备变动。
  经济含义：① 这部分净资产**从未经过损益表**，市场对其定价最不充分；
    ② 养老金重估与汇率折算常是大额负值，构成"表外负债的镜像"；
    ③ 套期储备变动反映企业对冲的意图与成本。
  ⇒ OCI/总资产高 = 账面净资产里有一大块市场看不见、且常常是负的 ⇒ 定价偏低。

本批设计（只解决一件事：把 SF 从 3.72 抬到 4.2+，同时别把 corr 推过 0.70）：
  · 主腿 oci 权重固定 3.0（已验证的母件，不动，避免重掷 corr）
  · 配腿从 f2 有效四信号 + 弱引擎里挑，权重 0.3~1.0
  · 分组轴在 subindustry / industry / market / sector / **pvc11等分位桶** 里换
    （MEMORY：组别刀是当前最可靠的重掷手段，幅度 ±0.03~0.06）

用法：python src/mine/mine_w303_oci.py
输出：src/mine/w303_batches.json
"""
import os as _os, io, json, itertools
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

G = lambda x, g: f'group_rank({x}, {g})'

# 母件主腿（裸表达式，分组轴组合时现套）
OCI = 'other_comprehensive_income_net_tax/assets'

# 配腿池：f2 有效四信号（atoms.md D-30 1010 复验）+ 弱引擎
# 全部用 cov>=0.7 字段；税务族已判死不纳入
LEGS = {
    # f2 有效四信号（其他三个 SF 略低但 corr 也低，做差异化配腿）
    'lease_cur': 'current_minimum_operating_lease_payment/assets',
    'lease_fut': 'future_minimum_operating_lease_payments/assets',
    'sbp_nonvst': 'sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a',
    'opt_outstd': 'option_award_outstanding_count/fn_entity_common_stock_shares_out_a',
    'dbt_issue': 'debt_issuance_proceeds_2/assets',
    'dbt_repay': '-(debt_repayments_total + line_of_credit_repayments)/assets',
    # 弱引擎（保 SF 用，权重压低）
    'e_cfo': 'ts_av_diff(cashflow_op/enterprise_value, 45)',
    'e_vol': 'volume/ts_mean(volume, 90)',
    'e_illiq': 'ts_mean(abs(returns)/volume, 20)',
    'e_rev5': '-ts_delta(close, 5)',
    'e_rank5': '-ts_rank(returns, 5)',
    # 已验证的强腿（levR8Gz2 的无形资产腿，SF 结构好）
    'intang': '-annual_intangible_assets_net_carrying_value/assets',
    'accr': 'fn_accrued_liab_curr_a/assets',
}

# 分组轴：组别刀形态（MEMORY：subindustry↔industry 互换、内外层组互换幅度最大）
GRP = ['subindustry', 'industry', 'market', 'sector']

MAIN_W = [2.0, 3.0]          # oci 主腿权重（3.0 是已验证母件）
SUB_W = [0.3, 0.5, 0.75, 1.0]

def build():
    out, seen = [], set()
    # 形态①：oci 单腿 + 单配腿（最简，先探哪个配腿提SF 效果最好）
    for name, leg in LEGS.items():
        for g in GRP:
            for mw in MAIN_W:
                for sw in SUB_W:
                    cid = 'w303_%s_%s_%s_%s' % (name, g, mw, sw)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    out.append(dict(cid=cid, kind='solo',
                                    code='%s*%s + %s*%s' % (mw, G(OCI, g), sw, G(leg, g)),
                                    leg=name, grp=g, mw=mw, sw=sw))
    # 形态②：oci 双配腿（提 SF 更强，同时测两腿组合效应）
    for a, b in itertools.combinations(sorted(LEGS), 2):
        for g in ('subindustry', 'industry'):
            for mw in (2.0, 3.0):
                for sw in (0.4, 0.6):
                    cid = 'w303x_%s_%s_%s_%s_%s' % (a, b, g, mw, sw)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    out.append(dict(cid=cid, kind='duo',
                                    code='%s*%s + %s*%s + %s*%s'
                                         % (mw, G(OCI, g), sw, G(LEGS[a], g), sw, G(LEGS[b], g)),
                                    leg='%s+%s' % (a, b), grp=g, mw=mw, sw=sw))
    # 形态③：oi 主腿取负（做多"OCI 占比低"的对照组，测符号方向）
    for g in ('subindustry', 'industry'):
        for mw in (2.0, 3.0):
            for sw in (0.4, 0.6):
                cid = 'w303neg_%s_%s_%s' % (g, mw, sw)
                if cid in seen:
                    continue
                seen.add(cid)
                out.append(dict(cid=cid, kind='neg',
                                code='%s*%s + %s*%s' % (mw, G('-' + OCI, g), sw, G(LEGS['intang'], g)),
                                leg='-oci+intang', grp=g, mw=mw, sw=sw))
    return out

if __name__ == '__main__':
    out = build()
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w303_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条 → %s' % (len(out), p))
    print('形态分布:', {k: sum(1 for x in out if x['kind'] == k) for k in ('solo', 'duo', 'neg')})
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    print()
    print('★ 母件参照（已实测平台 corr=0.5447, SF=3.72, tS=1.49）：')
    print('  3.0*group_rank(other_comprehensive_income_net_tax/assets, subindustry)')
    print('  + 0.5*group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), subindustry)')
    print()
    for x in out[:3]:
        print(' ', x['cid'])
        print('   ', x['code'])