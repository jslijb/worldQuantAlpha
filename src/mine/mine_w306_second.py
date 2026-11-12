# -*- coding: utf-8 -*-
"""w306 —— 第二条：换主腿（保留"存量+流量"范式，换 oci 为其他 f2 存量腿）

═══ 为什么必须换主腿（不能同骨架变体）═══
`kqgWNYw8` 已于 1010 ACCEPTED 入池（SF4.46/平台corr0.6081）。
同骨架的权重变体实测两两相关 **0.976~0.990**（E5R8m1kR / wpb2Qv72 vs kqgWNYw8），
按 CLAUDE.md §3 频控「每骨架每美东日只提1 条」，今日该骨架封顶。
⇒ 必须换**主腿字段**，但保留 1010 实证有效的结构范式。

═══ 保留的范式（1010 实测有效，不许改）═══
  存量腿（f2 会计科目水平）×3.0~3.5
  ＋ 流量腿（ts_av_diff(cashflow_op/EV, 45)）×1.0~1.5   ← f_cfo 是唯一到 4.46 的流量腿
  ＋ subindustry 轴（corr 0.54~0.61，比 industry 略低）
  关键：**存量 + 流量** 正交。同质叠加只会稀释（w303 全证）。

═══ 主腿候选池（f2 cov>=0.7 的存量型腿，atoms.md D-30 1010 复验有效集）═══
已测SF（单腿，含弱引擎）：lease_cur 3.29 / sbp_nonvst 2.47 / dbt_issue 2.54 / oci 3.72
未测的 f2 cov>=0.7 存量腿（从 fields_of 输出里挑同类）：
  · 租赁族：operating_lease_minimum_payments_due_* 系列（year2/3y/year4/five_years）
  · 债务族：debt_repayments_total / line_of_credit_repayments / repayments_of_credit_lines
  · 激励族：sbp_equity_nonvested_count / option_award_outstanding_count / option_awards_granted_count
  · 税务-已判死，排除
  · 折旧摊销 / 累计折旧 / 机械设备原值（gross_machinery_equipment_value_2）
  · comprehensive_income_net_tax / other_comprehensive_income_net_tax（compr_tax 已判死）

用法：python src/mine/mine_w306_second.py
输出：src/mine/w306_batches.json
"""
import os as _os, io, json, itertools
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

G = lambda x, g: f'group_rank({x}, {g})'

# ★ 唯一到SF4.46 的流量腿，固定不变
FLOW = 'ts_av_diff(cashflow_op/enterprise_value, 45)'

# 主腿候选池（f2 cov>=0.7 存量型；oci 是已入池的基准，保留作对照）
MAIN = {
    # 已测过SF 的四个（对照）
    'oci':        'other_comprehensive_income_net_tax/assets',
    'lease_cur':  'current_minimum_operating_lease_payment/assets',
    'dbt_issue':  'debt_issuance_proceeds_2/assets',
    'sbp_nonvst': 'sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a',
    # 未测的租赁族（同族但不同期限口径）
    'lease_y2':   'operating_leases_minimum_payments_due_year2/assets',
    'lease_3y':   'operating_leases_min_payments_3y/assets',
    'lease_y4':   'operating_leases_minimum_payments_due_year4/assets',
    'lease_5y':   'operating_lease_minimum_payments_due_five_years/assets',
    'lease_fut2': 'future_minimum_operating_lease_payments/assets',
    # 债务族
    'dbt_repay':  'debt_repayments_total/assets',
    'dbt_locr':   'line_of_credit_repayments/assets',
    'dbt_issue3': 'debt_issuance_proceeds_2/assets',
    # 激励族
    'opt_outstd': 'option_award_outstanding_count/fn_entity_common_stock_shares_out_a',
    'opt_grant':  'option_awards_granted_count/assets',
    'sbp_alloc2': 'allocated_sbp_expense_total/assets',
    # 折旧摊销 / 固定资产（全新维度，未碰过）
    'dep':        'depreciation_and_amortization/assets',
    'accdep':     'accumulated_depreciation_depletion_amortization_ppne/assets',
    'grosmach':   'gross_machinery_equipment_value_2/assets',
    # 税-已判死，留作对照不期望
    'tax_dtl2':   'deferred_tax_liabilities_total_4/assets',
}
GRP = ['subindustry', 'industry']
MAIN_W = [3.0, 3.5]
FLOW_W = [1.0, 1.5]

def build():
    out, seen = [], set()
    for name, m in MAIN.items():
        for g in GRP:
            for mw in MAIN_W:
                for fw in FLOW_W:
                    cid = 'w306_%s_%s_%s_%s' % (name, g, mw, fw)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    out.append(dict(cid=cid, main=name, grp=g, mw=mw, fw=fw,
                                    code='%s*%s + %s*%s' % (mw, G(m, g), fw, G(FLOW, g))))
    return out

if __name__ == '__main__':
    out = build()
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w306_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条 → %s' % (len(out), p))
    print('主腿池(%d 个):' % len(MAIN), list(MAIN))
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    print()
    print('★ 今日已入池基准：kqgWNYw8 SF=4.46 平台corr=0.6081 (oci×3.0 + cfo×1.5 subindustry)')
    print('★ 结构范式固定，只换主腿；同骨架变体 corr 0.976~0.990 今日不可再交')
    for x in out[:3]:
        print(' ', x['cid'])
        print('   ', x['code'])