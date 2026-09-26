# -*- coding: utf-8 -*-
"""rejudge70.py —— 修正本地判决器的系统性高估

问题：submit_exempt.py 用 CORR_FLOOR=0.66 收对手，然后
      need = 1.10 x max(对手 S)，**没有把 corr<0.70 的对手剔除**。
      而平台的豁免线只数 corr>=0.70 的对手。
      于是当"最高 S 对手"的本地 corr 落在 0.66~0.70 时，need 被系统性抬高
      （实测反例 0mXKpmYq：本地判死，直接 POST 却 ACCEPTED）。

本脚本：读判决日志，按平台口径重算 need70，输出"值得直接 POST 试"的名单。
用法：python _autologs/rejudge70.py <logfile> [...]
"""
import io, re, sys, os

LOGS = sys.argv[1:] or ['_autologs/exempt_0920_212224.log', '_autologs/exempt_0920_213306.log']

RIVAL = re.compile(r'([A-Za-z0-9]{6,12})\(S=([\d.]+),corr=([\d.]+)\)')
HEAD = re.compile(r'(?:\u2717|\u2605|\u2713|\?)\s+([A-Za-z0-9]{6,12})\s+(\S+?)\s+SF=([\d.]+)\s+S=([\d.]+)\s+corr_max=([\d.]+)')

allrec = {}
for LG in LOGS:
    if not os.path.exists(LG):
        continue
    for ln in io.open(LG, encoding='utf-8'):
        m = HEAD.search(ln)
        if not m:
            continue
        aid, cid, SF, S, cmax = m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5))
        rivals = [(a, float(s), float(c)) for a, s, c in RIVAL.findall(ln)]
        if not rivals:
            continue
        r70 = [r for r in rivals if r[2] >= 0.70]
        need_all = 1.10 * max(r[1] for r in rivals)
        need70 = 1.10 * max(r[1] for r in r70) if r70 else None
        topS = max(rivals, key=lambda r: r[1])
        allrec[aid] = dict(aid=aid, cid=cid, SF=SF, S=S, cmax=cmax, rivals=rivals,
                           r70=r70, need_all=need_all, need70=need70, topS=topS)

L = ['解析到 %d 条判决' % len(allrec)]
L.append('')
L.append('== A. 最高 S 对手本地 corr < 0.70 → 本地 need 被抬高（平台口径更低）==')
A = [r for r in allrec.values() if r['topS'][2] < 0.70]
A.sort(key=lambda r: -(r['S'] - (r['need70'] or 0)))
for r in A:
    n70 = ('%.2f' % r['need70']) if r['need70'] else 'n/a'
    gap = r['S'] - r['need70'] if r['need70'] else None
    L.append('  %s %-24s S=%.2f corr_max=%.4f | 本地判 need=%.2f(撞%s,corr=%.4f) | 按0.70重算 need70=%s 差=%s'
             % (r['aid'], r['cid'], r['S'], r['cmax'], r['need_all'], r['topS'][0], r['topS'][2], n70,
                ('%+.2f' % gap) if gap is not None else '-'))
    L.append('      对手(按S降序): ' + ' '.join('%s(S=%.2f,c=%.4f)' % x for x in sorted(r['rivals'], key=lambda t: -t[1])))
L.append('  共 %d 条' % len(A))

L.append('')
L.append('== B. 按 0.70 口径已达标（S >= need70）→ 建议直接 POST ==')
B = [r for r in allrec.values() if r['need70'] and r['S'] >= r['need70']]
B.sort(key=lambda r: -(r['S'] - r['need70']))
for r in B:
    L.append('  %s %-24s S=%.2f SF=%.2f need70=%.2f 余量=+%.3f corr_max=%.4f'
             % (r['aid'], r['cid'], r['S'], r['SF'], r['need70'], r['S'] - r['need70'], r['cmax']))
L.append('  共 %d 条' % len(B))

L.append('')
L.append('== C. 接近区（S 距 need70 只差 0~0.30，值得调 decay 顶 S 后 POST）==')
C = [r for r in allrec.values() if r['need70'] and 0 < r['need70'] - r['S'] <= 0.30]
C.sort(key=lambda r: (r['need70'] - r['S']))
for r in C:
    L.append('  %s %-24s S=%.2f need70=%.2f 缺口=%.3f corr_max=%.4f'
             % (r['aid'], r['cid'], r['S'], r['need70'], r['need70'] - r['S'], r['cmax']))
L.append('  共 %d 条' % len(C))

L.append('')
L.append('== D. 全库 corr_max 分布（去重）==')
import collections
b = collections.Counter()
for r in allrec.values():
    c = r['cmax']
    k = '<=0.685' if c <= 0.685 else ('0.685-0.70' if c <= 0.70 else ('0.70-0.80' if c <= 0.80 else ('0.80-0.90' if c <= 0.90 else '>0.90')))
    b[k] += 1
for k in ['<=0.685', '0.685-0.70', '0.70-0.80', '0.80-0.90', '>0.90']:
    L.append('  %-11s %d' % (k, b[k]))

io.open('_autologs/_rejudge70.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok %d' % len(allrec))
