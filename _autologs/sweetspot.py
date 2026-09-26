# -*- coding: utf-8 -*-
"""sweetspot.py —— 从判决日志里捞出"豁免线低（撞弱靶）"的近失候选

判据：日志里 "需≥X" 是豁免线（1.1 × 收录到的最高 S 对手）。
      X 越低说明撞的对手越弱、越可能靠中等 S 过关。
      缺口 = X - 候选 S。
"""
import re, io, glob, os

L = []
rows = []
for f in glob.glob('_autologs/_dry3_latest.txt') + glob.glob('_autologs/_grp_judge.txt') \
        + glob.glob('_autologs/_w236_judge.txt') + glob.glob('_autologs/_dry2_latest.txt'):
    if not os.path.exists(f):
        continue
    for ln in io.open(f, encoding='utf-8').read().splitlines():
        m = re.match(r'^\s*[✗★]\s+(\S+)\s+(\S+)\s+SF=([\d.]+)\s+S=([\d.]+)\s+corr_max=([\d.]+)\s+撞\S+\(S=([\d.]+)\)\s+需≥([\d.]+)', ln)
        if not m:
            continue
        aid, cid, sf, S, cm, oppS, need = m.groups()
        S, need, cm, oppS = float(S), float(need), float(cm), float(oppS)
        if need <= 2.90:                       # 只看"撞弱靶"的
            rows.append(dict(aid=aid, cid=cid, S=S, need=need, gap=need - S,
                             cm=cm, oppS=oppS, src=os.path.basename(f)))

# 同一个 cid 取最新一条（后出现的覆盖）
best = {}
for r in rows:
    k = r['cid']
    if k not in best or r['need'] < best[k]['need']:
        best[k] = r
vs = sorted(best.values(), key=lambda r: r['gap'])

L.append('== 撞弱靶（豁免线 ≤ 2.90）的候选，按缺口排序 ==')
L.append('  %-26s %-10s S=%.2f 需≥%.2f 缺口%+.2f corr=%.4f 最高对手S=%.2f' % ('cid', '', 0, 0, 0, 0, 0))
for r in vs:
    L.append('  %-26s %-10s S=%.2f 需≥%.2f 缺口%+.2f corr=%.4f 最高对手S=%.2f  [%s]'
             % (r['cid'], r['aid'], r['S'], r['need'], r['gap'], r['cm'], r['oppS'], r['src']))
L.append('')
L.append('合计 %d 条（去重后）；缺口 ≤ 0.20 的 %d 条'
         % (len(vs), sum(1 for r in vs if r['gap'] <= 0.20)))
io.open('_autologs/_sweetspot.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('rows', len(vs))
