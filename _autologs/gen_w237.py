# -*- coding: utf-8 -*-
"""gen_w237.py —— 换分组批次（杠杆②：改 group，不只改中性化）

依据：候选池 97% 共享 `assets/close` 基准，而 `group_rank(x, subindustry)` 是共享结构
      的直接来源（同一分组内的排序结构一致 → PnL 高度相似）。
      把腿内分组换成 sector / industry（零算子成本）或 bucket(rank(<慢变量>))（+3 算子/腿），
      同时拉开"比什么"和"跟谁比"，是比换锚强得多的去相关杠杆。

范围：submit_exempt 干跑里 corr_max ∈ [0.685, 0.82) 的 66 条（F≥2.0、TO≤20%）。
算子上限：平台 64；bucket 版只对 operatorCount ≤ 40 的表达式生成，避免超限。
"""
import re, io, json, os

LOG = '_autologs/_dry3_latest.txt'
OUT = '_autologs/leg_combos_w237.json'
MINED = 'data/alpha_quality_analysis/mined'

LO_BAND, HI_BAND = 0.685, 0.82
SIMPLE_GROUPS = ['sector', 'industry']          # 零算子成本
BUCKET_VOL = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'
BUCKET_DV = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
OP_CAP = 40                                     # 留出 bucket 替换的余量

pat = re.compile(r'^\s*[✗★✓]\s+(\S+)\s+(\S+)\s+SF=([\d.]+)')
targets = []
for ln in io.open(LOG, encoding='utf-8').read().splitlines():
    m = pat.match(ln)
    if not m:
        continue
    mc = re.search(r'corr_max=([\d.]+)', ln)
    if not mc:
        continue
    c = float(mc.group(1))
    if LO_BAND <= c < HI_BAND:
        targets.append(m.group(2))

combos = {}
skipped = 0
for cid in targets:
    p = f'{MINED}/{cid}.json'
    if not os.path.exists(p):
        continue
    d = json.load(io.open(p, encoding='utf-8'))
    code = ((d.get('regular') or {}).get('code') or '').strip()
    opc = ((d.get('regular') or {}).get('operatorCount') or 0)
    if not code or 'subindustry' not in code:
        continue
    neut = ((d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY')
    decay = ((d.get('settings') or {}).get('decay')) or 10
    trunc = ((d.get('settings') or {}).get('truncation')) or 0.08

    variants = {}
    for g in SIMPLE_GROUPS:
        variants[f'{cid}__g_{g[:3]}'] = (code.replace(', subindustry)', f', {g})'), f'换分组->{g}')
    if opc and opc <= OP_CAP:
        variants[f'{cid}__g_bvol'] = (code.replace(', subindustry)', f', {BUCKET_VOL})'), '换分组->波动率桶')
        variants[f'{cid}__g_bdv'] = (code.replace(', subindustry)', f', {BUCKET_DV})'), '换分组->成交额桶')

    for ncid, (expr, note) in variants.items():
        if expr == code or os.path.exists(f'{MINED}/{ncid}.json'):
            skipped += 1
            continue
        combos[ncid] = {'expr': expr, 'neutralization': neut,
                        'decay': decay, 'truncation': trunc, '_note': note}

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
io.open('_autologs/_gen_w237.txt', 'w', encoding='utf-8').write(
    '目标 %d 条 → 换分组组合 %d 条（跳过 %d）\n' % (len(targets), len(combos), skipped))
print('combos', len(combos))
