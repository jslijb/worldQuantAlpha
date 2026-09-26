# -*- coding: utf-8 -*-
"""vread.py —— 读 verdict_<id>.out，抽出自相关 records 明细"""
import io, re, json, sys
aid = sys.argv[1]
t = io.open('D:/Python/worldquant/_autologs/verdict_%s.out' % aid, encoding='utf-8').read()
L = []
for ln in t.splitlines():
    if ln.startswith('POST') or ln.startswith('VERDICT') or ln.startswith(aid):
        L.append(ln[:300])
m = re.search(r'"selfCorrelated".*?"records":\s*(\[.*?\]),\s*"min"', t, re.S)
if m:
    try:
        rec = json.loads(m.group(1))
    except Exception:
        rec = None
    if rec:
        L.append('')
        L.append('selfCorrelated.records（平台口径的对手集合，%d 条）:' % len(rec))
        for r in rec:
            L.append('  %-10s corr=%.4f  S=%.2f  ret=%.4f  TO=%.4f  F=%.2f  margin=%.5f'
                     % (r[0], r[5], r[6], r[7], r[8], r[9], r[10]))
        mx = max(rec, key=lambda r: r[6])
        L.append('')
        L.append('  max-S 对手 = %s S=%.2f → 豁免线 = 1.10×%.2f = %.3f' % (mx[0], mx[6], mx[6], 1.1 * mx[6]))
else:
    L.append('（未匹配到 records）')
io.open('D:/Python/worldquant/_autologs/_vread_%s.txt' % aid, 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
