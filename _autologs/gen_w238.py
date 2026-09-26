# -*- coding: utf-8 -*-
"""gen_w238.py —— bucket 换分组的快速验证批（小批、近线优先）

假设：今天入池的 9qjZ8oZ2（成交额桶）与 O0N5o3Nv（波动率桶）都用 bucket 分组命中，
      而所有卡死候选清一色 subindustry 分组 → bucket 分组才是真去相关杠杆。
做法：取离直通线最近的 N 条，只做"波动率桶 / 成交额桶"两种换分组，快速拿信号。
"""
import re, io, json, os

LOG = '_autologs/_dry3_latest.txt'
OUT = '_autologs/leg_combos_w238.json'
MINED = 'data/alpha_quality_analysis/mined'
N = 8
BUCKETS = {
    'bvol': 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")',
    'bdv':  'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")',
}

pat = re.compile(r'^\s*[✗★✓]\s+(\S+)\s+(\S+)\s+SF=([\d.]+)')
rows = []
for ln in io.open(LOG, encoding='utf-8').read().splitlines():
    m = pat.match(ln)
    if not m:
        continue
    mc = re.search(r'corr_max=([\d.]+)', ln)
    if not mc:
        continue
    c = float(mc.group(1))
    if 0.685 <= c < 0.82:
        rows.append((c, m.group(2)))
rows.sort()                                      # 离 0.685 最近优先
rows = [(c, cid) for c, cid in rows if os.path.exists(f'{MINED}/{cid}.json')][:N]

combos = {}
info = []
for c, cid in rows:
    d = json.load(io.open(f'{MINED}/{cid}.json', encoding='utf-8'))
    reg = d.get('regular') or {}
    code = (reg.get('code') or '').strip()
    if not code or 'subindustry' not in code:
        continue
    opc = reg.get('operatorCount') or 0
    added = 0
    for tag, g in BUCKETS.items():
        expr = code.replace(', subindustry)', f', {g})')
        if expr == code:
            continue
        est = opc + 3 * code.count(', subindustry)')
        if est > 64:                             # 预估算子上限
            info.append('  %-24s opc=%d 预估换桶后 %d > 64 跳过' % (cid, opc, est))
            continue
        ncid = f'{cid}__{tag}'
        if os.path.exists(f'{MINED}/{ncid}.json'):
            continue
        combos[ncid] = {'expr': expr,
                        'neutralization': ((d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'),
                        'decay': ((d.get('settings') or {}).get('decay')) or 10,
                        'truncation': ((d.get('settings') or {}).get('truncation')) or 0.08,
                        '_note': '近线换桶 %s（原corr %.4f, opc %d）' % (tag, c, opc)}
        added += 1
    info.append('  %-24s corr=%.4f opc=%d → 新增 %d 条' % (cid, c, opc, added))

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
io.open('_autologs/_gen_w238.txt', 'w', encoding='utf-8').write(
    '近线 %d 条 → 组合 %d 条\n%s' % (len(rows), len(combos), '\n'.join(info)))
print('combos', len(combos))
