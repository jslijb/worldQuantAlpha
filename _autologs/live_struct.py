# -*- coding: utf-8 -*-
"""live_struct.py —— 看实时判决日志的段落结构，找"可提交/通过"的正面结论行"""
import io, re

for SRC in ['_autologs/_exempt_live.txt', '_autologs/_exempt_dry_run.txt']:
    raw = io.open(SRC, 'rb').read()
    t = None
    for enc in ('utf-8', 'utf-16', 'gbk'):
        try:
            t = raw.decode(enc)
            break
        except Exception:
            pass
    if t is None:
        continue
    lines = t.splitlines()
    L = ['===== %s (%d 行) =====' % (SRC, len(lines))]

    L.append('-- 段落标题行（以 == / -- / ★ / 匹配 / 池子 开头）--')
    for i, x in enumerate(lines):
        s = x.strip()
        if re.match(r'^(==|--|\u2605|\u5339\u914d|\u6c60\u5b50|\u5019\u9009|\u76f4\u901a|\u8c41\u514d|\u53ef\u63d0\u4ea4|\u5efa\u8bae)', s) or s.startswith('=') or s.startswith('-'):
            L.append('  %5d | %s' % (i, s[:160]))

    L.append('-- 含 PASS/\u53ef\u63d0\u4ea4/\u2713/\u2714/\u2605 的行 --')
    n = 0
    for i, x in enumerate(lines):
        if ('\u53ef\u63d0\u4ea4' in x) or ('PASS' in x) or ('\u2713' in x) or ('\u2714' in x) or ('\u2605' in x):
            L.append('  %5d | %s' % (i, x.strip()[:200]))
            n += 1
            if n > 60:
                break
    L.append('  共 %d 行' % n)
    io.open('_autologs/_live_struct_%s.txt' % SRC.split('/')[-1].replace('.txt', ''), 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
