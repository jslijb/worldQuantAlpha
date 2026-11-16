# -*- coding: utf-8 -*-
"""w307 —— analyst4 管理层指引区间（1010 第二个降corr 战场）

═══ 为什么换战场（1010 12:0x）═══
f2 数据集已挖到底：w306 实测 75 条，19 个存量主腿里**只有 oci 能过 SF4.2**（两个变体 SF4.35
但与已入池的 kqgWNYw8 自撞 0.9984，今日封顶），其余 9 腿最高 3.70，差 0.5 以上。
⇒ 换信息维度（D-33 纠偏方向），不在 f2 里继续挖。

═══ 新战场：analyst4 的管理层指引区间 ═══
`anl4_fs_guidances_advanced_af_nd_*` 系列：
  · **cov = 1.000**（全池覆盖）
  · **userCount = 1**（atoms.md 已登记为"无人区"，全平台几乎没人用过）
  · 每个指标成对存在 `maxguidance` / `minguidance` = **管理层自己给的业绩上下限区间**
  · 共约 20 个指标（epsr/epsa/epsa/ebit/ebitda/cfo/cff/cfi/capex/bvps/fcf/fcfps/custom_eps）

经济机制（这是 idea.md §2 M05 的新变体E504~E507）：
  M05 原机制 = 分析师预测修正后的价格漂移（PEAD）
  **本机制 = 管理层指引区间本身的宽度与相对位置**，信息源从第三方分析师换成管理层自己，
  更新更即时、更少被套利：
  ① 区间宽（E504）= 管理层自己都没把握 ⇒ 不确定性高 ⇒ 预期分歧大 ⇒ 定价不足
  ② 指引下限低（E505）= 管理层预期偏保守 ⇒ 下调风险
  ③ 指引中值 vs 分析师预测的差（E506）= 双方分歧 ⇒ 分析师未跟随 ⇒ 未来下修
  ④ 无量纲倍数（E507）= 区间宽度的稳健版本

═══ 沿用 1010 实证有效的结构（不许改）═══
  存量腿 ×3.0~3.5 ＋ 流量腿（ts_av_diff(cashflow_op/EV,45)）×1.0~1.5
  → 1010 实测：同质叠加会稀释，存量+流量正交才有效（w303 全证）

用法：python src/mine/mine_w307_guid.py
输出：src/mine/w307_batches.json
"""
import os as _os, io, json, itertools
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

G = lambda x, g: f'group_rank({x}, {g})'
FLOW = 'ts_av_diff(cashflow_op/enterprise_value, 45)'   # 1010 唯一到 SF4.46 的流量腿

# guidance 系列全清单（cov=1.000 userCount=1）
GD = {
    'epsr':  'anl4_fs_guidances_advanced_af_nd_epsr',
    'epsa':  'anl4_fs_guidances_advanced_af_nd_epsa',
    'custom_eps': 'anl4_fs_guidances_advanced_af_nd_custom_eps',
    'ebit':  'anl4_fs_guidances_advanced_af_nd_ebit',
    'ebitda': 'anl4_fs_guidances_advanced_af_nd_ebitda',
    'cfo':   'anl4_fs_guidances_advanced_af_nd_cfo',
    'cff':   'anl4_fs_guidances_advanced_af_nd_cff',
    'cfi':   'anl4_fs_guidances_advanced_af_nd_cfi',
    'capex': 'anl4_fs_guidances_advanced_af_nd_capex',
    'bvps':  'anl4_fs_guidances_advanced_af_nd_bvps',
    'fcf':   'anl4_fs_guidances_advanced_af_nd_fcf',
    'fcfps': 'anl4_fs_guidances_advanced_af_nd_fcfps',
}

def legs(prefix):
    """四种指引信号形态：区间宽/ 指引下限 / 指引中值 / 无量纲倍数"""
    out = {}
    out[prefix + '_width'] = '(%s_maxguidance - %s_minguidance)/abs(%s_minguidance)' % (prefix, prefix, prefix)
    out[prefix + '_floor'] = '%s_minguidance/assets' % prefix
    out[prefix + '_mid']   = '(%s_maxguidance + %s_minguidance)/2/assets' % (prefix, prefix)
    out[prefix + '_ratio'] = '%s_maxguidance/(abs(%s_minguidance) + 1)' % (prefix, prefix)
    return out

GRP = ['subindustry', 'industry']
MAIN_W = [3.0, 3.5]
FLOW_W = [1.0, 1.5]

def build():
    out, seen = [], set()
    for name, pfx in GD.items():
        for lname, leg in legs(pfx).items():
            for g in GRP:
                for mw in MAIN_W:
                    for fw in FLOW_W:
                        cid = 'w307_%s_%s_%s_%s' % (lname, g, mw, fw)
                        if cid in seen:
                            continue
                        seen.add(cid)
                        out.append(dict(cid=cid, main=lname, grp=g, mw=mw, fw=fw,
                                        code='%s*%s + %s*%s' % (mw, G(leg, g), fw, G(FLOW, g))))
    # 形态：指引区间宽 + 指引下限双leg（同一指标的两个口径，测是否共振）
    for name in ['epsr', 'ebitda', 'cfo']:
        pfx = GD[name]
        w = '(%s_maxguidance - %s_minguidance)/abs(%s_minguidance)' % (pfx, pfx, pfx)
        f = '%s_minguidance/assets' % pfx
        for g in ('subindustry',):
            for mw in (3.0,):
                for fw in (1.0,  1.5):
                    cid = 'w307x_%s_wf_%s_%s' % (name, g, fw)
                    if cid in seen:
                        continue
                    seen.add(cid)
                    out.append(dict(cid=cid, main=name + '_width+floor', grp=g, mw=mw, fw=fw,
                                    code='3.0*%s + 0.5*%s + %s*%s'
                                         % (G(w, g), G(f, g), fw, G(FLOW, g))))
    return out

if __name__ == '__main__':
    out = build()
    for x in out:
        x['ops'] = x['code'].count('(') + x['code'].count('+')
    out.sort(key=lambda x: x['ops'])
    p = ROOT / 'src/mine/w307_batches.json'
    json.dump(out, io.open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('生成 %d 条 → %s' % (len(out), p))
    print('指引指标 %d 个 × 4 形态 × 2 轴 × 2 主腿权 × 2 流量权 = %d' % (len(GD), len(GD) * 4 * 2 * 2 * 2))
    print('算子数分布:', {k: sum(1 for x in out if x['ops'] == k) for k in sorted({x['ops'] for x in out})})
    print()
    print('★ 1010 已入池基准：kqgWNYw8 SF=4.46 corr=0.6081 (f2 oci ×3.0 + cfo ×1.5)')
    print('★ 换战场原因：w306 实测 75 条，f2 里只有 oci 能过 4.2，其余 9 腿最高 3.70')
    print('★ 本批守 1010 实证结构：存量腿(指引区间) × 3.0~3.5 + 流量腿(cfo) × 1.0~1.5')
    for x in out[:3]:
        print(' ', x['cid'])
        print('   ', x['code'])