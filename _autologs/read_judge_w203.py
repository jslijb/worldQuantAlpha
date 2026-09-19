# -*- coding: utf-8 -*-
import io
raw = open(r'_autologs/judge_w203.log', 'rb').read()
t = None
for enc in ('utf-8', 'utf-16', 'gbk'):
    try:
        t = raw.decode(enc)
        if 'corr=' in t or 'w203' in t:
            break
    except Exception:
        pass
io.open(r'_autologs\q6.txt', 'w', encoding='utf-8').write(t)
