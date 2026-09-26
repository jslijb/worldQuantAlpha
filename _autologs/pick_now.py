# -*- coding: utf-8 -*-
"""pick_now.py —— 从实时豁免判决日志里挑出：① corr<=0.688 ② 满足豁免线（S>=need）的候选"""
import io, re, os

SRC = '_autologs/_exempt_live.txt'
raw = io.open(SRC, 'rb').read()
t = None
for enc in ('utf-8', 'utf-16', 'gbk'):
    try:
        t = raw.decode(enc)
        break
    except Exception:
        pass

lines = t.splitlines()
L = []

# 匹配形如: ✗ id skeleton  SF=6.82 S=3.30 corr_max=0.9779 撞 pwRwWoJ3(S=3.33) 需≥3.66
pat = re.compile(r'SF=([\d.]+)\s+S=([\d.]+)\s+corr_max=([\d.]+)\s+撞\s+(\S+?)\(S=([\d.]+)\)\s+需≥([\d.]+)')
pat2 = re.compile(r'SF=([\d.]+)\s+S=([\d.]+)\s+corr_max=([\d.]+)')

recs = []
cur = None
for ln in lines:
    m = re.search(r'([\u2717\u2713\u2718\u2714\u26a0\u2757\u2605]\s*)?([A-Za-z0-9_]{6,12})\s+(\S+)\s+SF=', ln)
    idm = re.search(r'SF=', ln)
    if not idm:
        continue
    mm = pat.search(ln)
    mm2 = pat2.search(ln)
    if not mm2:
        continue
    # 取 id：SF= 之前最后一个 token
    head = ln[:idm.start()].strip()
    toks = head.replace('\u2717', ' ').replace('\u2713',' ').split()
    cid = toks[-2] if len(toks) >= 2 else None
    skel = toks[-1] if toks else ''
    if mm:
        recs.append(dict(id=cid, skel=skel, sf=float(mm.group(1)), S=float(mm.group(2)),
                         corr=float(mm.group(3)), hit=mm.group(4), hitS=float(mm.group(5)),
                         need=float(mm.group(6))))
    else:
        recs.append(dict(id=cid, skel=skel, sf=float(mm2.group(1)), S=float(mm2.group(2)),
                         corr=float(mm2.group(3)), hit=None, hitS=None, need=None))

L.append('解析到 %d 条判决记录' % len(recs))

L.append('')
L.append('== ① corr_max <= 0.688（直通区）==')
low = [r for r in recs if r['corr'] <= 0.688]
low.sort(key=lambda r: r['corr'])
for r in low[:30]:
    L.append('  %s %-26s SF=%5.2f S=%5.2f corr=%.4f 撞 %s(S=%.2f) need=%.2f' % (
        r['id'], r['skel'], r['sf'], r['S'], r['corr'], r['hit'] or '-', r['hitS'] or 0, r['need'] or 0))
if not low:
    L.append('  (无)')

L.append('')
L.append('== ② corr_max 0.688~0.70（缓冲待测区）==')
mid = [r for r in recs if 0.688 < r['corr'] <= 0.70]
mid.sort(key=lambda r: r['corr'])
for r in mid[:30]:
    L.append('  %s %-26s SF=%5.2f S=%5.2f corr=%.4f 撞 %s' % (r['id'], r['skel'], r['sf'], r['S'], r['corr'], r['hit'] or '-'))
if not mid:
    L.append('  (无)')

L.append('')
L.append('== ③ 满足豁免线（S >= need）==')
ok = [r for r in recs if r['need'] and r['S'] >= r['need']]
ok.sort(key=lambda r: -(r['S'] - r['need']))
for r in ok[:30]:
    L.append('  %s %-26s S=%5.2f need=%.2f 余量=+%.3f corr=%.4f' % (r['id'], r['skel'], r['S'], r['need'], r['S'] - r['need'], r['corr']))
if not ok:
    L.append('  (无)')

L.append('')
L.append('== ④ 全库 corr_max 分布 ==')
import collections
bins = collections.Counter()
for r in recs:
    c = r['corr']
    k = '<=0.60' if c <= 0.60 else ('0.60-0.65' if c <= 0.65 else ('0.65-0.685' if c <= 0.685 else ('0.685-0.70' if c <= 0.70 else ('0.70-0.80' if c <= 0.80 else ('0.80-0.90' if c <= 0.90 else '>0.90')))))
    bins[k] += 1
for k in ['<=0.60', '0.60-0.65', '0.65-0.685', '0.685-0.70', '0.70-0.80', '0.80-0.90', '>0.90']:
    L.append('  %-11s %d' % (k, bins[k]))

L.append('')
L.append('== ⑤ SF 最高 Top25（不管 corr）==')
top = sorted(recs, key=lambda r: -r['sf'])[:25]
for r in top:
    L.append('  %s %-26s SF=%5.2f S=%5.2f corr=%.4f 撞 %s(S=%.2f) need=%.2f' % (
        r['id'], r['skel'], r['sf'], r['S'], r['corr'], r['hit'] or '-', r['hitS'] or 0, r['need'] or 0))

io.open('_autologs/_pick_now.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok %d' % len(recs))
