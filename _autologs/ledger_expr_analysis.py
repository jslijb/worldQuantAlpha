# -*- coding: utf-8 -*-
"""把已提交 alpha 的表达式从 mined 映射出来，生成台账增强视图（不修改原台账）。
并分析：已提交池的字段/算子频次、高 S 对手的结构共性。"""
import csv, json, glob, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
rows = list(csv.DictReader(open(LEDGER, encoding='utf-8-sig')))
rows = [r for r in rows if r.get('id')]

# 建 id -> 表达式映射（从全部 mined）
id2expr = {}
id2meta = {}
for f in glob.glob('data/alpha_quality_analysis/mined/*.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid:
        continue
    code = (d.get('regular') or {}).get('code') or ''
    if code:
        id2expr[aid] = code
        id2meta[aid] = {
            'cid': d.get('_cid'),
            'settings': d.get('settings') or {},
            'neutralization': (d.get('settings') or {}).get('neutralization'),
        }

hit = sum(1 for r in rows if r['id'].strip() in id2expr)

# 输出增强视图（新文件，不动原台账）
outp = 'data/alpha_quality_analysis/ledger_with_expr.csv'
with open(outp, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['id', 'expr', 'S', 'F', 'T', 'R', 'DD', 'selfCorr', 'dateSubmitted',
                'decay', 'neutralization', 'batch', '_cid'])
    for r in rows:
        aid = r['id'].strip()
        m = id2meta.get(aid, {})
        w.writerow([aid, id2expr.get(aid, ''), r.get('S'), r.get('F'), r.get('T'),
                    r.get('R'), r.get('DD'), r.get('selfCorr'), r.get('dateSubmitted'),
                    m.get('neutralization') or r.get('neutralization'), r.get('batch'),
                    m.get('cid', '')])

out = []
out.append(f'台账行: {len(rows)} | mined 中匹配到表达式: {hit} / {len(rows)}')
out.append(f'增强视图已写出: {outp}')
out.append('')

# 字段/算子频次
FIELD_KW = ['cashflow_op', 'enterprise_value', 'cash', 'assets', 'fnd6_xrent', 'xrent',
            'cfo', 'cap', 'liab', 'opex', 'revenue', 'sales', 'income', 'eps', 'debt',
            'close', 'open', 'high', 'low', 'volume', 'vwap', 'returns', 'shares',
            'ev', 'ebit', 'sga', 'inventory', 'receivable', 'payable']
OP_KW = ['ts_av_diff', 'ts_regression', 'ts_delta', 'ts_mean', 'ts_std_dev', 'ts_zscore',
         'ts_decay_linear', 'group_rank', 'group_neutralize', 'rank', 'vec_avg',
         'ts_corr', 'bucket', 'quantile', 'trade_when', 'hump', 'ts_rank', 'ts_sum',
         'ts_backfill', 'winsorize', 'if_else', 'scale', 'normalize', 'ts_arg_max']

fc = collections.Counter(); oc = collections.Counter(); nc = collections.Counter()
exprs = []
for r in rows:
    e = id2expr.get(r['id'].strip(), '')
    if not e:
        continue
    exprs.append((r['id'].strip(), r.get('S'), r.get('F'), r.get('selfCorr'), r.get('batch'), e))
    for k in FIELD_KW:
        if k in e: fc[k] += 1
    for k in OP_KW:
        if k in e: oc[k] += 1
    neut = id2meta.get(r['id'].strip(), {}).get('neutralization')
    if neut: nc[neut] += 1

out.append(f'有表达式的已提交 alpha: {len(exprs)}')
out.append('')
out.append('=== 中性化方式分布 ===')
for k, v in nc.most_common():
    out.append(f'  {k:16} {v:3} ({v/len(exprs)*100:.0f}%)')
out.append('')
out.append('=== 字段使用频次（已提交池）===')
for k, v in fc.most_common(22):
    out.append(f'  {k:20} {v:3} 次 ({v/len(exprs)*100:.0f}%)')
out.append('')
out.append('=== 算子使用频次（已提交池）===')
for k, v in oc.most_common(18):
    out.append(f'  {k:20} {v:3} 次 ({v/len(exprs)*100:.0f}%)')
out.append('')
out.append('=== 已提交池 S 最高的 12 个 + 表达式 ===')
srt = sorted(exprs, key=lambda x: -(float(x[1]) if x[1] else 0))
for aid, S, F, sc, batch, e in srt[:12]:
    out.append(f'  {aid:10} S={S:>5} F={F:>5} selfCorr={sc:>7} | {batch}')
    out.append(f'      {e[:400]}')
    out.append('')

open('_autologs/ledger_expr_analysis.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
