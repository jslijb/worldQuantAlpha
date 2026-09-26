# -*- coding: utf-8 -*-
"""gen_w243.py —— x162_w164_00_MAR 的 decay 阶梯补测

背景：低靶区清单里缺口最小的三条，两条已靠 decay 顶 S 过线入池
  · x162_w164_04_MAR  d10→d6  S2.45→2.55  平台 corr 0.8042 ACCEPTED
  · w189_01__g_bdv    d10→d6  S2.45→2.58  平台 corr 0.7725 ACCEPTED
剩下 x162_w164_00_MAR（need 2.54 / S2.47 / 缺口 +0.07），但 d4/d6 从未产出。
本批补齐 d4/d5/d6/d8 四个点（d1/d2/d20 已有：d1 S2.51/F0.94/TO98%、d2 S2.69/F1.30/TO65%、d20 S2.25/F2.28/TO10.6%/tS1.19）。
目标：找到 S ≥ 2.54 且 TO ≤ 20%、tS ≥ 1.25 的那个 decay 点。
"""
import io, json

ROOT = 'D:/Python/worldquant/'
EXPR = ('1.5*group_rank(fnd6_txtubadjust/cap, subindustry) '
        '+ group_rank(fnd6_newqv1300_dpactq/cap, subindustry) '
        '+ group_rank(fnd6_xrent/assets, subindustry) '
        '+ 1.5*group_rank(-ts_rank(returns, 20), subindustry) '
        '+ 1.5*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry) '
        '+ 1.5*group_rank(-ts_rank(returns, 5), subindustry)')

combos = {}
for d in (4, 5, 6, 8):
    combos['x162_w164_00_MAR__d%d' % d] = {
        'expr': EXPR,
        'neutralization': 'MARKET',
        'decay': d,
        'truncation': 0.08,
        '_note': '低靶区顶S补齐：need 2.54 / 基线 S2.47（缺口+0.07），decay 阶梯找 S≥2.54 且 TO≤20% 的拐点',
    }

io.open(ROOT + '_autologs/leg_combos_w243.json', 'w', encoding='utf-8').write(
    json.dumps(combos, ensure_ascii=False, indent=1))
print('w243 combos = %d' % len(combos))
