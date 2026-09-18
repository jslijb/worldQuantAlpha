# -*- coding: utf-8 -*-
import os, json, glob
os.chdir(r'D:\Python\worldquant')
out = []
files = sorted(glob.glob('data/alpha_quality_analysis/mined/w201_*.json'))
out.append('files: %d' % len(files))
led = set()
import csv
for r in csv.reader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')):
    if r and r[0]:
        led.add(r[0])
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    isd = d.get('is', {})
    fails = [c.get('name') for c in (isd.get('checks') or []) if isinstance(c, dict) and c.get('result') == 'FAIL']
    s = isd.get('sharpe') or 0
    ft = isd.get('fitness') or 0
    ts = (d.get('test') or {}).get('sharpe')
    cid = os.path.basename(f)[:-5]
    out.append('%s id=%s SF=%.2f tS=%s FAIL=%s' % (cid, d.get('id'), s + ft, ts, fails))
open('_autologs/r19.txt', 'w', encoding='utf-8').write('\n'.join(out))
