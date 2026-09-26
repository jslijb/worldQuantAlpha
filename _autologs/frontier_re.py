# -*- coding: utf-8 -*-
"""frontier_re.py —— 解析判决日志，按 corr_max 升序排出「离墙最近的候选」（自写 UTF-8）"""
import io, os, re, glob

ROOT = 'D:/Python/worldquant/'
logs = sorted(glob.glob(ROOT + '_autologs/exempt_*.log'), key=os.path.getmtime)
log = logs[-1]

recs = []
raw = io.open(log, 'rb').read().decode('utf-8', 'ignore')
for ln in raw.splitlines():
    # 形如:  ✗ pQID cid  SF=.. S=.. corr_max=0.xxxx 撞XX(S=..) 需≥.. → ..
    m = re.search(r'([✓✗★?])\s+(\w+)\s+(\S+)\s+SF=([\d.]+)\s+S=([\d.]+)\s+corr_max=([\d.]+)', ln)
    if not m:
        m2 = re.search(r'([✓✗★?])\s+(\w+)\s+(\S+)\s+SF=([\d.]+)\s+tS=([\d.]+)\s+corr<', ln)
        if m2:
            recs.append(dict(mark=m2.group(1), aid=m2.group(2), cid=m2.group(3),
                             SF=float(m2.group(4)), S=None, cmax=0.0, need=None, rival=None))
        continue
    mark, aid, cid, SF, S, cmax = m.group(1), m.group(2), m.group(3), float(m.group(4)), float(m.group(5)), float(m.group(6))
    need = None
    mn = re.search(r'需≥([\d.]+)', ln)
    if mn:
        need = float(mn.group(1))
    rv = re.search(r'撞(\w+)\(S=([\d.]+)\)', ln)
    rival = (rv.group(1), float(rv.group(2))) if rv else None
    recs.append(dict(mark=mark, aid=aid, cid=cid, SF=SF, S=S, cmax=cmax, need=need, rival=rival))

L = []
L.append('日志: %s' % os.path.basename(log))
L.append('解析出候选 %d 条' % len(recs))
marks = {}
for r in recs:
    marks[r['mark']] = marks.get(r['mark'], 0) + 1
L.append('标记分布: %s' % marks)
L.append('')
if recs:
    cm = [r['cmax'] for r in recs if r['S'] is not None]
    L.append('corr_max: 最小 %.4f / 中位 %.4f / 最大 %.4f'
             % (min(cm), sorted(cm)[len(cm) // 2], max(cm)))
    bands = [('<=0.685 直通', 0, 0.685), ('0.685~0.70', 0.685, 0.70), ('0.70~0.75', 0.70, 0.75),
             ('0.75~0.80', 0.75, 0.80), ('0.80~0.90', 0.80, 0.90), ('>=0.90', 0.90, 9)]
    L.append('')
    L.append('== corr_max 分带 ==')
    for name, lo, hi in bands:
        g = [r for r in recs if r['S'] is not None and lo <= r['cmax'] < hi]
        L.append('  %-14s %3d 条' % (name, len(g)))

    L.append('')
    L.append('== 离墙最近 Top 30（corr_max 升序）==')
    L.append('  %-28s %-11s %6s %6s %9s %8s %s' % ('cid', 'aid', 'S', 'SF', 'corr_max', '需≥', '撞谁'))
    for r in sorted([x for x in recs if x['S'] is not None], key=lambda z: z['cmax'])[:30]:
        L.append('  %-28s %-11s %6.2f %6.2f %9.4f %8s %s'
                 % (r['cid'][:28], r['aid'], r['S'], r['SF'], r['cmax'],
                    ('%.2f' % r['need']) if r['need'] else '-',
                    ('%s(S=%.2f)' % r['rival']) if r['rival'] else ''))

    L.append('')
    L.append('== 缺口最小的 Top 20（need - S 升序，最接近豁免放行）==')
    g = [r for r in recs if r['need'] and r['S'] is not None]
    for r in sorted(g, key=lambda z: z['need'] - z['S'])[:20]:
        L.append('  %-28s %-11s S=%5.2f 需≥%5.2f 缺口 %+5.2f corr_max=%.4f 撞%s'
                 % (r['cid'][:28], r['aid'], r['S'], r['need'], r['need'] - r['S'], r['cmax'],
                    ('%s(S=%.2f)' % r['rival']) if r['rival'] else ''))

io.open(ROOT + '_autologs/_frontier_re.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
