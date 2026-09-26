# -*- coding: utf-8 -*-
"""读最近 2 份 exempt 判决日志"""
import io, os

ROOT = r'D:\Python\worldquant'
AD = os.path.join(ROOT, '_autologs')
fs = [(os.path.getmtime(os.path.join(AD, f)), f) for f in os.listdir(AD)
      if f.startswith('exempt_') and f.endswith('.log')]
fs.sort(reverse=True)
L = ['最近 3 份判决日志：']
for t, f in fs[:3]:
    import datetime
    L.append('  %s  %s' % (f, datetime.datetime.fromtimestamp(t).strftime('%m-%d %H:%M:%S')))
L.append('')
for t, f in fs[:2]:
    L.append('=' * 90)
    L.append('### %s' % f)
    for ln in io.open(os.path.join(AD, f), encoding='utf-8', errors='replace'):
        ln = ln.rstrip('\n')
        if 'need' in ln or 'corr' in ln or '完成' in ln or '匹配' in ln or '池子' in ln:
            L.append(ln)

io.open(os.path.join(AD, '_latest_exempt.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
