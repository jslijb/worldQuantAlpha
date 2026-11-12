# -*- coding: utf-8 -*-
"""w302 —— lease_cur + sbp_nonvst 双强原子组合（2026-10-10）

来源（实测，非推测）：
  w301 52 条f2 脚注单腿探针跑出 13 条真实结果，**只有 2 个 f2 信号无 FAIL 且 SF 过 2**：
    · lease_cur（当期经营租赁最小付款/assets）SF=3.29 / S1.84 F1.45 TO2.6% / subSharpe1.21
      id=YPMEbWVM代码：2.0*group_rank(current_minimum_operating_lease_payment/assets, subindustry)
                        + 0.5*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)
    · sbp_nonvst（未归属股权激励数/总股本）SF=2.47 / S1.41 F1.06 TO4.3% / subSharpe0.64
      id=omWJLOEn  代码：2.0*group_rank(sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a, subindustry)
                        + 0.5*group_rank(volume/ts_mean(volume,90), subindustry)
  税务三兄弟（tax_cash/tax_dtl）SF 0.97~1.96 且全带 LOW_SHARPE/LOW_FITNESS ⇒ **税务维度判死**。

经济含义（两个维度必须正交，这是能叠的前提）：
  · lease_cur：当期应付经营租赁款/资产。衡量**表外杠杆的当期强度**——
    零售、餐饮、航空这类租店经营的公司，真实负债不在资产负债表上，
    租金进了利润表但债务没进，市场对其定价不足。租赁强度高的定价偏低。
  · sbp_nonvst：未归属（已授予未归属）股权激励数/总股本。衡量**管理层过度自信的代理**
    ——公司愿意为还没解锁的激励付多少，隐含管理层对股价的预期；
    未归属比例高 = 潜在稀释大 + 管理层押注。过度自信文献（Cooper/Gulen/Schill）实证
    过度自信者高估成长、低估风险 ⇒ 后续跑输。

组合逻辑：两者唯一的共同点是"资产负债表没讲完的故事"（表外义务 + 表外稀释），
其余（租赁=租赁会计口径、激励=薪酬会计口径）机制完全独立 ⇒ 叠加应降corr。

用法：python src/mine/mine_w302_combo.py
输出：src/mine/w302_batches.json
"""
import os as _os, io, json, itertools
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

GR = lambda x, g='subindustry': f'group_rank({x}, {g})'

# 两个强原子腿（去掉自带的小引擎腿，重组时统一配）
# LEG 存**裸表达式**，group_rank 在组合时按分组轴现套
LEG = {
    # 租赁强度（表外杠杆）
    'lease_cur':  'current_minimum_operating_lease_payment/assets',
    'lease_fut':  'future_minimum_operating_lease_payments/assets',
    'lease_rent': 'net_operating_lease_rent_expense/assets',
    # 股权激励（表外稀释 + 过度自信）
    'sbp_nonvst': 'sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a',
    'opt_outstd': 'option_award_outstanding_count/fn_entity_common_stock_shares_out_a',
    'opt_grant':  'option_awards_granted_count/assets',
    'sbp_alloc':  'allocated_sbp_expense_total/assets',
}
RENT = {'lease_cur', 'lease_fut', 'lease_rent'}
SBP = {'sbp_nonvst', 'opt_outstd', 'opt_grant', 'sbp_alloc'}

# 配腿（弱引擎，只保 SF，权重压到 0.35~0.6 以控 corr）
ENG = {
    'e_cfo': 'ts_av_diff(cashflow_op/enterprise_value, 45)',
    'e_vol': 'volume/ts_mean(volume, 90)',
    'e_rev': 'ts_mean(abs(returns)/volume, 20)',
}

GRP_SET = {'subindustry', 'industry', 'market', 'sector'}
MAIN_W = (1.2, 1.5, 2.0)
SEC_W = (0.6, 0.8, 1.0)
ENG_W = (0.35, 0.5)
# 只在 TOP3000 主池跑；decay 由模拟器固定 10（与w301 探针同口径，便于横向比）

def build():
    out, seen = [], set()
    # 跨维组合：租赁腿 + 激励腿（必然跨维，保证机制正交）
    for a in sorted(RENT):
        for b in sorted(SBP):
            for g in GRP_SET:
                for gw in MAIN_W:
                    for sw in SEC_W:
                        for eng in ENG:
                            for ew in ENG_W:
                                cid = 'w302_%s_%s_%s_%s_%s_%s' % (a, b, g, gw, sw, eng)
                                if cid in seen:
                                    continue
                                seen.add(cid)
                                code = ('%s*%s + %s*%s + %s*%s'
                                        % (gw, GR(LEG[a], g), sw, GR(LEG[b], g),
                                           ew, GR(ENG[eng], g)))
                                out.append(dict(cid=cid, code=code, a=a, b=b,
                                                grp=g, gw=gw, sw=sw, eng=eng, ew=ew))
    # 同族单维加深（只跑最强的 lease_cur / sbp_nonvst 各配弱引擎，用于确认单维上限）
    for solo in ['lease_cur', 'sbp_nonvst']:
        for g in ('subindustry', 'industry'):
            for gw in (1.5, 2.0, 2.5):
                for eng in ENG:
                    for ew in ENG_W:
                        cid = 'w302solo_%s_%s_%s_%s' % (solo, g, gw, eng)
                        if cid in seen:
                            continue
                        seen.add(cid)
                        code = '%s*%s + %s*%s' % (gw, GR(LEG[solo], g), ew, GR(ENG[eng], g))
                        out.append(dict(cid=cid, code=code, a=solo, b=None,
                                        grp=g, gw=gw, sw=0, eng=eng, ew=ew))
    return out

if __name__ == '__main__':
    out = build()
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w302_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条→ %s' % (len(out), p))
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    for x in out[:3]:
        print(' ', x['cid'])
        print('   ', x['code'])