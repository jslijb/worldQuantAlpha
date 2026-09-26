# -*- coding: utf-8 -*-
"""tail_log.py —— 打印指定日志的最后 N 行（自写 UTF-8，避开 shell 编码）"""
import io, sys
f = sys.argv[1]
n = int(sys.argv[2]) if len(sys.argv) > 2 else 40
t = None
raw = io.open(f, 'rb').read()
for enc in ('utf-8', 'utf-16', 'gbk'):
    try:
        t = raw.decode(enc)
        break
    except Exception:
        pass
ls = t.splitlines()
out = ['%s  共 %d 行，末 %d 行：' % (f, len(ls), n), ''] + ls[-n:]
io.open('_autologs/_tail.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
