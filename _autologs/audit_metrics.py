# -*- coding: utf-8 -*-
"""拉取已提交 alpha 的全维度指标，按 turnover / sharpe 分档，找优化靶子。"""
import json, io, sys, statistics as st
import requests

_RPT = io.open('_autologs/audit_metrics_report.txt', 'w', encoding='utf-8')


class _T:
    def write(self, s):
        _RPT.write(s)

    def flush(self):
        _RPT.flush()


sys.stdout = _T()

S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

rows, off = [], 0
while len(rows) < 400:
    r = S.get('https://api.worldquantbrain.com/users/self/alphas',
              params={'limit': 100, 'offset': off, 'order': '-dateSubmitted'})
    try:
        j = r.json()
    except Exception as e:
        io.open('_autologs/audit_metrics.err', 'w', encoding='utf-8').write('json fail off=%d %s' % (off, e))
        break
    if isinstance(j, list):
        io.open('_autologs/audit_metrics.err', 'w', encoding='utf-8').write(
            'list at off=%d len=%d sample=%r' % (off, len(j), j[:2]))
        break
    res = j.get('results') or []
    if not res:
        break
    rows += res
    off += len(res)
    if off >= j.get('count', 0):
        break

sub = [a for a in rows if a.get('dateSubmitted')]
ACT = [a for a in sub if a.get('status') == 'ACTIVE']
print('total alphas fetched:', len(rows))
print('with dateSubmitted  :', len(sub))
print('ACTIVE              :', len(ACT))


def g(a, k, d=None):
    v = (a.get('is') or {}).get(k)
    return d if v is None else v


recs = []
for a in ACT:
    recs.append(dict(
        id=a['id'],
        s=g(a, 'sharpe', 0.0), f=g(a, 'fitness', 0.0),
        ts=((a.get('test') or {}).get('sharpe') or 0.0),
        to=g(a, 'turnover', 0.0), ret=g(a, 'returns', 0.0),
        dd=g(a, 'drawdown', 0.0), margin=g(a, 'margin', 0.0),
        grade=a.get('grade') or '-',
        date=(a.get('dateSubmitted') or '')[:19],
    ))

recs.sort(key=lambda x: -x['s'])
print()
print('=== 全部 ACTIVE 按 Sharpe 降序 ===')
print(f"{'id':<10}{'S':>7}{'F':>7}{'tS':>7}{'TO%':>8}{'ret%':>7}{'DD%':>7}{'margin':>9}  grade")
for x in recs:
    print(f"{x['id']:<10}{x['s']:>7.2f}{x['f']:>7.2f}{x['ts']:>7.2f}"
          f"{x['to']*100:>8.2f}{x['ret']*100:>7.2f}{x['dd']*100:>7.2f}{x['margin']*1e4:>9.2f}  {x['grade']}")

to = [x['to'] for x in recs if x['to'] > 0]
sf = [x['s'] + x['f'] for x in recs]


def q(v, p):
    v = sorted(v)
    i = min(len(v) - 1, max(0, int(len(v) * p)))
    return v[i]


print()
print('=== 分布 ===')
print(f"n={len(recs)}")
print(f"turnover  中位 {q(to,0.5)*100:.2f}%  Q1 {q(to,0.25)*100:.2f}%  Q3 {q(to,0.75)*100:.2f}%  max {max(to)*100:.2f}%  min {min(to)*100:.2f}%")
print(f"S+F       中位 {q(sf,0.5):.2f}  mean {st.mean(sf):.2f}  合计 {sum(sf):.1f}")
print(f"Sharpe    中位 {q([x['s'] for x in recs],0.5):.2f}  mean {st.mean([x['s'] for x in recs]):.2f}")
print(f"Fitness   中位 {q([x['f'] for x in recs],0.5):.2f}")

buckets = [(0, .10, 'TO<10% 呆滞'), (.10, .15, 'TO 10-15% 甜点偏慢'), (.15, .20, 'TO 15-20% 甜点'),
           (.20, .30, 'TO 20-30% 偏高'), (.30, .50, 'TO 30-50% 过高'), (.50, 9, 'TO>50% 失控')]
print()
print('=== turnover 分档 ===')
for lo, hi, name in buckets:
    grp = [x for x in recs if lo <= x['to'] < hi]
    if not grp:
        continue
    print(f"{name:<22} n={len(grp):>3}  平均S={st.mean([x['s'] for x in grp]):.2f}"
          f"  平均F={st.mean([x['f'] for x in grp]):.2f}  平均S+F={st.mean([x['s']+x['f'] for x in grp]):.2f}"
          f"  平均tS={st.mean([x['ts'] for x in grp]):.2f}")

print()
print('=== 优化靶子：turnover>20% 或 S<2.0 ===')
bad = [x for x in recs if x['to'] > 0.20 or x['s'] < 2.0]
bad.sort(key=lambda x: x['to'], reverse=True)
print(f"共 {len(bad)} 条 / {len(recs)}")
for x in bad:
    tag = []
    if x['to'] > 0.20:
        tag.append('高换手')
    if x['s'] < 2.0:
        tag.append('低夏普')
    if x['f'] < 1.0:
        tag.append('低fitness')
    print(f"  {x['id']:<10} S={x['s']:.2f} F={x['f']:.2f} TO={x['to']*100:6.2f}%  {'/'.join(tag)}")

io.open('_autologs/audit_metrics.out', 'w', encoding='utf-8').write(
    '\n'.join(f"{x['id']} {x['s']:.3f} {x['f']:.3f} {x['ts']:.3f} {x['to']:.4f} {x['ret']:.4f} {x['dd']:.4f} {x['margin']:.6f} {x['grade']}" for x in recs))
print()
print('written -> _autologs/audit_metrics.out')
