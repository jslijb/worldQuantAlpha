# -*- coding: utf-8 -*-
"""表达式结构分析：高分组 vs 失败组的差异，用于提炼"什么结构有效" """
import json, re, collections, statistics
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
d = json.load(open(ROOT / '_autologs' / 'expr_all.json', encoding='utf-8'))
recs = d['records']

L = []
L.append('=' * 72)
L.append('表达式结构分析')
L.append('=' * 72)

# status 分布
L.append('A. status 分布: ' + str(dict(collections.Counter(r.get('status') for r in recs))))
L.append('   grade 分布: ' + str(dict(collections.Counter(r.get('grade') for r in recs))))
L.append('')

def legs(e):
    # 按顶层 + 拆腿（忽略括号内的 +）
    out, dep, cur = [], 0, ''
    for ch in e:
        if ch == '(':
            dep += 1
        elif ch == ')':
            dep -= 1
        if ch == '+' and dep == 0:
            out.append(cur.strip()); cur = ''
        else:
            cur += ch
    if cur.strip():
        out.append(cur.strip())
    return [x for x in out if x]

def fields(e):
    # 提取标识符（排除算子名）
    return re.findall(r'\b([a-z][a-z0-9_]{2,})\b', e)

ops = {o['name'] for o in json.load(open(ROOT / 'data/alpha_quality_analysis' / 'operators.json', encoding='utf-8'))}

# 分档
def band(r):
    S, F, tS, f = r['S'], r['F'], r['tS'], r['fails']
    sf = (S or 0) + (F or 0)
    if S is None: return 'ERR'
    if sf >= 5.5 and not f: return 'A ≥5.5'
    if sf >= 5.0 and not f: return 'B 5.0-5.5'
    if sf >= 4.0 and not f: return 'C 4.0-5.0'
    if sf >= 3.0: return 'D 3.0-4.0'
    return 'E <3.0'

bands = collections.defaultdict(list)
for r in recs:
    bands[band(r)].append(r)

L.append('B. 分档统计')
for k in sorted(bands):
    v = bands[k]
    tv = [x['T'] for x in v if x['T']]
    tsv = [x['tS'] for x in v if x['tS'] is not None]
    L.append(f'   {k:12} n={len(v):4} 中位T={statistics.median(tv) if tv else 0:.3f} 中位tS={statistics.median(tsv) if tsv else 0:.2f}')
L.append('')

L.append('C. 腿数分布（按档）')
for k in sorted(bands):
    lc = collections.Counter(len(legs(r['expr'])) for r in bands[k])
    L.append(f'   {k:12} ' + '  '.join(f'{a}腿:{b}' for a, b in sorted(lc.items())))
L.append('')

# 分档字段 top
L.append('D. 各档高频字段 top15（排除算子/常量）')
for k in sorted(bands):
    fc = collections.Counter()
    for r in bands[k]:
        for f in fields(r['expr']):
            if f in ops or f in ('range', 'nan', 'true', 'false', 'rate', 'k', 'constant', 'dense', 'market'):
                continue
            fc[f] += 1
    L.append(f'   {k:12} ' + ', '.join(f'{a}({b})' for a, b in fc.most_common(15)))
L.append('')

# 骨架签名聚类（字段集合）
L.append('E. 字段组合签名 top20（= 可复用的骨架）')
sig = collections.Counter()
sig_ok = collections.Counter()
for r in recs:
    fs = tuple(sorted({f for f in fields(r['expr']) if f not in ops and len(f) > 3 and '_' in f}))
    if not fs: continue
    sig[fs] += 1
    if band(r).startswith(('A', 'B', 'C')): sig_ok[fs] += 1
for s, c in sig.most_common(20):
    L.append(f'   n={c:3} 全过={sig_ok.get(s,0):3}  {", ".join(s)[:150]}')
L.append('')

# 失败组特征
L.append('F. 失败组特征（LOW_FITNESS / LOW_SHARPE）')
for key in ('LOW_FITNESS', 'LOW_SHARPE', 'LOW_SUB_UNIVERSE_SHARPE', 'CONCENTRATED_WEIGHT', 'HIGH_TURNOVER'):
    sub = [r for r in recs if key in r['fails']]
    if not sub: continue
    tv = [x['T'] for x in sub if x['T']]
    lc = collections.Counter(len(legs(r['expr'])) for r in sub)
    L.append(f'   {key:24} n={len(sub):4} 中位T={statistics.median(tv) if tv else 0:.3f} 腿数={dict(sorted(lc.items()))}')
L.append('')

# 同式多跑
L.append('G. 同式多跑（同表达式不同 setting 跑多次）top15')
ec = collections.Counter(r['expr'] for r in recs)
for e, c in ec.most_common(15):
    if c < 2: break
    ss = [r for r in recs if r['expr'] == e]
    L.append(f'   n={c}  SF={[round(x["SF"],2) for x in ss]}  {e[:100]}')
L.append('')

L.append('H. 已提交过的表达式（与台账 id 交叉）')
import csv
led = list(csv.DictReader(open(ROOT / 'data/alpha_quality_analysis' / 'SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
led_ids = {r['id'].strip() for r in led if r.get('id')}
hit = [r for r in recs if r['id'] in led_ids]
L.append(f'   台账 {len(led_ids)} 个 id，在 mined 中匹配到 {len(hit)} 条记录的表达式')
for r in hit[:15]:
    L.append(f'   {r["cid"]:10} {r["id"]:10} SF={r["SF"]:.2f} tS={r["tS"]}  {r["expr"][:90]}')

(ROOT / '_autologs' / 'expr_struct.txt').write_text('\n'.join(L), encoding='utf-8')
print('OK')
