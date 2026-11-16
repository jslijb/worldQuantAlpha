# -*- coding: utf-8 -*-
"""w304 —— oci 提 SF（2026-10-10，基于 w303 实测的瓶颈定位）

w303 实测诊断（7 条，预测 corr 全部过线 0.55~0.65）：
  | cid | SF | S | F | TO | tS | 预测corr |
  |---|---|---|---|---|---|---|
  | omWJo23k | 3.28 | 1.96 | 1.32 | 0.014 | 1.25 | 0.5558 |
  | akxQVZ3x | 3.33 | 1.97 | 1.36 | 0.014 | 1.19 | 0.5749 |
  | 0mrNjQo1 | 3.41 | 1.98 | 1.43 | 0.015 | 1.28 | 0.6024 |
  | 9qWdEgv2 | 3.49 | 1.98 | 1.51 | 0.015 | 0.88 | 0.6504 |

**瓶颈定位（本批的设计依据）**：
  S 已到 1.96~1.99（离平台线 2.0 只差 0.01~0.04），
  F 只有 1.32~1.51，缺口 0.7~0.9 全部在 F 上。
  由 F = S×√(|R|/max(TO,0.125))，本批 TO=1.4%~1.5% << 0.125 ⇒ 被夹到下限
  ⇒ **F = S×√(R/0.125)，与 TO 无关，只由 S 和 |R| 决定**。
  ⇒ 提 F 有两条路：**① 提 S**（主攻）**② 提 |R|（换手率）**。

本批对策（三条并行，按MEMORY 深挖优先于横扫）：
  A. **decay 收口**：TO 只 1.4% 意味着日持仓几乎不变，信号衰减极慢。
     decay 10→40/60/80 会压 TO，但 TO 已远低于甜点区，降 TO 反而**伤 F**（F∝√R）⇒
     这条只作为对照，实测确认方向。
  B. **信号锐化**：oci 是"资产占比"型连续变量，分组内取值密集。
     改用`ts_delta`（同比变化）而非静态占比，让信号有方向性 ⇒ 提 S。
     这是 M11 机制的自然延伸：OCI 的**变动**比其**水平**更含信息
     （养老金重估的大幅计提通常伴随股价反应）。
  C. **换分组轴提高组内分化**：market/sector 轴组内同质性低，
     排序区分度更高 ⇒ group_rank 输出更分散 ⇒ |R| 提升。

  D. **窗口共振**：oci 的 static 占比 + 不同窗长的变化量叠加，测是否共振。

用法：python src/mine/mine_w304_sf.py
输出：src/mine/w304_batches.json
"""
import os as _os, io, json, itertools
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

G = lambda x, g: f'group_rank({x}, {g})'

OCI = 'other_comprehensive_income_net_tax/assets'
OCI_RAW = 'other_comprehensive_income_net_tax'

# 配腿（w303 实测：lease_cur 权重越小 tS 越好，但 F 不足；这里换思路）
SEC = {
    'lease_cur': 'current_minimum_operating_lease_payment/assets',
    'lease_fut': 'future_minimum_operating_lease_payments/assets',
    'sbp_nonvst': 'sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a',
    'intang': '-annual_intangible_assets_net_carrying_value/assets',
    'accr': 'fn_accrued_liab_curr_a/assets',
    'e_vol': 'volume/ts_mean(volume, 90)',
    'e_cfo': 'ts_av_diff(cashflow_op/enterprise_value, 45)',
}

# 形态 A/B/D 的 oci 变体：static 占比 vs 变化量
OCI_FORMS = {
    'static': OCI,
    'd60': f'ts_delta({OCI_RAW}, 60)/assets',
    'd120': f'ts_delta({OCI_RAW}, 120)/assets',
    'd250': f'ts_delta({OCI_RAW}, 250)/assets',
    'yoy': f'(ts_delay({OCI_RAW}, 250) - ts_delay({OCI_RAW}, 500))/assets',
    'neg_static': '-' + OCI,
    'd60_neg': f'-ts_delta({OCI_RAW}, 60)/assets',
}
GRP = ['subindustry', 'industry', 'market', 'sector']
MAIN_W = [2.0, 3.0]
SUB_W = [0.3, 0.5, 0.75, 1.0]

def build():
    out, seen = [], set()
    # 形态 B（主攻）：oci 变体 × 分组轴 × 副腿
    for fname, f in OCI_FORMS.items():
        for g in GRP:
            for mw in MAIN_W:
                # B1：只 oci 单腿（看纯 oci 变体的SF 上限）
                cid = 'w304_%s_%s_%s_solo' % (fname, g, mw)
                if cid not in seen:
                    seen.add(cid)
                    out.append(dict(cid=cid, form=fname, sec='-', grp=g, mw=mw, sw=0,
                                    code='%s*%s' % (mw, G(f, g))))
                # B2：oci 变体 + 副腿
                for sname, s in SEC.items():
                    for sw in SUB_W:
                        cid = 'w304_%s_%s_%s_%s_%s' % (fname, g, mw, sname, sw)
                        if cid in seen:
                            continue
                        seen.add(cid)
                        out.append(dict(cid=cid, form=fname, sec=sname, grp=g, mw=mw, sw=sw,
                                        code='%s*%s + %s*%s' % (mw, G(f, g), sw, G(s, g))))
    # 形态 D：两个 oci 变体叠加（static + 变化量，测共振）
    for f1, f2 in [('static', 'd60'), ('static', 'd250'), ('d60', 'd120'),
                   ('static', 'neg_static'), ('d60', 'd60_neg')]:
        for g in ('subindustry', 'industry'):
            for mw in (2.0, 3.0):
                cid = 'w304x_%s_%s_%s_%s' % (f1, f2, g, mw)
                if cid in seen:
                    continue
                seen.add(cid)
                out.append(dict(cid=cid, form=f1 + '+' + f2, sec=f2, grp=g, mw=mw, sw=0.5,
                                code='%s*%s + 0.5*%s' % (mw, G(OCI_FORMS[f1], g), G(OCI_FORMS[f2], g))))
    return out

if __name__ == '__main__':
    out = build()
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w304_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条 → %s' % (len(out), p))
    print('oci 变体:', list(OCI_FORMS))
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    print()
    print('★ w303 已实测基线（SF 天花板 3.49，tS 最好 1.28，预测 corr 0.55~0.65）：')
    for c in ['3.0*group_rank(other_comprehensive_income_net_tax/assets, subindustry) + 0.3*group_rank(current_minimum_operating_lease_payment/assets, subindustry)']:
        print('  ', c)
    print()
    for x in out[:4]:
        print(' ', x['cid'])
        print('   ', x['code'])