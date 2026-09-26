# -*- coding: utf-8 -*-
"""ledger_analyze.py —— 台账体检：按换手率分组，找出"漏钱"的已提交因子（自写 UTF-8）"""
import io, csv, json

ROOT = 'D:/Python/worldquant/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
raw = io.open(LED, 'rb').read().decode('utf-8-sig')
rows = list(csv.reader(io.StringIO(raw)))
hdr = rows[0]
data = [r for r in rows[1:] if r and r[0].strip()]

recs = []
for r in data:
    try:
        recs.append(dict(id=r[0], expr=r[1], S=float(r[2]), F=float(r[3]), T=float(r[4]),
                         R=float(r[5]), DD=float(r[6]),
                         sc=float(r[7]) if r[7] not in ('', None) else None,
                         date=r[8], decay=r[9], neut=r[10],
                         batch=r[11] if len(r) > 11 else ''))
    except Exception:
        pass

L = []
L.append('台账数据行: %d （去重前）' % len(data))
seen = {}
for r in recs:
    seen.setdefault(r['id'], r)
L.append('唯一 id: %d' % len(seen))

def margin(r):
    # margin(bp) ≈ 日收益/日换手 ≈ R/(T*252) *1e4  （粗略，仅排序用）
    return r['R'] / max(r['T'], 1e-9) * 1e4 / 252

bands = {'TO<10%': [], '10~15%': [], '15~20%': [], '20~30%': [], 'TO>30%': []}
for r in seen.values():
    t = r['T']
    if t < 0.10: bands['TO<10%'].append(r)
    elif t < 0.15: bands['10~15%'].append(r)
    elif t < 0.20: bands['15~20%'].append(r)
    elif t < 0.30: bands['20~30%'].append(r)
    else: bands['TO>30%'].append(r)

L.append('')
L.append('== 换手率分布 ==')
for k, v in bands.items():
    if not v:
        L.append('  %-8s : 0' % k); continue
    L.append('  %-8s : %3d 条 | 平均 S=%.2f | 平均 margin≈%.1fbp'
             % (k, len(v), sum(x['S'] for x in v) / len(v),
                sum(margin(x) for x in v) / len(v)))

L.append('')
L.append('== 漏钱最狠：换手率 Top 20（按 TO 降序）==')
L.append('  %-11s %6s %6s %7s %8s %8s %14s %s' % ('id', 'S', 'F', 'TO', 'margin', 'DD', 'neut', 'batch'))
for r in sorted(seen.values(), key=lambda z: -z['T'])[:20]:
    L.append('  %-11s %6.2f %6.2f %6.1f%% %6.1fbp %7.2f%% %14s %s'
             % (r['id'], r['S'], r['F'], r['T'] * 100, margin(r), r['DD'] * 100, r['neut'], r['batch'][:46]))

L.append('')
L.append('== 质量最差：S+F 最低的 15 条（拖排名的）==')
for r in sorted(seen.values(), key=lambda z: z['S'] + z['F'])[:15]:
    L.append('  %-11s S=%5.2f F=%5.2f SF=%5.2f TO=%5.1f%% margin=%5.1fbp %s'
             % (r['id'], r['S'], r['F'], r['S'] + r['F'], r['T'] * 100, margin(r), r['batch'][:44]))

L.append('')
L.append('== 最强 15 条（做参照模板用）==')
for r in sorted(seen.values(), key=lambda z: -(z['S'] + z['F']))[:15]:
    L.append('  %-11s S=%5.2f F=%5.2f SF=%5.2f TO=%5.1f%% margin=%5.1fbp %s'
             % (r['id'], r['S'], r['F'], r['S'] + r['F'], r['T'] * 100, margin(r), r['batch'][:44]))

io.open(ROOT + '_autologs/_ledger_report.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
