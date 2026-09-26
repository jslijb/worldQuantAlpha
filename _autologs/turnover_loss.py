# -*- coding: utf-8 -*-
"""turnover_loss.py —— 量化"高换手吃掉多少 Fitness"

BRAIN Fitness 定义（已用 pwRwWoJ3 校验：
  3.33 × sqrt(0.1445 / max(0.1207,0.125)) = 3.33 × 1.0752 = 3.58 == 台账 F=3.58）：
    Fitness = Sharpe × sqrt( |Returns| / max(Turnover, 0.125) )
→ turnover 有 **0.125 地板**：TO ≤ 12.5% 时，再降换手**不涨 Fitness**；
   TO > 12.5% 时，每多 1 个点都在 F 上按 sqrt 比例打折。

本脚本：对台账逐条算
  F_ideal = S × sqrt(|R| / 0.125)      （把 TO 压到地板时能拿到的 Fitness）
  F_loss  = F_ideal - F_actual          （换手造成的 Fitness 损失）
输出按损失排序的名单 + 分带统计。输出 _autologs/_to_loss.txt
"""
import io, csv, math, statistics as st

ROOT = 'D:/Python/worldquant/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

rows = []
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f)
    hdr = next(rd)
    for r in rd:
        if r and r[0].strip():
            rows.append(r)

seen = {}
for r in rows:
    seen.setdefault(r[0].strip(), r)

L = []
L.append('台账 %d 行，唯一 id %d' % (len(rows), len(seen)))
L.append('')

def fnum(v):
    try:
        return float(v)
    except Exception:
        return None

recs = []
for aid, r in seen.items():
    S = fnum(r[2]); F = fnum(r[3]); TO = fnum(r[4]); R = fnum(r[5])
    if None in (S, F, TO, R):
        continue
    F_ideal = S * math.sqrt(abs(R) / 0.125)
    recs.append(dict(aid=aid, S=S, F=F, TO=TO, R=R, Fi=F_ideal, loss=F_ideal - F,
                     batch=r[11] if len(r) > 11 else ''))

L.append('== ① Fitness 损失排行榜（TO 压到 12.5% 地板能捡回多少）==')
recs.sort(key=lambda x: -x['loss'])
L.append('  %-10s %6s %6s %7s %8s %8s %8s  %s' % ('id', 'S', 'F', 'TO', 'R', 'F_ideal', '损失', '批次'))
for x in recs[:25]:
    L.append('  %-10s %6.2f %6.2f %7.3f %8.4f %8.2f %8.2f  %s'
             % (x['aid'], x['S'], x['F'], x['TO'], x['R'], x['Fi'], x['loss'], x['batch'][-26:]))

L.append('')
L.append('== ② 按换手分带（均值）==')
bands = [('TO<=0.125', lambda t: t <= 0.125), ('0.125-0.18', lambda t: 0.125 < t <= 0.18),
         ('0.18-0.25', lambda t: 0.18 < t <= 0.25), ('0.25-0.35', lambda t: 0.25 < t <= 0.35),
         ('>0.35', lambda t: t > 0.35)]
L.append('  %-12s %4s %7s %7s %7s %7s %8s' % ('带', 'n', '均值S', '均值F', '均值TO', '均值R', '均值损失'))
for name, fn in bands:
    g = [x for x in recs if fn(x['TO'])]
    if not g:
        continue
    L.append('  %-12s %4d %7.3f %7.3f %7.3f %7.4f %8.3f'
             % (name, len(g), st.mean(x['S'] for x in g), st.mean(x['F'] for x in g),
                st.mean(x['TO'] for x in g), st.mean(x['R'] for x in g), st.mean(x['loss'] for x in g)))

tot_loss = sum(x['loss'] for x in recs)
L.append('')
L.append('池内 Fitness 总损失（相对 TO 全部压到 12.5%%）= %.1f 分' % tot_loss)
L.append('平均每条损失 %.3f 分（当前均值 F=%.3f）' % (tot_loss / len(recs), st.mean(x['F'] for x in recs)))
hi = [x for x in recs if x['TO'] > 0.25]
L.append('TO>25%% 的 %d 条，平均损失 %.3f 分，占全池损失 %.0f%%'
         % (len(hi), st.mean(x['loss'] for x in hi), 100.0 * sum(x['loss'] for x in hi) / tot_loss))

L.append('')
L.append('== ③ 反例：低换手但 S 也低的（说明"压换手"不能靠牺牲信号）==')
low = sorted([x for x in recs if x['TO'] <= 0.125], key=lambda x: x['S'])[:10]
for x in low:
    L.append('  %-10s S=%5.2f F=%5.2f TO=%.3f R=%.4f 损失=%.2f' % (x['aid'], x['S'], x['F'], x['TO'], x['R'], x['loss']))

io.open(ROOT + '_autologs/_to_loss.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok %d' % len(recs))
