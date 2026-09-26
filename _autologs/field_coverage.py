# -*- coding: utf-8 -*-
"""field_coverage.py —— 池内到底用了几个"数据字段"（墙的材质清单）"""
import io, csv, re, collections

ROOT = 'D:/Python/worldquant/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

# 视为"原始数据字段"的模式：不含纯算子/常量
OPS = set('''group_rank ts_rank ts_mean ts_delta ts_av_diff ts_std_dev ts_corr ts_zscore ts_sum ts_min ts_max
ts_decay_linear ts_arg_max ts_arg_min abs log sign sqrt rank bucket if_else trade_when vec_avg vec_sum
subtract divide add multiply power max min reverse scale winsorize hump quantile days_from_last_change
kth_element last_diff_value ts_backfill ts_returns ts_step ts_regression ts_ir ts_skewness ts_kurtosis'''.split())

rows = []
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f); hdr = next(rd)
    for r in rd:
        if r and r[0].strip():
            rows.append(r)
seen = {}
for r in rows:
    seen.setdefault(r[0].strip(), r)

TOKEN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
fields = collections.Counter()
for aid, r in seen.items():
    code = (r[1] if len(r) > 1 else '').strip('"')
    for t in TOKEN.findall(code):
        if t in OPS or t in ('subindustry', 'industry', 'sector', 'range', 'TOP3000', 'TOP1000'):
            continue
        if len(t) <= 2:
            continue
        fields[t] += 1

L = ['台账唯一 id %d 条' % len(seen)]
L.append('')
L.append('== 原始数据字段使用频次（出现 >=2 次）==')
for k, v in fields.most_common():
    if v >= 2:
        L.append('  %-55s %d' % (k, v))
L.append('  —— 只出现 1 次的字段 %d 个：%s' % (
    sum(1 for v in fields.values() if v == 1),
    ', '.join(k for k, v in fields.items() if v == 1)))

L.append('')
L.append('== 汇总 ==')
L.append('  不同字段总数 %d' % len(fields))
top = fields.most_common(8)
tot = sum(fields.values())
L.append('  前 8 个字段占全部字段引用的 %.0f%%：%s' % (
    100.0 * sum(v for _, v in top) / tot, ', '.join('%s(%d)' % (k, v) for k, v in top)))

io.open(ROOT + '_autologs/_fields.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok %d' % len(fields))
