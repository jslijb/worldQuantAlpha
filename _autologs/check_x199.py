# -*- coding: utf-8 -*-
"""检查 x199 转换产出（w59_b/w114_m 的 SECTOR/MARKET 版）质量指标"""
import json, glob, io

out = []
for fp in sorted(glob.glob(r'D:\Python\worldquant\data\alpha_quality_analysis\mined\x199_*.json')):
    d = json.load(open(fp, encoding='utf-8'))
    isd = d.get('is', {})
    fails = [c.get('name') for c in (isd.get('checks') or [])
             if isinstance(c, dict) and c.get('result') == 'FAIL']
    ts = (d.get('test') or {}).get('sharpe')
    s, f = isd.get('sharpe') or 0, isd.get('fitness') or 0
    out.append('%s id=%s S=%.2f F=%.2f SF=%.2f tS=%s FAIL=%s neut=%s' % (
        fp.split(chr(92))[-1], d.get('id'), s, f, s + f, ts, fails,
        d.get('settings', {}).get('neutralization')))

if not out:
    out.append('NO x199 FILES')
io.open(r'D:\Python\worldquant\_autologs\ans6.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
