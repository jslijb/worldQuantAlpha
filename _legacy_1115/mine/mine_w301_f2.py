# -*- coding: utf-8 -*-
"""w301 —— fundamental2 财报脚注无人区开矿（2026-10-10）

为什么开这一批（1010 战略纠偏 D-33 落地）：
  · 存量 445 条候选平台 selfCorr 全 0.798~0.989，一条都过不了 0.70 —— 已死。
  · 根因：全是同一族（ts_av_diff(cashflow_op/EV,45) + fnd6_xrent + ts_delta(close,N)），
    平台早已收录同款。
  · D-33 定的路：换信息维度。fundamental2（Report Footnotes，766 字段）
    cov>=0.7 的 56 个字段里 **55 个台账从未用过**（税务/租赁/股权激励/债务明细），
    平台收录极少 ⇒ corr 天然低。

结构设计（三腿，字段族互不重叠）：
  主腿  f2 脚注信号（税务/租赁/股权激励）× 2.0~2.5
  副腿  f2 脚注 × 0.5~1.0（不同经济含义，制造组内分化）
  引擎  弱共享腿 × 0.5（唯一保 SF 的来源，权重压到最低以控 corr）

经济含义（每条腿都要能一句话说清为什么）：
  · 递延税项/有效税率差  → 盈余质量与税收激进度的市场定价不足
  · 经营租赁最小付款  → 隐性负债被低估（表外杠杆）
  · 股权激励费用/未行权期权 → 管理层过度自信代理 + 稀释成本
  · 债务偿还/发行 → 再融资节奏与流动性压力

用法：python src/mine/mine_w301_f2.py
输出：src/mine/w301_batches.json（待模拟表达式清单）
"""
import os as _os, io, json, itertools, pathlib as _pl
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

G = lambda x, g='subindustry': f'group_rank({x}, {g})'
GM = lambda x: f'group_rank({x}, market)'

# ── 主腿：f2 脚注（每个都有独立经济含义）──
MAIN = {
    # 税务维度
    'tax_eff':G('(income_tax_expense_total - current_income_tax_expense_amount)/assets'),
    'tax_dta':G('-(deferred_tax_assets_net_value - deferred_tax_assets_valuation_allowance_value)/assets'),
    'tax_cash':G('income_taxes_paid_total/income_tax_expense_total'),
    'tax_dtl':G('deferred_tax_liabilities_total_4/assets'),
    # 租赁维度（表外杠杆）
    'lease_fut':G('-(future_minimum_operating_lease_payments + operating_leases_minimum_payments_due_five_years)/assets'),
    'lease_rent':G('net_operating_lease_rent_expense/assets'),
    'lease_cur':G('current_minimum_operating_lease_payment/assets'),
    # 股权激励维度（过度自信代理）
    'sbp_alloc':G('allocated_sbp_expense_total/assets'),
    'sbp_nonvst':G('sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a'),
    'opt_outstd':G('option_award_outstanding_count/fn_entity_common_stock_shares_out_a'),
    'opt_grant':G('option_awards_granted_count/assets'),
    'sbp_forfeit':G('non_option_equity_awards_forfeited_count/assets'),
    # 债务明细维度（再融资节奏）
    'dbt_repay':G('-(debt_repayments_total + line_of_credit_repayments)/assets'),
    'dbt_issue':G('debt_issuance_proceeds_2/assets'),
    'dbt_net':G('(debt_issuance_proceeds_2 - debt_repayments_total)/assets'),
    # 员工/其他
    'compr_tax':G('comprehensive_income_net_tax/assets'),
    'oci':G('other_comprehensive_income_net_tax/assets'),
    'compr_val':G('comprehensive_income_net_tax_value/assets'),
}

# ── 引擎腿：唯一与旧池重叠的弱腿，压到 0.5 保 SF ──
ENGINE = {
    'e_cfo':G('ts_av_diff(cashflow_op/enterprise_value, 45)'),
    'e_vol':G('volume/ts_mean(volume, 90)'),
}

# 三腿组合：主(2.0~2.5) + 副(0.5~1.0) + 引擎(0.5)
MAIN_W = (2.0, 2.5)
SUB_W = (0.5, 0.75, 1.0)
ENG_W = (0.5,)

# 经济含义分组：同组内不组合（避免同义重复），跨组自由配
GRP = {
    'tax': ['tax_eff', 'tax_dta', 'tax_cash', 'tax_dtl'],
    'lease': ['lease_fut', 'lease_rent', 'lease_cur'],
    'sbp': ['sbp_alloc', 'sbp_nonvst', 'opt_outstd', 'opt_grant', 'sbp_forfeit'],
    'debt': ['dbt_repay', 'dbt_issue', 'dbt_net'],
    'oci': ['compr_tax', 'oci', 'compr_val'],
}

def build():
    out = []
    seen = set()
    # 1) 双 f2 腿（主+副，跨经济组）
    for g1, g2 in itertools.permutations(GRP.keys(), 2):
        for m in GRP[g1]:
            for s in GRP[g2]:
                for mw in MAIN_W:
                    for sw in SUB_W:
                        for eng in ENGINE:
                            for ew in ENG_W:
                                cid = 'w301_%s__%s__%s_%s_%s' % (m, s, eng, mw, sw)
                                if cid in seen:
                                    continue
                                seen.add(cid)
                                code = ('%s*%s + %s*%s + %s*%s'
                                        % (mw, MAIN[m], sw, MAIN[s], ew, ENGINE[eng]))
                                out.append(dict(cid=cid, code=code,
                                                main=m, sub=s, eng=eng,
                                                grp=[g1, g2], mw=mw, sw=sw, ew=ew))
    # 2) 单 f2 腿（只有主腿 + 引擎，用来探哪类信号本身最强）
    for g1, members in GRP.items():
        for m in members:
            for mw in (2.0, 3.0):
                for eng in ENGINE:
                    for ew in ENG_W:
                        cid = 'w301solo_%s__%s_%s' % (m, eng, mw)
                        if cid in seen:
                            continue
                        seen.add(cid)
                        code = '%s*%s + %s*%s' % (mw, MAIN[m], ew, ENGINE[eng])
                        out.append(dict(cid=cid, code=code,
                                        main=m, sub=None, eng=eng,
                                        grp=[g1], mw=mw, sw=0, ew=ew))
    return out

if __name__ == '__main__':
    out = build()
    # 按字母数排序控算子上限（MEMORY：上限 64 含 +-*/）
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w301_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条表达式 → %s' % (len(out), p))
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    for x in out[:3]:
        print(' ', x['cid'])
        print('   ', x['code'])
