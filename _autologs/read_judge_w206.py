# -*- coding: utf-8 -*-
import io
raw = open(r'_autologs/judge_w206.log', 'rb').read()
t = None
for enc in ('utf-8', 'utf-16', 'gbk'):
    try:
        t = raw.decode(enc)
        if 'corr=' in t or 'w206' in t:
            break
    except Exception:
        pass
io.open(r'_autologs\q12.txt', 'w', encoding='utf-8').write(t)
