# -*- coding: utf-8 -*-
"""历史挖矿经验提取器
来源 A: alpha_quality_analysis/mined/*.json  (1098 个，含完整模拟结果)
来源 B: 所有历史 .py 脚本内嵌的表达式字符串（可能含未跑过的）
产出: _autologs/expr_all.json + _autologs/expr_report.txt
"""
import json, re, glob, os, collections, statistics
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
OUT = ROOT / '_autologs'
mined_dir = ROOT / 'data/alpha_quality_analysis' / 'mined'

ops = {o['name'] for o in json.load(open(ROOT / 'data/alpha_quality_analysis' / 'operators.json', encoding='utf-8'))}
fields_all = set()
try:
    for fp in (ROOT / 'data/alpha_quality_analysis').glob('*field*.json'):
        j = json.load(open(fp, encoding='utf-8'))
        if isinstance(j, list):
            for x in j:
                if isinstance(x, dict) and x.get('id'):
                    fields_all.add(x['id'])
except Exception:
    pass

# ---------------- A. mined json ----------------
records = []
dup = collections.Counter()
for f in sorted(mined_dir.glob('*.json')):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    reg = d.get('regular') or {}
    code = reg.get('code') if isinstance(reg, dict) else (reg if isinstance(reg, str) else '')
    if not code:
        continue
    is_ = d.get('is') or {}
    te = d.get('test') or {}
    st = d.get('settings') or {}
    fails = [c.get('name') for c in (is_.get('checks') or []) if c.get('result') == 'FAIL']
    S, F = is_.get('sharpe'), is_.get('fitness')
    tS = te.get('sharpe')
    sf = round((S or 0) + (F or 0), 2)
    ok = (sf >= 4.0) and (tS is not None and tS >= 1.25) and (not fails)
    dup[code] += 1
    records.append({
        'cid': d.get('_cid') or f.stem, 'id': d.get('id'), 'expr': code,
        'S': S, 'F': F, 'SF': sf, 'T': is_.get('turnover'), 'R': is_.get('returns'),
        'DD': is_.get('drawdown'), 'tS': tS, 'fails': fails, 'grade': d.get('grade'),
        'status': d.get('status'), 'settings': st, 'src': 'mined',
        'datasets': sorted({f2.split('_')[0] for f2 in re.findall(r'\b([a-z][a-z0-9]*_[a-z0-9_]+)\b', code) if f2.split('_')[0] in ('fnd6', 'fnd2', 'fnd28', 'anl4', 'pv1', 'pv13', 'snt', 'news12', 'model51', 'option8', 'mdf', 'oth')}),
    })

uniq_expr = {}
for r in records:
    uniq_expr.setdefault(r['expr'], []).append(r)

# ---------------- B. 历史 py 脚本 ----------------
strlit = re.compile(r'''["']([^"'\n\\]{8,600})["']''')
op_prefix = tuple(o + '(' for o in ops)
py_files = [p for p in ROOT.rglob('*.py') if '_autologs' not in str(p) and 'worldquant_backup' not in str(p)]
py_expr = collections.defaultdict(set)
for p in py_files:
    try:
        src = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    for m in strlit.finditer(src):
        s = m.group(1)
        if any(op in s for op in op_prefix) and '(' in s:
            if not s.strip().startswith(('http', '/', '{', 'select', 'Select')):
                py_expr[str(p.relative_to(ROOT))].add(s.strip())

py_only = set()
for k, v in py_expr.items():
    for s in v:
        if s not in uniq_expr:
            py_only.add(s)

# ---------------- C. 统计报告 ----------------
L = []
L.append('=' * 72)
L.append('历史挖矿经验提取报告')
L.append('=' * 72)
L.append(f'A. mined json: {len(list(mined_dir.glob("*.json")))} 个文件, 有效记录 {len(records)} 条')
L.append(f'   唯一表达式: {len(uniq_expr)} 条   重复(同式多跑): {sum(1 for k,v in dup.items() if v>1)} 条')
L.append(f'B. 历史 py 脚本: {len(py_files)} 个, 从中抽出表达式串 {sum(len(v) for v in py_expr.values())} 个')
L.append(f'   py 独有(mined 未覆盖)表达式: {len(py_only)} 条')
L.append('')

# 达标
ok_recs = [r for r in records if r['SF'] >= 4.0 and r['tS'] is not None and r['tS'] >= 1.25 and not r['fails']]
q_recs = [r for r in records if r['SF'] >= 4.0]
L.append(f'C. 质量门槛: SF>=4.0 的 {len(q_recs)} 条 ({len(q_recs)/max(len(records),1)*100:.1f}%)')
L.append(f'   三关全过(SF>=4.0 & tS>=1.25 & 无FAIL): {len(ok_recs)} 条 ({len(ok_recs)/max(len(records),1)*100:.1f}%)')
L.append('')

# 数据集
ds = collections.Counter()
ds_ok = collections.Counter()
for r in records:
    for x in r['datasets']:
        ds[x] += 1
        if r in ok_recs: ds_ok[x] += 1
L.append('D. 按数据集统计（出现次数 / 其中三关全过）')
for k, v in ds.most_common(20):
    L.append(f'   {k:10} {v:5}   全过 {ds_ok.get(k,0)}')
L.append('')

# 算子
opc = collections.Counter()
opc_ok = collections.Counter()
for r in records:
    e = r['expr']
    for o in ops:
        if o + '(' in e:
            opc[o] += 1
            if r in ok_recs: opc_ok[o] += 1
L.append('E. 按算子统计 top30（使用次数 / 全过率）')
for k, v in opc.most_common(30):
    L.append(f'   {k:20} {v:5}   全过 {opc_ok.get(k,0):3}  ({opc_ok.get(k,0)/v*100:4.1f}%)')
L.append('')

# settings
for key in ('universe', 'neutralization', 'region', 'delay', 'decay', 'truncation', 'nanHandling', 'instrumentType'):
    c = collections.Counter((r['settings'] or {}).get(key) for r in records)
    L.append(f'F. setting {key}: {dict(c.most_common(8))}')
L.append('')

# checks FAIL
failc = collections.Counter()
for r in records:
    for x in r['fails']:
        failc[x] += 1
L.append('G. checks FAIL 分布')
for k, v in failc.most_common(20):
    L.append(f'   {k:38} {v}')
L.append('')

# turnover / testS
tvs = [r['T'] for r in records if r['T']]
if tvs:
    L.append(f'H. turnover: n={len(tvs)} 中位={statistics.median(tvs):.4f} 均值={statistics.mean(tvs):.4f} min={min(tvs):.4f} max={max(tvs):.4f}')
tss = [r['tS'] for r in records if r['tS'] is not None]
if tss:
    L.append(f'   testS:     n={len(tss)} 中位={statistics.median(tss):.4f} 均值={statistics.mean(tss):.4f} min={min(tss):.4f} max={max(tss):.4f}')
ss = [r['S'] for r in records if r['S'] is not None]
if ss:
    L.append(f'   IS Sharpe: n={len(ss)} 中位={statistics.median(ss):.4f} 均值={statistics.mean(ss):.4f} min={min(ss):.4f} max={max(ss):.4f}')
L.append('')

# top
L.append('I. 三关全过 优中选优（按 SF 降序 top 40）')
L.append(f'   {"cid":10} {"id":10} {"S":>6} {"F":>6} {"SF":>6} {"T":>8} {"tS":>6}')
top = sorted(ok_recs, key=lambda r: -r['SF'])
for r in top[:40]:
    L.append(f'   {r["cid"]:10} {str(r["id"]):10} {r["S"]:6.2f} {r["F"]:6.2f} {r["SF"]:6.2f} {str(r["T"]):>8} {str(r["tS"]):>6}')
L.append('')

# 已提交的
L.append('J. 已提交(status=ACTIVE)且 SF>=4.0 的配方（供"是否可优化"参考）')
act = [r for r in records if (r.get('status') or '') == 'ACTIVE' and r['SF'] >= 4.0]
for r in sorted(act, key=lambda x: -x['SF'])[:30]:
    L.append(f'   {r["cid"]:10} {str(r["id"]):10} SF={r["SF"]:.2f} tS={r["tS"]}')
L.append(f'   (共 {len(act)} 条)')
L.append('')

(OUT / 'expr_report.txt').write_text('\n'.join(L), encoding='utf-8')
json.dump({'records': records, 'uniq_count': len(uniq_expr), 'py_only': sorted(py_only)}, open(OUT / 'expr_all.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('OK  records=%d uniq=%d py_only=%d' % (len(records), len(uniq_expr), len(py_only)))
