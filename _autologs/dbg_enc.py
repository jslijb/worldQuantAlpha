# -*- coding: utf-8 -*-
import os
os.chdir(r'D:\Python\worldquant')
out = []
raw = open('_autologs/judge_w198.log', 'rb').read()
out.append('len %d head %r' % (len(raw), raw[:80]))
for enc in ('utf-8', 'utf-16', 'gbk'):
    try:
        t = raw.decode(enc)
        out.append('%s OK corr_in=%s len=%d' % (enc, 'corr=' in t, len(t)))
        if 'corr=' in t:
            for line in t.splitlines():
                if 'corr=' in line:
                    out.append('SAMPLE %r' % line)
                    break
    except Exception as e:
        out.append('%s FAIL %s' % (enc, e))
open('_autologs/r7.txt', 'w', encoding='utf-8').write('\n'.join(out))
