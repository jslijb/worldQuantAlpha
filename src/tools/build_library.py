# -*- coding: utf-8 -*-
"""建立目录框架 + 生成表达式库（历史脚本删除前的完整经验留存）"""
import json, re, csv, collections, statistics
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')

# ---------------- 1. 建目录骨架 ----------------
DIRS = [
    'src/core', 'src/submit', 'src/mine', 'src/ops',
    'src/archive/mining', 'src/archive/submit', 'src/archive/hunt',
    'src/archive/checks', 'src/archive/tests', 'src/archive/tools',
    'data/data/alpha_quality_analysis',
    'docs/methodology/01_骨架与配方', 'docs/methodology/02_参数与设置',
    'docs/methodology/03_过墙与提交', 'docs/methodology/04_失败模式',
    'docs/methodology/05_历史因子复盘',
    'docs/research', 'docs/study', 'docs/exam', 'docs/project',
    'docs/reference', 'docs/archive',
]
for p in DIRS:
    (ROOT / p).mkdir(parents=True, exist_ok=True)
print('目录骨架建立:', len(DIRS))

# ---------------- 2. 读提取结果 ----------------
d = json.load(open(ROOT / '_autologs' / 'expr_all.json', encoding='utf-8'))
recs = d['records']
py_only = d['py_only']
ops = {o['name'] for o in json.load(open(ROOT / 'data/alpha_quality_analysis' / 'operators.json', encoding='utf-8'))}
led = list(csv.DictReader(open(ROOT / 'data/alpha_quality_analysis' / 'SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
led_ids = {r['id'].strip() for r in led if r.get('id')}

def band(r):
    sf = (r['S'] or 0) + (r['F'] or 0)
    if sf >= 5.5 and not r['fails']: return 'A'
    if sf >= 5.0 and not r['fails']: return 'B'
    if sf >= 4.0 and not r['fails']: return 'C'
    if sf >= 3.0: return 'D'
    return 'E'

def legs(e):
    out, dep, cur = [], 0, ''
    for ch in e:
        if ch == '(': dep += 1
        elif ch == ')': dep -= 1
        if ch == '+' and dep == 0:
            out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return [x for x in out if x]

# 过滤 py_only 里的模板碎片 / 代码片段
def is_real_expr(s):
    if any(t in s for t in ('{GS(', '{GI_', 'row[', 'done.add', 'ids.add', 'SELECT', 'http', 'print(')):
        return False
    if s.count('(') != s.count(')'): return False
    if len(s) < 18: return False
    if not any(o + '(' in s for o in ops): return False
    return True

py_real = sorted({s for s in py_only if is_real_expr(s)})
py_notes = sorted({s for s in py_only if not is_real_expr(s) and len(s) > 30})

# ---------------- 3. 生成表达式库 ----------------
uniq = {}
for r in recs:
    uniq.setdefault(r['expr'], []).append(r)

legcnt, legok = collections.Counter(), collections.Counter()
for r in recs:
    for lg in legs(r['expr']):
        k = re.sub(r'\s+', ' ', lg).strip()
        legcnt[k] += 1
        if band(r) in 'ABC': legok[k] += 1

L = []
L.append('# -*- coding: utf-8 -*-')
L.append('"""历史 Alpha 表达式库 —— 自动生成，请勿手改')
L.append('')
L.append('来源: 411 个历史 .py 脚本 + 1098 条 mined 模拟记录')
L.append('生成: 2026-09-15  (历史脚本已提取经验后删除，本文件是其完整留存)')
L.append('')
L.append(f'内容:  ALL_EXPR {len(recs)} 条(含重复) / UNIQUE_EXPR {len(uniq)} 条 / LEG_VALUE {len(legcnt)} 条腿 / PY_ONLY {len(py_real)} 条未跑过')
L.append('指标:  S=IS Sharpe  F=IS Fitness  T=turnover  tS=验证期Sharpe  FAIL=未通过检查')
L.append('"""')
L.append('')
L.append('# 单腿价值排行: (腿表达式, 出现次数, 全过次数, 全过率)')
L.append('LEG_VALUE = [')
for k, v in legcnt.most_common():
    if v >= 3:
        ok = legok.get(k, 0)
        L.append('    (%r, %d, %d, %.3f),' % (k, v, ok, ok / v))
L.append(']')
L.append('')
L.append('# 全部模拟过的表达式: (表达式, S, F, T, tS, FAIL串)')
L.append('ALL_EXPR = [')
for r in sorted(recs, key=lambda x: -(x['SF'] or 0)):
    L.append('    (%r, %s, %s, %s, %s, %r),' % (r['expr'], r['S'], r['F'], r['T'], r['tS'], ','.join(r['fails'])))
L.append(']')
L.append('')
L.append('# 三关全过(SF>=4.0 & tS>=1.25 & 无FAIL) 的表达式')
L.append('QUALIFIED = [e for e in ALL_EXPR if e[1] is not None and e[2] is not None and e[1]+e[2] >= 4.0 and e[4] is not None and e[4] >= 1.25 and not e[5]]')
L.append('')
L.append('# 脚本里出现但从未模拟过的表达式（1442 条中过滤掉模板碎片后的真表达式）')
L.append('PY_ONLY = [')
for e in py_real:
    L.append('    %r,' % e)
L.append(']')
L.append('')
L.append('# 脚本里的模板片段（f-string 骨架，保留备查）')
L.append('PY_TEMPLATE_NOTES = [')
for e in py_notes[:400]:
    L.append('    %r,' % e)
L.append(']')
L.append('')
(ROOT / 'src' / 'archive' / 'expr_library.py').write_text('\n'.join(L), encoding='utf-8')

# ---------------- 4. CSV 清单 ----------------
head = ['cid', 'id', 'S', 'F', 'SF', 'T', 'R', 'DD', 'tS', 'band', 'fails', 'grade',
        'universe', 'neutralization', 'decay', 'truncation', 'delay', 'submitted', 'expr']
def row(r):
    s = r['settings'] or {}
    return [r['cid'], r['id'], r['S'], r['F'], r['SF'], r['T'], r['R'], r['DD'], r['tS'], band(r),
            ','.join(r['fails']), r['grade'], s.get('universe'), s.get('neutralization'),
            s.get('decay'), s.get('truncation'), s.get('delay'),
            'Y' if r['id'] in led_ids else 'N', r['expr']]

out = ROOT / 'data' / 'data/alpha_quality_analysis'
with open(out / 'candidates_all.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(head)
    for r in sorted(recs, key=lambda x: -(x['SF'] or 0)): w.writerow(row(r))

with open(out / 'candidates_unsubmitted_qualified.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(head)
    n = 0
    for r in sorted(recs, key=lambda x: -(x['SF'] or 0)):
        if band(r) in 'ABC' and r['id'] not in led_ids:
            w.writerow(row(r)); n += 1
    print('未提交优质候选:', n)

with open(out / 'leg_value_rank.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f); w.writerow(['leg', 'appear', 'pass_quality', 'pass_rate'])
    for k, v in legcnt.most_common():
        w.writerow([k, v, legok.get(k, 0), round(legok.get(k, 0) / v, 4)])

print('docx: expr_library.py %d 行' % len(L))
print('py_real(未跑过真表达式):', len(py_real), ' py_notes(模板):', len(py_notes))
