# -*- coding: utf-8 -*-
"""gen_w240.py —— 收窄高价值批（换分组换对手池 + 甜点区双保险）

合并两个靶群（都按"离成功最近的先跑"排序）：
  A. 离直通线最近的 12 条（corr_max 0.685~0.76）—— 靠换分组把 corr 压到 0.685 下
  B. 甜点区缺口最小的 12 条（豁免线缺口 ≤0.30）—— 换分组换对手池 + 顺带提 S

换分组：bucket(波动率桶) / bucket(成交额桶) / sector / industry
算子预算：平台上限 64，按 operatorCount + 3×腿数 预估，超限跳过。
硬上限 60 条，保证今晚能跑完。
"""
import re, io, json, os

LOG = '_autologs/_dry3_latest.txt'
SWEET = '_autologs/_sweetspot.txt'
OUT = '_autologs/leg_combos_w240.json'
MINED = 'data/alpha_quality_analysis/mined'
CAP = 60

GROUPS = {
    'bvol': 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")',
    'bdv':  'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")',
    'sec':  'sector',
    'ind':  'industry',
}


def load_targets():
    A, B = [], []
    if os.path.exists(LOG):
        for ln in io.open(LOG, encoding='utf-8').read().splitlines():
            m = re.match(r'^\s*[✗★✓]\s+(\S+)\s+(\S+)\s+SF=([\d.]+)', ln)
            mc = re.search(r'corr_max=([\d.]+)', ln)
            if m and mc:
                c = float(mc.group(1))
                if 0.685 <= c < 0.76:
                    A.append((c - 0.685, m.group(2)))       # 越接近直通线越小
    if os.path.exists(SWEET):
        for ln in io.open(SWEET, encoding='utf-8').read().splitlines():
            m = re.match(r'^\s+(\S+)\s+(\S+)\s+S=[\d.]+\s+需≥[\d.]+\s+缺口\+([\d.]+)', ln)
            if m:
                B.append((float(m.group(3)), m.group(1)))   # 缺口越小越好
    A.sort(); B.sort()
    return [c for _, c in A[:12]], [c for _, c in B[:12]]


A, B = load_targets()
seen, plan = set(), []
for cid in A:
    if cid not in seen:
        seen.add(cid); plan.append((cid, list(GROUPS)))          # 近线：4 种分组全试
for cid in B:
    if cid not in seen:
        seen.add(cid); plan.append((cid, ['bdv', 'sec']))        # 甜点：只试 2 种

combos, skipped = {}, []
for cid, gs in plan:
    p = f'{MINED}/{cid}.json'
    if not os.path.exists(p):
        continue
    d = json.load(io.open(p, encoding='utf-8'))
    reg = d.get('regular') or {}
    code = (reg.get('code') or '').strip()
    if not code or 'subindustry' not in code:
        skipped.append('  %-26s 无 subindustry 分组，跳过' % cid)
        continue
    opc = reg.get('operatorCount') or 0
    nleg = code.count(', subindustry)')
    s = d.get('settings') or {}
    for g in gs:
        expr = code.replace(', subindustry)', f', {GROUPS[g]})')
        est = opc + (3 * nleg if g.startswith('b') else 0)
        if est > 64:
            skipped.append('  %-26s __%s opc%d+%d>64 跳过' % (cid, g, opc, est))
            continue
        ncid = f'{cid}__r_{g}'
        if os.path.exists(f'{MINED}/{ncid}.json'):
            continue
        if len(combos) >= CAP:
            break
        combos[ncid] = {'expr': expr,
                        'neutralization': s.get('neutralization') or 'SUBINDUSTRY',
                        'decay': s.get('decay') or 10,
                        'truncation': s.get('truncation') or 0.08,
                        '_note': '换分组->%s（近线/甜点 %s）' % (g, cid)}
    if len(combos) >= CAP:
        break

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
io.open('_autologs/_gen_w240.txt', 'w', encoding='utf-8').write(
    '近线 %d + 甜点 %d → 组合 %d 条（上限 %d）\n%s'
    % (len(A), len(B), len(combos), CAP, '\n'.join(skipped)))
print('combos', len(combos))
