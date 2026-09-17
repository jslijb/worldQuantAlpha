# -*- coding: utf-8 -*-
"""验证：换中性化是否让原本错开的 alpha 变像？"""
import os as _os, pathlib as _pl, json, statistics as st
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d/'brain_credentials.txt').exists(): _os.chdir(_d); break
PC='data/alpha_quality_analysis/pnl'
def pnl(a): return {k: float(v) for k, v in json.load(open(f'{PC}/{a}.json', encoding='utf-8')).items()}
def corr(a,b):
    ks=sorted(set(a)&set(b))
    x=[a[k] for k in ks]; y=[b[k] for k in ks]
    mx=st.mean(x); my=st.mean(y)
    sx=sum((v-mx)**2 for v in x)**.5; sy=sum((v-my)**2 for v in y)**.5
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy) if sx and sy else None

# SUBINDUSTRY 原版 vs MARKET 版
print('=== 同一表达式：SUBINDUSTRY 原版 vs 换中性化版 ===')
for sub, mar, name in [('d5b5voEJ','levpXXGl','d5b5voEJ'),
                       ('qMxMV8NA','ZYbPGzr1','qMxMV8NA'),
                       ('N1a18988','LLNVA1m1','N1a18988'),
                       ('58z8eK91','2rw8da7N','58z8eK91')]:
    try: c=corr(pnl(sub), pnl(mar))
    except Exception as e: c=f'缺数据 {e}'
    print(f'  {name:10s} SUB({sub}) vs MARKET({mar}) = {c if isinstance(c,str) else round(c,4)}')

print()
print('=== 关键：两个原本错开的表达式，换 MARKET 后是否变像 ===')
pairs=[('d5b5voEJ','qMxMV8NA','原版 SUBINDUSTRY'),
       ('d5b5voEJ','N1a18988','原版 SUBINDUSTRY'),
       ('qMxMV8NA','58z8eK91','原版 SUBINDUSTRY')]
for a,b,tag in pairs:
    print(f'  {a} vs {b} [{tag}] = {corr(pnl(a),pnl(b)):.4f}')
pairs2=[('levpXXGl','ZYbPGzr1','换 MARKET 后'),
        ('levpXXGl','pwRYOV8X','MARKET vs SECTOR'),
        ('levpXXGl','LLNVA1m1','换 MARKET 后')]
for a,b,tag in pairs2:
    print(f'  {a} vs {b} [{tag}] = {corr(pnl(a),pnl(b)):.4f}')
