# -*- coding: utf-8 -*-
"""升级路径分析：同骨架下 A 档 vs E 档差在哪；D 档(3.0-4.0)"差一点"的候选；py_only 未跑过的思路"""
import json, re, collections, statistics, csv
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
d = json.load(open(ROOT / '_autologs' / 'expr_all.json', encoding='utf-8'))
recs = d['records']
ops = {o['name'] for o in json.load(open(ROOT / 'data/alpha_quality_analysis' / 'operators.json', encoding='utf-8'))}
led = list(csv.DictReader(open(ROOT / 'data/alpha_quality_analysis' / 'SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
led_ids = {r['id'].strip() for r in led if r.get('id')}

L = []
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

def core(e):
    """去掉 group_rank(...) 外壳，取核心数学式"""
    return re.sub(r'\s+', ' ', e).strip()

def band(r):
    sf = (r['S'] or 0) + (r['F'] or 0)
    if sf >= 5.5 and not r['fails']: return 'A'
    if sf >= 5.0 and not r['fails']: return 'B'
    if sf >= 4.0 and not r['fails']: return 'C'
    if sf >= 3.0: return 'D'
    return 'E'

def sig(r):
    return tuple(sorted({f for f in re.findall(r'\b([a-z][a-z0-9_]{4,})\b', r['expr'])  if f not in ops}))

# ---------- 1. 同一腿（单条腿的核）在不同档的表现 ----------
L.append('=' * 74)
L.append('一、单腿复用价值：每条腿出现在多少条全过记录里')
L.append('=' * 74)
legcnt = collections.Counter(); legok = collections.Counter()
for r in recs:
    for lg in legs(r['expr']):
        key = core(lg)[:110]
        legcnt[key] += 1
        if band(r) in 'ABC': legok[key] += 1
L.append(f'{"腿表达式":<112} {"出现":>4} {"全过":>4} {"率":>6}')
for k, v in legcnt.most_common(28):
    L.append(f'{k:<112} {v:>4} {legok.get(k,0):>4} {legok.get(k,0)/v*100:>5.1f}%')
L.append('')

# ---------- 2. D 档"差一点"的候选 ----------
L.append('=' * 74)
L.append('二、D 档（SF 3.0-4.0）"差一点"的候选 top25 —— 最值得捡回的历史资产')
L.append('=' * 74)
Ds = [r for r in recs if band(r) == 'D']
Ds.sort(key=lambda r: -r['SF'])
L.append(f'{"cid":10} {"id":10} {"S":>5} {"F":>5} {"SF":>5} {"T":>7} {"tS":>5} 腿 FAIL')
for r in Ds[:25]:
    L.append(f'{r["cid"]:10} {str(r["id"]):10} {r["S"]:5.2f} {r["F"]:5.2f} {r["SF"]:5.2f} {r["T"]:7.4f} {str(r["tS"]):>5} {len(legs(r["expr"])):>2} {",".join(r["fails"])[:26]}')
L.append('')
L.append('   D 档腿数分布: ' + str(dict(sorted(collections.Counter(len(legs(r["expr"])) for r in Ds).items()))))
L.append(f'   D 档中 tS>=1.25 的有 {len([r for r in Ds if (r["tS"] or 0)>=1.25])} 条（验证期稳定，只差 IS 分数）')
L.append(f'   D 档中 无FAIL 的有 {len([r for r in Ds if not r["fails"]])} 条（只差分数不够）')
L.append('')

# ---------- 3. 同骨架 A vs E 逐条对照 ----------
L.append('=' * 74)
L.append('三、同一字段组合下 A 档 vs E 档 的表达式差异（升级动作实证）')
L.append('=' * 74)
groups = collections.defaultdict(list)
for r in recs:
    groups[sig(r)].append(r)
shown = 0
for s, rs in sorted(groups.items(), key=lambda kv: -len(kv[1])):
    A = [r for r in rs if band(r) == 'A']
    E = [r for r in rs if band(r) == 'E']
    if not A or not E or len(s) < 2:
        continue
    shown += 1
    if shown > 6: break
    L.append(f'--- 骨架 {", ".join(s)[:120]}  (n={len(rs)}  A={len(A)} E={len(E)})')
    for tag, rs2 in (('A最好', sorted(A, key=lambda r: -r['SF'])[:1]), ('E最差', sorted(E, key=lambda r: r['SF'])[:1])):
        r = rs2[0]
        L.append(f'   [{tag}] {r["cid"]} SF={r["SF"]:.2f} tS={r["tS"]} T={r["T"]:.4f} 腿={len(legs(r["expr"]))}')
        L.append(f'      {core(r["expr"])[:400]}')
    # A 档多出的腿
    a_legs = {core(l)[:60] for l in legs(A[0]['expr'])}
    e_legs = {core(l)[:60] for l in legs(E[0]['expr'])}
    L.append(f'   A 有而 E 没有的腿: {sorted(a_legs - e_legs)[:3]}')
    L.append('')

# ---------- 4. py_only ----------
L.append('=' * 74)
L.append('四、脚本独有（mined 未覆盖）表达式 %d 条 —— 抽样' % len(d['py_only']))
L.append('=' * 74)
po = d['py_only']
kind = collections.Counter()
for e in po:
    if 'news' in e or 'snt' in e: kind['news/sentiment'] += 1
    elif 'anl4' in e: kind['analyst4'] += 1
    elif 'fnd' in e: kind['fundamental'] += 1
    elif 'option' in e: kind['option'] += 1
    elif 'model' in e or 'mdf' in e: kind['model'] += 1
    else: kind['pv/其他'] += 1
L.append('   类型分布: ' + str(dict(kind.most_common())))
L.append('')
for e in po[:40]:
    L.append('   ' + e[:180])
L.append('')

# ---------- 5. 未提交的优质候选 ----------
L.append('=' * 74)
L.append('五、全过（A/B/C 档）但未出现在台账的候选')
L.append('=' * 74)
abc = [r for r in recs if band(r) in 'ABC']
unsub = [r for r in abc if r['id'] not in led_ids]
L.append(f'   全过 {len(abc)} 条，其中 {len(unsub)} 条未提交（台账 {len(led_ids)} 个 id，匹配 {len([r for r in abc if r["id"] in led_ids])} 条）')
L.append(f'   未提交者 SF 中位={statistics.median([r["SF"] for r in unsub]):.2f}，tS 中位={statistics.median([r["tS"] for r in unsub if r["tS"] is not None]):.2f}')
L.append('')
L.append('   按 cid 前缀分组（未提交的全过候选）:')
c = collections.Counter(r['cid'].split('_')[0] for r in unsub)
L.append('   ' + ', '.join(f'{a}:{b}' for a, b in sorted(c.items(), key=lambda x: -x[1])[:30]))
L.append('')
L.append('   最强 20 条未提交候选:')
for r in sorted(unsub, key=lambda r: -r['SF'])[:20]:
    L.append(f'   {r["cid"]:10} {str(r["id"]):10} SF={r["SF"]:.2f} tS={str(r["tS"]):>5} T={r["T"]:.4f}  {r["expr"][:110]}')

(ROOT / '_autologs' / 'upgrade_path.txt').write_text('\n'.join(L), encoding='utf-8')
print('OK')
