# -*- coding: utf-8 -*-
"""扫所有豁免判决日志，抽出命中行（放行/直通/入池）。"""
import glob, os, io

R = io.open('_autologs/_hits_scan.txt', 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


fs = sorted(glob.glob('_autologs/exempt_*.log'), key=os.path.getmtime)
log('logs: %d' % len(fs))
for f in fs[-5:]:
    t = io.open(f, encoding='utf-8', errors='replace').read()
    lines = t.splitlines()
    hits = [l for l in lines if ('★' in l or '✓' in l or '台账已追加' in l or 'ACCEPTED' in l)]
    log('=' * 60)
    log('%s  lines=%d  hits=%d' % (os.path.basename(f), len(lines), len(hits)))
    for h in hits:
        log('   ' + h.strip())
    tail = lines[-3:]
    log('  --- tail ---')
    for x in tail:
        log('   ' + x.strip())
