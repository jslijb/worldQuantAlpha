# -*- coding: utf-8 -*-
"""盘点未提交达标候选池（只读）"""
import json, glob, csv, os, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

out = []
rows = list(csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
led = {r['id'].strip() for r in rows if r.get('id')}
out.append(f"台账: {len(rows)} 行 / {len(led)} 唯一 id")

fs = sorted(glob.glob('data/alpha_quality_analysis/mined/*.json'))
bypre = collections.defaultdict(lambda: {'tot': 0, 'q': 0, 'unsub': 0, 'best': (0, '')})
allrows = []
for f in fs:
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    cid = d.get('_cid') or os.path.basename(f)[:-5]
    pre = cid.split('_')[0]
    b = d.get('is') or {}
    te = d.get('test') or {}
    S = b.get('sharpe') or 0
    F = b.get('fitness') or 0
    tS = te.get('sharpe')
    fails = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    ok = (S + F) >= 4.0 and (tS is not None and tS >= 1.25) and not fails
    s = bypre[pre]
    s['tot'] += 1
    if ok:
        s['q'] += 1
        if d.get('id') not in led:
            s['unsub'] += 1
            if S > s['best'][0]:
                s['best'] = (S, f"{cid} {d.get('id')} SF={S+F:.2f} tS={tS:.2f} T={b.get('turnover')}")
            allrows.append((pre, cid, d.get('id'), round(S, 2), round(F, 2), round(S + F, 2),
                            round(tS, 2), b.get('turnover')))

out.append('')
out.append(f"{'前缀':8} {'模拟':>5} {'达标':>5} {'未提交达标':>8}  最佳")
tot = 0
for p in sorted(bypre):
    s = bypre[p]
    if s['unsub'] > 0:
        tot += s['unsub']
        out.append(f"{p:8} {s['tot']:5} {s['q']:5} {s['unsub']:8}  {s['best'][1]}")
out.append('')
out.append(f">>> 未提交达标候选合计: {tot}")

# 现有清单文件是否已含新批次
out.append('')
out.append('=== 清单文件是否含 w120/w121 ===')
for fn in ['candidates_all.csv', 'candidates_unsubmitted_qualified.csv']:
    p = 'data/alpha_quality_analysis/' + fn
    if os.path.exists(p):
        c = open(p, encoding='utf-8-sig').read()
        out.append(f"  {fn}: {len(c.splitlines())-1} 行 | w120_: {c.count('w120_')} | w121_: {c.count('w121_')}")

out.append('')
out.append('=== 未提交达标候选全表（按 S+F 降序）===')
allrows.sort(key=lambda x: -x[5])
out.append(f"{'前缀':8} {'cid':10} {'id':10} {'S':>5} {'F':>5} {'S+F':>6} {'tS':>6} {'T':>7}")
for r in allrows:
    t = r[7]
    ts = f"{t:.4f}" if isinstance(t, (int, float)) else str(t)
    out.append(f"{r[0]:8} {r[1]:10} {str(r[2]):10} {r[3]:5.2f} {r[4]:5.2f} {r[5]:6.2f} {r[6]:6.2f} {ts:>7}")

open('_autologs/pool.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:40]))
