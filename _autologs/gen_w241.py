# -*- coding: utf-8 -*-
"""gen_w241.py —— 官方评分杠杆批（universe 降池 + truncation 收紧）

依据（平台官方评分文档 07_scoring-algorithm-challenge-users.md）：
  Quality 子因子 = Universe(小池加分) / SelfCorrelation(越低越好) / Fitness(越高越好) / Delay(D1>D0)
我们 97.9% 的产出都是 TOP3000（最大池→该项最低分），truncation 98.8% 是 0.08。
本批把这两个"从没当得分项测过"的轴，叠在高 Fitness、离墙最近的骨架上。

目标（均为 TOP3000/trunc0.08 基线，corr 离 0.685 直通线最近）：
  w162_06         SF5.81  corr=0.7678
  w162_06__g_ind  SF5.59  corr=0.7564
  w162_06__g_sec  SF5.47  corr=0.7593
  w164_04         SF5.86  corr=0.7698
  w164_04 家族另加 fnd6_pstkl 换 fnd6_txtubadjust 的双锚版本

变体：universe ∈ {TOP1000, TOP500} × truncation ∈ {0.08, 0.04}
"""
import io, json

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined'

TARGETS = {
    'w162_06': '1.5*group_rank(fnd6_pstkl/cap, subindustry) + group_rank(fn_accrued_liab_curr_a/assets, subindustry) + group_rank(fnd6_xrent/assets, subindustry) + 0.75*group_rank(-ts_delta(close, 5), subindustry) + 0.75*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry) + 0.75*group_rank(-ts_rank(returns, 5), subindustry)',
    'w162_06__g_ind': '1.5*group_rank(fnd6_pstkl/cap, industry) + group_rank(fn_accrued_liab_curr_a/assets, industry) + group_rank(fnd6_xrent/assets, industry) + 0.75*group_rank(-ts_delta(close, 5), industry) + 0.75*group_rank(-ts_mean(abs(returns)/volume, 20), industry) + 0.75*group_rank(-ts_rank(returns, 5), industry)',
    'w162_06__g_sec': '1.5*group_rank(fnd6_pstkl/cap, sector) + group_rank(fn_accrued_liab_curr_a/assets, sector) + group_rank(fnd6_xrent/assets, sector) + 0.75*group_rank(-ts_delta(close, 5), sector) + 0.75*group_rank(-ts_mean(abs(returns)/volume, 20), sector) + 0.75*group_rank(-ts_rank(returns, 5), sector)',
    'w164_04': '1.5*group_rank(fnd6_pstkl/cap, subindustry) + group_rank(fnd6_txtubadjust/cap, subindustry) + group_rank(fnd6_xrent/assets, subindustry) + 1.25*group_rank(-ts_delta(close, 5), subindustry) + 1.25*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry) + 1.25*group_rank(-ts_rank(returns, 5), subindustry)',
}

UNIV = ['TOP1000', 'TOP500']
TRUNC = [0.08, 0.04]

combos = {}
for base, expr in TARGETS.items():
    for u in UNIV:
        for t in TRUNC:
            cid = '%s__u%s_t%02d' % (base, u.replace('TOP', ''), int(t * 100))
            combos[cid] = {
                'expr': expr,
                'neutralization': 'SUBINDUSTRY',
                'decay': 10,
                'universe': u,
                'truncation': t,
                '_note': '官方得分杠杆：%s + trunc%s（基线 TOP3000/0.08）' % (u, t),
            }

io.open(ROOT + '_autologs/leg_combos_w241.json', 'w', encoding='utf-8').write(
    json.dumps(combos, ensure_ascii=False, indent=1))
print('w241 combos = %d（%d 目标 × %d 池 × %d trunc）' % (len(combos), len(TARGETS), len(UNIV), len(TRUNC)))
