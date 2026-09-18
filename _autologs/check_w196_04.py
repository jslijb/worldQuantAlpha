# -*- coding: utf-8 -*-
"""一次性检查脚本：w196_04 是否落盘 + 指标摘要（0918）"""
import json, glob, io

fs = glob.glob(r'D:\Python\worldquant\data\alpha_quality_analysis\mined\w196_04.json')
out = []
if not fs:
    out.append('w196_04 NOT FOUND')
else:
    d = json.load(open(fs[0], encoding='utf-8'))
    isd = d.get('is', {})
    fails = [c.get('name') for c in (isd.get('checks') or [])
             if isinstance(c, dict) and c.get('result') == 'FAIL']
    ts = (d.get('test') or {}).get('sharpe')
    s, f = isd.get('sharpe') or 0, isd.get('fitness') or 0
    out.append(f"w196_04 id={d.get('id')} S={s} F={f} SF={s+f:.2f} tS={ts} FAIL={fails}")
    out.append(f"expr={str(d.get('regular',''))[:280]}")

# x196 转换批进度
for fp in sorted(glob.glob(r'D:\Python\worldquant\data\alpha_quality_analysis\mined\x196_*.json')):
    d = json.load(open(fp, encoding='utf-8'))
    isd = d.get('is', {})
    fails = [c.get('name') for c in (isd.get('checks') or [])
             if isinstance(c, dict) and c.get('result') == 'FAIL']
    ts = (d.get('test') or {}).get('sharpe')
    s, f = isd.get('sharpe') or 0, isd.get('fitness') or 0
    out.append(f"{fp.split(chr(92))[-1]} id={d.get('id')} S={s} F={f} SF={s+f:.2f} tS={ts} FAIL={fails} neut={d.get('settings',{}).get('neutralization')}")

io.open(r'D:\Python\worldquant\_autologs\state0918e.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
