# -*- coding: utf-8 -*-
"""w232 —— 优化历史高换手因子（李工 0920 指令：提夏普同时降换手）

问题诊断（平台实测）：
  历史提交里 TO>40% 的 14 条，margin 只有 5~8bp；TO<20% 的 65 条，margin 15~28bp。
  高换手族的共同设置是 INDUSTRY + decay=0 + truncation=0.01 + nanHandling=OFF，
  且腿数只有 2~3 条。这正是"只盯夏普"留下的账。

本批做两件事：
  A 组：6 条历史高换手因子 × 3 种改造，直接对照 TO/S/F 变化
  B 组：在 A 的改造版上扫 decay，量出「decay→turnover」定量曲线
"""
import json, io

OUT = '_autologs/leg_combos_w232.json'

# —— 6 条历史高换手因子（平台实测 TO / S / F）
BASE = {
    'kqjpepz8': ('group_rank(liabilities_curr/assets, industry) + group_rank(-ts_rank(close, 5), industry)',
                 0.6631, 2.74, 1.42),
    'N1QxNQK7': ('group_rank(liabilities_curr/cap, industry) + group_rank(-ts_rank(close, 5), industry)',
                 0.6575, 2.06, 1.17),
    '9qX3M2mq': ('group_rank(liabilities_curr/assets, industry) + group_rank(-ts_rank(close, 10), industry)',
                 0.5278, 2.49, 1.45),
    'qMW92Az2': ('group_rank(liabilities_curr/cap, industry) + group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry) + group_rank(-ts_rank(close, 10), industry)',
                 0.4640, 2.32, 1.60),
    '1YwRK1wW': ('group_rank(liabilities_curr/assets, industry) + group_rank(-ts_rank(close, 20), industry)',
                 0.4114, 2.11, 1.31),
    'e79kPeEM': ('group_rank(liabilities_curr/assets, industry) + group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry) + group_rank(-ts_rank(close, 5), industry)',
                 0.5700, 3.02, 1.79),
}

# —— 慢速腿池（来自平台实测高 F 样本，全部低换手）
SLOW_LEGS = [
    'group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)',
    'group_rank(volume/ts_mean(volume, 120), subindustry)',
    'group_rank(-ts_delta(close, 20), subindustry)',
]

combos = {}

for tag, (expr, to0, s0, f0) in BASE.items():
    # ① 只换设置：INDUSTRY→SUBINDUSTRY、decay 0→10、trunc 0.01→0.08、nan OFF→ON
    #    顺带把 ts_av_diff 窗口 60→45（文档实证：60 是死亡区，45 全过率 72.7%）
    e1 = expr.replace(', industry)', ', subindustry)').replace('enterprise_value, 60)', 'enterprise_value, 45)')
    combos[f'{tag}_v1'] = {'expr': e1, 'neutralization': 'SUBINDUSTRY', 'decay': 10,
                           'truncation': 0.08, '_note': f'原TO{to0:.0%}/S{s0}/F{f0} 仅换设置'}
    # ② 换设置 + 补 3 条慢速腿（腿数 2~3 → 5~6）
    e2 = e1 + ' + ' + ' + '.join(SLOW_LEGS)
    combos[f'{tag}_v2'] = {'expr': e2, 'neutralization': 'SUBINDUSTRY', 'decay': 10,
                           'truncation': 0.08, '_note': '换设置+补3慢腿'}
    # ③ 换设置 + 补 1 条慢速腿（保守版，避免 64 算子超限）
    e3 = e1 + ' + ' + SLOW_LEGS[0]
    combos[f'{tag}_v3'] = {'expr': e3, 'neutralization': 'SUBINDUSTRY', 'decay': 10,
                           'truncation': 0.08, '_note': '换设置+补1慢腿'}

# —— hump 降换手测试（hump 在本账号只收 1 参，先单独验）
combos['H_hump_kqjpepz8'] = {
    'expr': 'hump(' + BASE['kqjpepz8'][0].replace(', industry)', ', subindustry)') + ')',
    'neutralization': 'SUBINDUSTRY', 'decay': 10, 'truncation': 0.08, '_note': 'hump单参降换手测试'}
combos['H_hump_v2'] = {
    'expr': 'hump(' + BASE['e79kPeEM'][0].replace(', industry)', ', subindustry)') + ' + ' + SLOW_LEGS[0] + ')',
    'neutralization': 'SUBINDUSTRY', 'decay': 10, 'truncation': 0.08, '_note': 'hump+补腿'}

# —— B 组：decay 曲线（在两条代表基座的 v1 上扫）
SCAN_BASE = {
    'kqjpepz8': BASE['kqjpepz8'][0].replace(', industry)', ', subindustry)'),
    'e79kPeEM': BASE['e79kPeEM'][0].replace(', industry)', ', subindustry)').replace('enterprise_value, 60)', 'enterprise_value, 45)'),
}
for tag, e in SCAN_BASE.items():
    for d in (2, 4, 8, 15, 20):
        combos[f'D_{tag}_d{d}'] = {'expr': e, 'neutralization': 'SUBINDUSTRY', 'decay': d,
                                   'truncation': 0.08, '_note': f'decay扫描 d{d}'}

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('w232 combos:', len(combos))
for k in list(combos)[:4]:
    print(' ', k, '|', combos[k]['_note'])
