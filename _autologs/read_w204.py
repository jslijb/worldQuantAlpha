# -*- coding: utf-8 -*-
import io
raw = open(r'_autologs/w204_search.log', 'rb').read()
t = None
for enc in ('utf-8', 'utf-16', 'gbk'):
    try:
        t = raw.decode(enc)
        if '池子' in t or '腿库' in t or 'WARN' in t:
            break
    except Exception:
        pass
lines = [l for l in t.splitlines()
         if ('池子' in l or '腿库' in l or '评估' in l or '配额' in l
             or '已落盘' in l or 'WARN' in l or l.strip().startswith('w204_'))]
io.open(r'_autologs\q8.txt', 'w', encoding='utf-8').write('\n'.join(lines[:30]))
