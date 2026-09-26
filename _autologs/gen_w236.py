# -*- coding: utf-8 -*-
"""gen_w236.py —— 中性化换挡批次（0920 实证杠杆）

依据：j2Az8n0E 同骨架 SUBINDUSTRY 平台 corr 0.7367 → 换 MARKET 后 A_MAR 平台 corr 0.6467
      = 换挡 −0.090。把卡在 0.685~0.82 的高质量候选（F≥2.0、TO≤20%）全部换挡重跑，
      目标把它们推过 0.685 直通线。

输出：_autologs/leg_combos_w236.json（喂 mine_batch181.py）
"""
import re, io, json, os

LOG = '_autologs/_dry3_latest.txt'
OUT = '_autologs/leg_combos_w236.json'
MINED = 'data/alpha_quality_analysis/mined'

LO_BAND, HI_BAND = 0.685, 0.82
NEUTS = ['MARKET', 'SECTOR', 'INDUSTRY']       # 与 SUBINDUSTRY 并列的换挡目标

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
        targets.append((m.group(2), c, float(m.group(3))))   # cid, corr, SF

combos = {}
skipped_dup = 0
# ★ 按"离直通线 0.685 最近"排序生成 —— 最可能破线的先跑（平台并发受限时先出信号）
targets.sort(key=lambda t: t[1])
for cid, corr, sf in targets:
    p = f'{MINED}/{cid}.json'
    if not os.path.exists(p):
        continue
    d = json.load(io.open(p, encoding='utf-8'))
    code = ((d.get('regular') or {}).get('code') or '').strip()
    if not code:
        continue
    orig_neut = ((d.get('settings') or {}).get('neutralization')
                 or d.get('_neut') or 'SUBINDUSTRY')
    decay = d.get('_decay') or ((d.get('settings') or {}).get('decay')) or 10
    trunc = d.get('_trunc') or ((d.get('settings') or {}).get('truncation')) or 0.08
    for n in NEUTS:
        if n == orig_neut:
            continue
        ncid = f'{cid}__{n[:3]}'
        if os.path.exists(f'{MINED}/{ncid}.json'):
            skipped_dup += 1
            continue
        combos[ncid] = {
            'expr': code,
            'neutralization': n,
            'decay': decay, 'truncation': trunc,
            '_note': f'换挡 {orig_neut}->{n}，原corr={corr:.4f}',
        }

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
io.open('_autologs/_gen_w236.txt', 'w', encoding='utf-8').write(
    'band=[%.3f,%.3f) 目标 %d 条 → 换挡组合 %d 条（已存在跳过 %d）\n%s'
    % (LO_BAND, HI_BAND, len(targets), len(combos), skipped_dup,
       '\n'.join('  %-28s corr=%.4f SF=%.2f' % (c, v, s) for c, v, s in sorted(targets, key=lambda t: t[1])[:40])))
print('combos', len(combos))
