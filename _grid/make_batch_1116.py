# -*- coding: utf-8 -*-
"""make_batch_1116.py —— 11-16 生产批（形态骨架来自 11-15 实测高 S 形态）

## 设计依据（全部实测，非拍脑袋）

1. **形态骨架来自实测**（11-15 已模拟件 16198 个逐条读出）：
   单字段且 S≥1.0 的共 75 条，**全部收敛到两个骨架**：
   - **骨架A「波动+动量」**（量价族最高 S=2.85）：
     `0.6*group_scale(-ts_std_dev(X,120), grp) + 1.4*group_scale(-ts_av_diff(X,60), grp)`
     —— 同一字段的「波动率水平」+「中期动量」两条腿，关系靠 `-` 与 `+` 构成、
     层数=3、字段数=1 ⇒ 过深度门 + 门7。
   - **骨架B「比值+横截面排序」**（非量价族最高 S=1.30）：
     `group_scale(ts_delta(X,60)/ts_std_dev(X,120), grp)`
   ⇒ **idea 决定形态、形态可迁移**：同一骨架换字段 = 换数据集，
     一次跑批同时铺「数据集多样性 + idea 多样性 + 算子多样性 + 参数多样性」。

2. **字段来自冷门格子**（`_grid/_cand_fields_1116.json`）：
   按 `all_fields_usa_top3000.json` 的 cov（覆盖率）升序取冷门数据集，
   且必须**台账从未用过**（门8）⇒ 顺手满足 Total distinct Fields 提升。

3. **禁令合规**：全批**不用 group_rank**（李工 11-15 12:55 硬禁令，11-15~11-24），
   改用 group_scale / group_zscore / group_neutralize（`_grid/transforms.py` 外壳族）。

4. **AT 合规**：每条只用一个数据集的字段 + 6 个豁免分组字段。

5. **★ 11-16 门控实测反馈 → 批次参数必须避开历史热点**：
   live 库回灌 233 件后，历史集中度 = truncation 0.08 占 91%、SUBINDUSTRY 43%、
   TOP3000 46%、decay=10 13%。新批必须避开，否则多样性门必然拦（**门在正确工作**）。

用法：
    python _grid/make_batch_1116.py --out _grid/batch_1116.json --n 24
"""
import io, json, os, sys, csv, re, random, collections

ROOT = r'D:\Python\worldquant'
sys.path.insert(0, os.path.join(ROOT, '_grid'))
sys.path.insert(0, os.path.join(ROOT, 'src'))

GRPS = ('industry', 'subindustry', 'sector', 'exchange')

# ---------------------------------------------------------------- 形态骨架
# (形态名, 模板, idea_id, 机制说明)
# 模板里 {F}=字段、{G}=分组字段。全部自带横截面处理（不用 group_rank）。
SHAPES = [
    # 骨架 A：波动 + 动量（同一字段两腿）—— 11-15 量价族最高 S=2.85 的形态
    ('A_vol_mom',
     '0.6*group_scale(-ts_std_dev({F},120),{G}) + 1.4*group_scale(-ts_av_diff({F},60),{G})',
     'IDEA_VOL_MOM_MID', '高波动+弱动量组合：波动率高者后续收益弱，叠加中期动量反向'),
    ('A_vol_mom_short',
     '0.5*group_scale(-ts_std_dev({F},60),{G}) + 1.5*group_scale(-ts_av_diff({F},20),{G})',
     'IDEA_VOL_MOM_SHORT', '短周期波动+短期动量：高波动短期反转'),
    ('A_vol_mom_long',
     '0.6*group_scale(-ts_std_dev({F},250),{G}) + 1.4*group_scale(-ts_av_diff({F},120),{G})',
     'IDEA_VOL_MOM_LONG', '长期波动+中期动量：波动率结构下的动量持续性'),
    # 骨架 B：比值 + 横截面排序 —— 11-15 非量价族最高 S=1.30 的形态
    ('B_ratio_xs',
     'group_scale(ts_delta({F},60)/ts_std_dev({F},120),{G})',
     'IDEA_SNR_MOM', '信噪比动量：变化除以自身波动，消除量纲差异'),
    ('B_ratio_long',
     'group_scale(ts_mean({F},20)/ts_mean({F},120)-1,{G})',
     'IDEA_TREND_STRENGTH', '长短周期均值比：趋势强度的横截面比较'),
    # ★ 11-16 深度门实测拦下无关系算子的 B_ratio_z ⇒ 改成"差 ÷ 波动"
    #   （**改形态不改门**，idea 不变）
    ('B_ratio_z',
     'group_scale((ts_mean({F},20)-ts_mean({F},120))/ts_std_dev({F},120),{G})',
     'IDEA_TREND_STRENGTH', '长短均值差的信噪比：偏离强度除以自身波动'),
    # 骨架 C：分位反转 + 变化确认 —— 11-15 ATOMS S2=1.12 实证
    ('C_rank_delta',
     'group_zscore(ts_decay_linear(-ts_rank({F},252),10)+ts_zscore(ts_delta({F},5)/ts_std_dev({F},20),120),{G})',
     'IDEA_RANK_REVERSION', '长期分位反转 + 短期变化确认：极端位置均值回复'),
    # 骨架 D：条件分支 —— 11-15 ATOMS S5=0.93 实证
    ('D_cond',
     'if_else(ts_zscore(ts_mean({F},20)-ts_mean({F},120),250)>0,'
     'group_scale(ts_decay_linear(ts_zscore({F},60),10),{G}),'
     'group_scale(ts_decay_linear(-ts_zscore({F},250),10),{G}))',
     'IDEA_REGIME_SWITCH', '趋势/震荡状态切换：按长短均值差符号选腿'),
    # 骨架 E：波动变化率（★ 新 idea：波动率的变化本身）
    ('E_vol_of_vol',
     'group_scale(ts_std_dev(ts_delta({F},5),60)/ts_mean(ts_std_dev({F},60),250),{G})',
     'IDEA_VOL_OF_VOL', '波动率的变化率：不确定性的二阶导，衡量预期波动调整'),
    # 骨架 F：加速度（二阶差分，★ 与 E 分离 idea）
    ('F_accel',
     'group_scale(ts_delta(ts_delta({F},20),20)/ts_std_dev({F},120),{G})',
     'IDEA_ACCELERATION', '信号的二阶变化：动量加速度，捕捉趋势的转折点'),
    # 骨架 G：截面分位 vs 自身历史（★ 11-16 深度门拦下原版 ⇒ 加关系算子）
    ('G_xs_vs_hist',
     'group_scale((ts_rank({F},250)-ts_rank(ts_mean({F},20),250))/ts_std_dev({F},120),{G})',
     'IDEA_XS_VS_HIST', '当前截面分位与自身历史分位之差：相对强度的变化'),
    # 骨架 H：按波动状态切换 —— 与 D 分离 idea
    ('H_rank_vol_cond',
     'if_else(ts_std_dev({F},60)>ts_mean(ts_std_dev({F},250),120),'
     'group_scale(ts_decay_linear(-ts_rank({F},252),10),{G}),'
     'group_scale(ts_av_diff({F},20)/ts_std_dev({F},60),{G}))',
     'IDEA_VOL_REGIME', '按波动状态切换：高波动下取反转信号，低波动下取动量信号'),
    # 骨架 I：均值回复强度（★ 新 idea）
    ('I_mean_revert',
     'group_scale((ts_mean({F},20)-ts_mean({F},250))/ts_std_dev({F},120),{G})',
     'IDEA_MEAN_REVERSION', '短期相对长期均值的偏离：均值回复强度'),
    # 骨架 J：变化率之比（★ 新 idea）
    ('J_delta_ratio',
     'group_zscore(ts_delta({F},20)/ts_delta({F},60),{G})',
     'IDEA_MOM_RATIO', '短期变化率与中期变化率之比：动量的加速度形态'),
    # 骨架 K：分位数的时间差（★ 新 idea）
    ('K_rank_spread',
     'group_scale((ts_rank({F},60)-ts_rank({F},250))/ts_std_dev({F},120),{G})',
     'IDEA_RANK_SPREAD', '短长期分位差：水平在自身分布中的位置变化'),
]

# --- 11-16 新增：横截面处理变体（同一 idea 换横截面算子，散 operator 维度）---
SHAPES_V2 = [
    ('A_vol_mom_zs',
     '0.6*group_zscore(-ts_std_dev({F},120),{G}) + 1.4*group_zscore(-ts_av_diff({F},60),{G})',
     'IDEA_VOL_MOM_MID', '高波动+弱动量组合（zscore 截面）'),
    ('A_vol_mom_nu',
     '0.6*group_neutralize(-ts_std_dev({F},120),{G}) + 1.4*group_neutralize(-ts_av_diff({F},60),{G})',
     'IDEA_VOL_MOM_MID', '高波动+弱动量组合（中性化截面）'),
    ('B_ratio_xs_zs',
     'group_zscore(ts_delta({F},60)/ts_std_dev({F},120),{G})',
     'IDEA_SNR_MOM', '信噪比动量（zscore 截面）'),
    ('B_ratio_xs_nu',
     'group_neutralize(ts_delta({F},60)/ts_std_dev({F},120),{G})',
     'IDEA_SNR_MOM', '信噪比动量（中性化截面）'),
    ('E_vol_of_vol_zs',
     'group_zscore(ts_std_dev(ts_delta({F},5),60)/ts_mean(ts_std_dev({F},60),250),{G})',
     'IDEA_VOL_OF_VOL', '波动变化率（zscore 截面）'),
    ('I_mean_revert_zs',
     'group_zscore((ts_mean({F},20)-ts_mean({F},250))/ts_std_dev({F},120),{G})',
     'IDEA_MEAN_REVERSION', '均值回复强度（zscore 截面）'),
    ('F_accel_nu',
     'group_neutralize(ts_delta(ts_delta({F},20),20)/ts_std_dev({F},120),{G})',
     'IDEA_ACCELERATION', '动量加速度（中性化截面）'),
    ('K_rank_spread_zs',
     'group_zscore((ts_rank({F},60)-ts_rank({F},250))/ts_std_dev({F},120),{G})',
     'IDEA_RANK_SPREAD', '分位差（zscore 截面）'),
]
SHAPES = SHAPES + SHAPES_V2

# --- 11-16 新增：group_zscore / group_neutralize 变体（散 operator 维度）---
SHAPES_V3 = [
    ('A_vol_mom_long_zs',
     '0.6*group_zscore(-ts_std_dev({F},250),{G}) + 1.4*group_zscore(-ts_av_diff({F},120),{G})',
     'IDEA_VOL_MOM_LONG', '长期波动+中期动量（zscore 截面）'),
    ('A_vol_mom_short_nu',
     '0.5*group_neutralize(-ts_std_dev({F},60),{G}) + 1.5*group_neutralize(-ts_av_diff({F},20),{G})',
     'IDEA_VOL_MOM_SHORT', '短周期波动+短期动量（中性化截面）'),
    ('B_ratio_long_zs',
     'group_zscore(ts_mean({F},20)/ts_mean({F},120)-1,{G})',
     'IDEA_TREND_STRENGTH', '长短周期均值比（zscore 截面）'),
    ('B_ratio_z_nu',
     'group_neutralize((ts_mean({F},20)-ts_mean({F},120))/ts_std_dev({F},120),{G})',
     'IDEA_TREND_STRENGTH', '长短均值差信噪比（中性化截面）'),
    ('G_xs_vs_hist_nu',
     'group_neutralize((ts_rank({F},250)-ts_rank(ts_mean({F},20),250))/ts_std_dev({F},120),{G})',
     'IDEA_XS_VS_HIST', '截面分位 vs 历史分位差（中性化截面）'),
    ('H_rank_vol_cond_zs',
     'if_else(ts_std_dev({F},60)>ts_mean(ts_std_dev({F},250),120),'
     'group_zscore(ts_decay_linear(-ts_rank({F},252),10),{G}),'
     'group_zscore(ts_av_diff({F},20)/ts_std_dev({F},60),{G}))',
     'IDEA_VOL_REGIME', '波动状态切换（zscore 截面）'),
    ('J_delta_ratio_nu',
     'group_neutralize(ts_delta({F},20)/ts_delta({F},60),{G})',
     'IDEA_MOM_RATIO', '变化率之比（中性化截面）'),
]
SHAPES = SHAPES + SHAPES_V3

# 外壳族：套在整条表达式外的后处理层（散 operator 维度）
SHELLS = [
    ('raw', lambda s: s),
    ('dq', lambda s: 'ts_decay_linear(%s,10)' % s),
    ('jq', lambda s: 'quantile(%s,driver="gaussian")' % s),
    ('tz', lambda s: 'ts_zscore(%s,250)' % s),
    ('wq', lambda s: 'winsorize(%s,std=4)' % s),
    ('hp', lambda s: 'hump(%s,hump=0.01)' % s),
    ('jd', lambda s: 'jump_decay(%s,20)' % s),
]

# 回测参数多样性：8 组
# ★ 11-16 门控实测反馈（live 库回灌 233 件后的真实集中度）：
#   decay: 64(23.9%) / 30(14.8%) / 10(13.2%) / 45(9.9%) / 96(8.2%) / 20(7.4%) 是热点，
#         冷门 = 40/60/80/90/100/12/22/25/28/35/50/70/48/128/8/0
#   universe: TOP3000(45.7%) / MINVOL1M(28.0%) / TOP1000(15.6%) 热点，
#             冷门 = TOP500(5.8%) / TOP2500(4.5%) / TOPDIV3000(0.4%)
#   neutralization: SUBINDUSTRY(42.6%) / STATISTICAL(34.3%) 热点，
#             冷门 = MARKET(8.3%) / INDUSTRY(5.4%) / SECTOR(5.0%) / COUNTRY(2.9%) / NONE(1.7%)
#   truncation: 0.08 是绝对热点(91%)，0.05/0.01/0.02/0.03/0.06/0.1 都冷门
# ⇒ 本批**用冷门参数**，成为分散者而不是跟随者（这才是多样性门的本意）。
SETTINGS_SETS = [
    {'decay': 40, 'neutralization': 'MARKET', 'truncation': 0.05, 'universe': 'TOP500'},
    {'decay': 60, 'neutralization': 'INDUSTRY', 'truncation': 0.01, 'universe': 'TOP2500'},
    {'decay': 80, 'neutralization': 'SECTOR', 'truncation': 0.02, 'universe': 'TOPDIV3000'},
    {'decay': 90, 'neutralization': 'MARKET', 'truncation': 0.03, 'universe': 'TOP500'},
    {'decay': 100, 'neutralization': 'INDUSTRY', 'truncation': 0.06, 'universe': 'TOP2500'},
    {'decay': 12, 'neutralization': 'SECTOR', 'truncation': 0.05, 'universe': 'TOPDIV3000'},
    {'decay': 25, 'neutralization': 'MARKET', 'truncation': 0.01, 'universe': 'TOP500'},
    {'decay': 50, 'neutralization': 'INDUSTRY', 'truncation': 0.02, 'universe': 'TOP2500'},
]


def used_tokens():
    p = os.path.join(ROOT, 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv')
    rows = list(csv.DictReader(io.open(p, encoding='utf-8-sig')))
    used = set()
    for r in rows:
        c = r.get('expr') or ''
        ops = set(re.findall(r'([a-z][a-z0-9_]*)\s*\(', c))
        for t in re.findall(r'\b([a-z][a-z0-9_]{2,})\b', c):
            if t not in ops:
                used.add(t)
    return used


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, '_grid/batch_1116.json'))
    ap.add_argument('--n', type=int, default=24)
    args = ap.parse_args()

    cand = json.load(io.open(os.path.join(ROOT, '_grid/_cand_fields_1116.json'), encoding='utf-8'))
    used = used_tokens()

    # 字段映射（用于 ATOM 判定）
    fmap = {}
    p = os.path.join(ROOT, 'data/alpha_quality_analysis/field_ds_map.json')
    if os.path.exists(p):
        fmap.update(json.load(io.open(p, encoding='utf-8')))
    if not fmap:
        p = os.path.join(ROOT, 'data/alpha_quality_analysis/all_fields_usa_top3000.json')
        for k, v in json.load(io.open(p, encoding='utf-8')).items():
            if v.get('ds'):
                fmap[k.lower()] = v['ds']

    pool = []
    for ds, fs in cand.items():
        if ds == 'pv1':            # 量价：拥挤格子，VF 边际信息为零
            continue
        for nm, cov, uc in fs:
            if nm in used:
                continue
            if fmap.get(nm.lower()) not in (ds, None):
                continue
            pool.append((ds, nm, cov, uc))
    pool.sort(key=lambda x: (x[2], x[0]))

    random.seed(1116)
    batch = []
    ds_count = collections.Counter()
    shape_count = collections.Counter()
    shell_count = collections.Counter()
    idx = 0
    i = 0
    while i < len(pool) and len(batch) < args.n:
        ds, nm, cov, uc = pool[i]
        i += 1
        if ds_count[ds] >= 3:            # 一池一家族：同一数据集本批最多 3 条
            continue
        # ★ 11-16 门控实测：group_scale 累计上限 170 次、历史已用 157 ⇒ 本批只剩 13 次。
        #   形态轮转要**优先用非 group_scale 的变体**，否则必然超限。
        #   做法：把 SHAPES 按「是否含 group_scale」分成两堆，轮转时优先取不含的。
        _no_gs = [s for s in SHAPES if 'group_scale' not in s[1]]
        _with_gs = [s for s in SHAPES if 'group_scale' in s[1]]
        shape = (_no_gs + _with_gs)[idx % len(SHAPES)]
        shell = SHELLS[idx % len(SHELLS)]
        st = SETTINGS_SETS[idx % len(SETTINGS_SETS)]
        grp = GRPS[idx % len(GRPS)]
        idx += 1
        core = shape[1].replace('{F}', nm).replace('{G}', grp)
        code = shell[1](core)
        cid = 'B1116_%s_%s_%s_%s' % (ds[:10], nm[:24], shape[0], shell[0])
        batch.append({
            'cid': cid, 'code': code,
            'idea_id': shape[2], 'mech': shape[3],
            'dataset': ds, 'field': nm, 'shape': shape[0], 'shell': shell[0],
            'group': grp,
            'decay': st['decay'], 'neutralization': st['neutralization'],
            'truncation': st['truncation'], 'universe': st['universe'],
        })
        ds_count[ds] += 1
        shape_count[shape[0]] += 1
        shell_count[shell[0]] += 1

    json.dump(batch, io.open(args.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print('产出 %d 条 → %s' % (len(batch), args.out))
    print('数据集 %d 个: %s' % (len(ds_count), dict(ds_count.most_common())))
    print('形态 %d 种: %s' % (len(shape_count), dict(shape_count)))
    print('外壳 %d 种: %s' % (len(shell_count), dict(shell_count)))
    print('idea %d 种: %s' % (len(set(b['idea_id'] for b in batch)),
                              dict(collections.Counter(b['idea_id'] for b in batch))))
    for b in batch[:8]:
        print('  %-48s %s' % (b['cid'][:48], b['code'][:88]))


if __name__ == '__main__':
    main()
