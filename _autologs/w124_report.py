# -*- coding: utf-8 -*-
import json, glob, csv, os
done = {r['id'].strip() for r in csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')) if r.get('id')}
print('=== 今天(0915)新产出的达标未提交候选（按SF排序）===')
rows = []
for f in glob.glob('data/alpha_quality_analysis/mined/*.json'):
    try: d = json.load(open(f, encoding='utf-8'))
    except Exception: continue
    b = d.get('is') or {}; t = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    if S + F < 4.0: continue
    tS = t.get('sharpe') or 0
    fails = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    if tS >= 1.25 and not fails and d.get('id') not in done:
        rows.append((S + F, str(d.get('_cid')), d.get('id') or '', S, tS, b.get('turnover') or 0))
rows.sort(reverse=True)
print('达标未提交总数:', len(rows))
for SF, cid, aid, S, tS, to in rows[:25]:
    print('%-9s %-10s SF=%.2f S=%.2f tS=%.2f T=%.3f' % (cid, aid, SF, S, tS, to))
print()
print('=== w124_e 表达式 ===')
d = json.load(open('data/alpha_quality_analysis/mined/w124_e.json', encoding='utf-8'))
print((d.get('regular') or {}).get('code'))
print()
print('=== w124_a~h 表达式对比 ===')
for i in 'abcdefgh':
    try:
        d = json.load(open(f'data/alpha_quality_analysis/mined/w124_{i}.json', encoding='utf-8'))
        b = d.get('is') or {}
        print('w124_%s SF=%.2f : %s' % (i, (b.get('sharpe') or 0) + (b.get('fitness') or 0), ((d.get('regular') or {}).get('code') or '')[:180]))
    except Exception as e:
        print('w124_%s 读失败 %s' % (i, e))
