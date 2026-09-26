# -*- coding: utf-8 -*-
"""定位 x244 批次落盘文件 + 打印关键指标"""
import io, json, os, re

ROOT = r'D:\Python\worldquant'
MD = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'mined')
L = []
rows = []
for fn in os.listdir(MD):
    if not fn.startswith('x244_') or not fn.endswith('.json'):
        continue
    p = os.path.join(MD, fn)
    try:
        d = json.load(io.open(p, encoding='utf-8'))
    except Exception as e:
        L.append('ERR %s %s' % (fn, e))
        continue
    cid = d.get('cid') or d.get('name') or fn[:-5]
    aid = d.get('id') or d.get('alpha_id') or '-'
    isd = d.get('is') or {}
    S = isd.get('sharpe')
    F = isd.get('fitness')
    TO = isd.get('turnover')
    tS = (isd.get('test') or {}).get('sharpe') if isinstance(isd.get('test'), dict) else None
    st = d.get('settings') or {}
    rows.append((cid, aid, S, F, TO, tS, st.get('neutralization'), st.get('decay'),
                 len(d.get('regular') or d.get('expression') or '')))

rows.sort(key=lambda r: (-(r[3] or 0)))
L.append('x244 落盘 %d 条' % len(rows))
L.append('%-34s %-10s %5s %5s %7s %5s %-12s %5s' % ('cid', 'aid', 'S', 'F', 'TO', 'tS', 'neu', 'decay'))
for r in rows:
    L.append('%-34s %-10s %5s %5s %7s %5s %-12s %5s' % (
        str(r[0])[:34], str(r[1]), r[2], r[3], r[4], r[5], str(r[6]), str(r[7])))

io.open(os.path.join(ROOT, '_autologs', '_ls_x244.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok', len(rows))
