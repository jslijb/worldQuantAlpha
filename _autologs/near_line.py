# -*- coding: utf-8 -*-
"""near_line.py —— 挑出本轮判决里"离直通线最近"的候选，打印其设置与表达式"""
import io, json, os

# 本轮判决实测（来自 exempt_0920_221616 / 221744 日志）
NEAR = [
    ('w215_w54x__r_sec', '2rwnjeww', 0.7716),
    ('w215_w54x__r_bdv', 'O0N5JbVv', 0.7680),
    ('w215_w54y__r_ind', 'RRbkbnNb', 0.7561),
    ('w215_w54y__r_sec', 'vRrJkWEd', 0.7530),
    ('w162_02__r_bdv', '3qXn9X8g', 0.7284),
    ('w162_02__r_ind', 'levR8Gz2', 0.7418),
    ('w162_02__r_bvol', '2rwnO3YN', 0.7211),
    ('x162_w164_00_MAR__r_sec', 'VkaY0lMV', 0.7857),
    ('w215_w54y__r_bvol', 'zq8JY0aX', None),
    ('x174_w125_d_AMIINT__r_ind', 'Grb3lkx0', 0.7607),
]

L = []
L.append('候选离直通线(0.685)的距离 —— 换挡 -0.09 的预测效果')
L.append('')
L.append('%-28s %-10s %8s %8s %8s %7s %6s %6s %5s %s' % (
    'cid', 'aid', 'corr_max', '换挡后', '差直通', 'S', 'F', 'tS', 'TO', 'neut/decay'))
for cid, aid, cm in NEAR:
    f = 'data/alpha_quality_analysis/mined/%s.json' % cid
    if not os.path.exists(f):
        L.append('%-28s %-10s  <文件缺失>' % (cid, aid))
        continue
    d = json.load(io.open(f, encoding='utf-8'))
    i = d.get('is') or {}
    t = d.get('test') or {}
    s = d.get('settings') or {}
    after = ('%.4f' % (cm - 0.09)) if cm else '  -  '
    gap = ('%+.4f' % (cm - 0.09 - 0.685)) if cm else '  -  '
    L.append('%-28s %-10s %8s %8s %8s %7.2f %6.2f %6.2f %5.1f%% %s/d%s' % (
        cid, aid, ('%.4f' % cm) if cm else '-', after, gap,
        i.get('sharpe') or 0, i.get('fitness') or 0, (t.get('sharpe') or 0),
        (i.get('turnover') or 0) * 100,
        s.get('neutralization'), s.get('decay')))

L.append('')
L.append('== 表达式全文（前 3 条）==')
for cid, aid, cm in NEAR[:3]:
    f = 'data/alpha_quality_analysis/mined/%s.json' % cid
    if os.path.exists(f):
        d = json.load(io.open(f, encoding='utf-8'))
        L.append('\n[%s / %s] op=%s' % (cid, aid, d.get('_ops') or '?'))
        L.append('  ' + str(d.get('regular') or (d.get('settings') or {}).get('regular'))[:600])

io.open('_autologs/_near_line.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
