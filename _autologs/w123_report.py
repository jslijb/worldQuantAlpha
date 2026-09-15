# -*- coding: utf-8 -*-
import json, glob, csv, os
done = {r['id'].strip() for r in csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')) if r.get('id')}
print('=== batch123 (w123_) 产出指标 ===')
for f in sorted(glob.glob('data/alpha_quality_analysis/mined/w123_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    b = d.get('is') or {}; t = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0; tS = t.get('sharpe') or 0
    fails = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = 'PASS' if (S + F >= 4.0 and tS >= 1.25 and not fails) else 'fail'
    print('%-8s %-10s S=%.2f F=%.2f SF=%.2f tS=%.2f T=%.3f %s subm=%s FAILS=%s'
          % (d.get('_cid'), d.get('id'), S, F, S + F, tS, b.get('turnover') or 0, ok, d.get('id') in done, fails))
print()
print('=== mined 目录最近修改的 12 个文件 ===')
ls = sorted(glob.glob('data/alpha_quality_analysis/mined/*.json'), key=os.path.getmtime)
import datetime
for x in ls[-12:]:
    print(os.path.basename(x), datetime.datetime.fromtimestamp(os.path.getmtime(x)).strftime('%m-%d %H:%M'))
