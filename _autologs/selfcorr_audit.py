# -*- coding: utf-8 -*-
"""selfcorr_audit.py —— 按官方评分算法审计已提交 alpha 的质量因子漏点（自写 UTF-8）
官方 Quality 子因子：Universe(小池加分) / SelfCorrelation(越低越好) / Fitness(越高越好) / Delay(D1>D0)
"""
import io, csv, collections

ROOT = 'D:/Python/worldquant/'
raw = io.open(ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', 'rb').read().decode('utf-8-sig')
rows = list(csv.reader(io.StringIO(raw)))
data = [r for r in rows[1:] if r and r[0].strip()]

seen = {}
for r in data:
    try:
        seen.setdefault(r[0], dict(id=r[0], S=float(r[2]), F=float(r[3]), T=float(r[4]),
                                   sc=float(r[7]) if r[7] not in ('', None) else None,
                                   decay=r[9], neut=r[10], batch=r[11] if len(r) > 11 else ''))
    except Exception:
        pass

L = []
L.append('唯一 id: %d' % len(seen))
L.append('')
L.append('== SelfCorrelation 分布（官方：越低越好）==')
bands = [('sc<0.10 极低', 0, 0.10), ('0.10~0.40', 0.10, 0.40), ('0.40~0.60', 0.40, 0.60),
         ('0.60~0.70 临界', 0.60, 0.70), ('0.70~0.80 差', 0.70, 0.80), ('>=0.80 很差', 0.80, 1.01)]
tot = len(seen)
for name, lo, hi in bands:
    grp = [v for v in seen.values() if v['sc'] is not None and lo <= v['sc'] < hi]
    if grp:
        L.append('  %-14s %3d 条 (%4.1f%%) | 平均 S=%.2f | 平均 F=%.2f'
                 % (name, len(grp), len(grp) / tot * 100,
                    sum(x['S'] for x in grp) / len(grp), sum(x['F'] for x in grp) / len(grp)))
    else:
        L.append('  %-14s 0 条' % name)
nosc = [v for v in seen.values() if v['sc'] is None or v['sc'] == 0]
L.append('  无 selfCorr 记录: %d 条' % len(nosc))
scs = [v['sc'] for v in seen.values() if v['sc']]
L.append('  有记录 %d 条，均值 %.3f，中位 %.3f' % (len(scs), sum(scs) / len(scs), sorted(scs)[len(scs) // 2]))

L.append('')
L.append('== selfCorr≥0.70 的清单（这批按官方算法直接拖 Quality 均值）==')
bad = sorted([v for v in seen.values() if v['sc'] and v['sc'] >= 0.70], key=lambda z: -z['sc'])
L.append('  共 %d 条' % len(bad))
L.append('  %-11s %6s %6s %8s %8s %s' % ('id', 'S', 'F', 'selfCorr', 'TO', 'batch'))
for v in bad:
    L.append('  %-11s %6.2f %6.2f %8.4f %7.1f%% %s'
             % (v['id'], v['S'], v['F'], v['sc'], v['T'] * 100, v['batch'][:44]))

L.append('')
L.append('== 按 Fitness 排序：已提交 alpha 的质量分层 ==')
L.append('  F>=3.0: %d 条' % sum(1 for v in seen.values() if v['F'] >= 3.0))
L.append('  2.5~3.0: %d 条' % sum(1 for v in seen.values() if 2.5 <= v['F'] < 3.0))
L.append('  2.0~2.5: %d 条' % sum(1 for v in seen.values() if 2.0 <= v['F'] < 2.5))
L.append('  1.5~2.0: %d 条' % sum(1 for v in seen.values() if 1.5 <= v['F'] < 2.0))
L.append('  F<1.5:  %d 条' % sum(1 for v in seen.values() if v['F'] < 1.5))
L.append('  平均 F = %.3f' % (sum(v['F'] for v in seen.values()) / len(seen)))

L.append('')
L.append('== 低 Fitness + 高 selfCorr 双差清单（最该被"优化替换"的）==')
worst = sorted(seen.values(), key=lambda z: (z['F'] - (z['sc'] or 0) * 2))[:20]
L.append('  %-11s %6s %6s %8s %s' % ('id', 'S', 'F', 'selfCorr', 'batch'))
for v in worst:
    L.append('  %-11s %6.2f %6.2f %8s %s'
             % (v['id'], v['S'], v['F'], ('%.4f' % v['sc']) if v['sc'] else '-', v['batch'][:46]))

io.open(ROOT + '_autologs/_selfcorr_audit.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
