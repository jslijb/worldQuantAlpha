# -*- coding: utf-8 -*-
"""分析：抬高豁免线的"热对手"是谁、什么结构（只读台账）"""
import csv, collections

ROOT_CSV = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
rows = list(csv.DictReader(open(ROOT_CSV, encoding='utf-8-sig')))
rows = [r for r in rows if r.get('id')]

out = []
out.append(f'台账有效行: {len(rows)}')
out.append('列名: ' + str(list(rows[0].keys())))
out.append('')

# 按 S 降序
def fnum(v):
    try:
        return float(v)
    except Exception:
        return 0.0

srt = sorted(rows, key=lambda r: -fnum(r.get('sharpe') or r.get('S')))
out.append('=== 已提交池 S 最高的 15 个（这些决定豁免线天花板）===')
for r in srt[:15]:
    expr = (r.get('expression') or r.get('code') or r.get('表达式') or '')
    out.append(f"  {r['id']:10} S={fnum(r.get('sharpe') or r.get('S')):5.2f} "
               f"F={fnum(r.get('fitness') or r.get('F')):5.2f} "
               f"tag={r.get('batch') or r.get('tag') or r.get('批次标签') or ''}")
    out.append(f"      {expr[:180]}")

out.append('')
out.append('=== 热对手 id 定位（本次 w112_ 预检中出现的）===')
HOT = ['kqVp6wnO', '0mR2K6lr', 'j23Pl0e5', 'E5vx6NJP']
for hid in HOT:
    m = [r for r in rows if r['id'].strip() == hid]
    if not m:
        out.append(f'  {hid} -> 台账中未找到')
        continue
    r = m[0]
    out.append(f"  {hid} | S={fnum(r.get('sharpe') or r.get('S')):.2f} "
               f"F={fnum(r.get('fitness') or r.get('F')):.2f} "
               f"tS={r.get('testSharpe') or r.get('tS') or ''} | submitted={r.get('dateSubmitted','')[:10]}")
    out.append(f"      表达式: {(r.get('expression') or r.get('code') or r.get('表达式') or '')[:300]}")

# 统计已提交表达式里最高频的字段/算子
out.append('')
out.append('=== 已提交池的字段使用频次（前 25）===')
FIELD_KW = ['cashflow_op', 'enterprise_value', 'cash', 'assets', 'fnd6_xrent', 'xrent',
            'cfo', 'ev', 'liab', 'opex', 'revenue', 'sales', 'income', 'eps', 'debt',
            'close', 'open', 'high', 'low', 'volume', 'vwap', 'returns', 'cap', 'shares']
OP_KW = ['ts_av_diff', 'ts_regression', 'ts_delta', 'ts_mean', 'ts_std_dev', 'ts_zscore',
         'ts_decay_linear', 'group_rank', 'group_neutralize', 'rank', 'vec_avg',
         'ts_corr', 'bucket', 'quantile', 'trade_when', 'hump', 'ts_rank', 'ts_sum']

fc = collections.Counter(); oc = collections.Counter()
for r in rows:
    e = (r.get('expression') or r.get('code') or r.get('表达式') or '')
    for k in FIELD_KW:
        if k in e: fc[k] += 1
    for k in OP_KW:
        if k in e: oc[k] += 1
for k, v in fc.most_common(25):
    out.append(f'  {k:22} {v:3} 次 ({v/len(rows)*100:.0f}%)')
out.append('')
out.append('=== 已提交池的算子使用频次（前 20）===')
for k, v in oc.most_common(20):
    out.append(f'  {k:20} {v:3} 次 ({v/len(rows)*100:.0f}%)')

open('_autologs/hot_rivals.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
