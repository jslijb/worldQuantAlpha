# -*- coding: utf-8 -*-
"""pick_by_F.py —— 按"排名导向 + 低换手"挑未提交候选

依据（0920 实证）：
  · Fitness = S × sqrt(|R| / max(TO, 0.125))（已用 pwRwWoJ3 校验）
  · 官方 Quality 四子项里有 Fitness，没有 turnover；turnover 只经 Fitness 进入，
    且 Fitness 的换手分母有 0.125 地板 → **TO ≤ 12.5% 再降无收益**
  · 实测 TO>0.35 那批 S=2.743 却 F=1.622；TO≤0.125 那批 S=2.173 但 F=1.990
  → 出矿目标是「F 优先 + TO 落在 0.09~0.14」，不是「S 优先 + TO≤0.20」

本脚本扫 mined 全库：过闸（S+F≥4、tS≥1.25、无 FAIL、F≥1.8）且未在台账，
按 F 排序输出。用途：判决器说 corr 不够时，至少知道"该压换手的目标长什么样"。
输出 _autologs/_pickF.txt
"""
import io, os, csv, json, math

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

sub = set()
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if r and r[0].strip():
            sub.add(r[0].strip())

cands = []
for x in os.listdir(MINED):
    if not x.endswith('.json'):
        continue
    try:
        d = json.load(io.open(MINED + x, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid or aid in sub:
        continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    TO = i.get('turnover') or 0; R = i.get('returns') or 0
    tS = t.get('sharpe') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < 4.0 or tS < 1.25 or fa or F < 1.8:
        continue
    cands.append(dict(aid=aid, cid=d.get('_cid') or x[:-5], S=S, F=F, TO=TO, R=R, tS=tS,
                      Fi=S * math.sqrt(abs(R) / max(TO, 0.125)) if R else 0))

L = ['未提交 + 过闸候选 %d 条' % len(cands)]
L.append('')
L.append('== A. 直通带：TO ∈ [0.09, 0.14]（Fitness 地板区，再降无收益）按 F 排序 ==')
a = sorted([c for c in cands if 0.09 <= c['TO'] <= 0.14], key=lambda c: -c['F'])
for c in a[:25]:
    L.append('  %-10s %-28s S=%5.2f F=%5.2f TO=%.3f R=%.4f tS=%4.2f'
             % (c['aid'], c['cid'], c['S'], c['F'], c['TO'], c['R'], c['tS']))
L.append('  共 %d 条' % len(a))

L.append('')
L.append('== B. 全库按 F 排序 Top 30（不管 TO）==')
for c in sorted(cands, key=lambda c: -c['F'])[:30]:
    L.append('  %-10s %-28s S=%5.2f F=%5.2f(降TO后可达%5.2f) TO=%.3f tS=%4.2f'
             % (c['aid'], c['cid'], c['S'], c['F'], c['Fi'], c['TO'], c['tS']))

L.append('')
L.append('== C. 质量分布（过闸候选）==')
import statistics as st
for k, f in (('S', lambda c: c['S']), ('F', lambda c: c['F']), ('TO', lambda c: c['TO']), ('tS', lambda c: c['tS'])):
    v = sorted(f(c) for c in cands)
    L.append('  %-4s 中位 %.3f 均值 %.3f p90 %.3f max %.3f' % (k, v[len(v)//2], st.mean(v), v[int(len(v)*0.9)], v[-1]))

io.open(ROOT + '_autologs/_pickF.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok %d' % len(cands))
