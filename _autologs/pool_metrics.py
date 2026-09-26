# -*- coding: utf-8 -*-
"""pool_metrics.py —— 把已入池 113 条的完整指标拉到本地（台账只有 S/F/T/R/DD）

为什么需要它：
  · 台账 `SUBMITTED_LEDGER.csv` 没有 `test.sharpe`（tS）列，导致"tS>=1.25 闸门"到底
    严不严无法核对 —— 若池里有 tS<1.25 甚至负值的 alpha 被平台照收，那这条闸门就是
    自设限流，在"提日分"的目标下应当放宽。
  · 池内指标表也用于后续选靶（need = 1.1 x 对手 S 需要 S 现况）。

产出：data/alpha_quality_analysis/pool_metrics.json
      _autologs/_pool_metrics.txt
用法：python _autologs/pool_metrics.py [--refresh]
"""
import os as _os, io, sys, json, time
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import requests

REFRESH = '--refresh' in sys.argv
LED = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
MF = ROOT / 'data/alpha_quality_analysis/pool_metrics.json'
OUT = io.open(ROOT / '_autologs' / '_pool_metrics.txt', 'w', encoding='utf-8')
def w(s=''):
    OUT.write(str(s) + '\n'); OUT.flush()

pool = []
for ln in io.open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    aid = ln.split(',')[0].strip().strip('"')
    if aid and aid not in pool:
        pool.append(aid)

pm = {}
if MF.exists() and not REFRESH:
    try:
        pm = json.load(io.open(MF, encoding='utf-8'))
    except Exception:
        pm = {}

todo = [a for a in pool if a not in pm or REFRESH]
w('池子 %d 条，需拉取 %d 条' % (len(pool), len(todo)))

if todo:
    sess = requests.Session()
    sess.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
    for _ in range(8):
        try:
            if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                break
        except Exception:
            time.sleep(5)
    for a in todo:
        for att in range(6):
            try:
                j = sess.get(f'https://api.worldquantbrain.com/alphas/{a}', timeout=60).json()
            except Exception:
                time.sleep(3); continue
            if j.get('id'):
                b = j.get('is') or {}; te = j.get('test') or {}; st = j.get('settings') or {}
                pm[a] = dict(S=b.get('sharpe'), F=b.get('fitness'), TO=b.get('turnover'),
                             R=b.get('returns'), DD=b.get('drawdown'), tS=te.get('sharpe'),
                             tF=te.get('fitness'), u=st.get('universe'), dec=st.get('decay'),
                             neu=st.get('neutralization'), dly=st.get('delay'))
                break
            time.sleep(3)
        time.sleep(0.15)
    json.dump(pm, io.open(MF, 'w', encoding='utf-8'), ensure_ascii=False)

rows = [pm[a] for a in pool if pm.get(a)]
ts = [r['tS'] for r in rows if r.get('tS') is not None]
w('')
w('可取到指标 %d 条' % len(rows))
if ts:
    ts_s = sorted(ts)
    w('== tS（测试期夏普）分布 ==')
    w('   均值 %.3f  中位 %.3f  min %.2f  max %.2f'
      % (sum(ts) / len(ts), ts_s[len(ts_s) // 2], ts_s[0], ts_s[-1]))
    for th in (-0.5, 0.0, 0.5, 1.0, 1.25, 1.5, 2.0):
        n = len([x for x in ts if x < th])
        w('   tS < %5.2f : %3d / %d = %3.0f%%' % (th, n, len(ts), 100 * n / len(ts)))
w('')
to = [r['TO'] for r in rows if r.get('TO') is not None]
if to:
    to_s = sorted(to)
    w('== TO 分布：均值 %.4f 中位 %.4f max %.4f ==' % (sum(to) / len(to), to_s[len(to_s) // 2], to_s[-1]))
    for th in (0.15, 0.20, 0.30, 0.50):
        n = len([x for x in to if x > th])
        w('   TO > %.2f : %3d / %d = %3.0f%%' % (th, n, len(to), 100 * n / len(to)))
w('')
F = [r['F'] for r in rows if r.get('F') is not None]
w('== F 分布：均值 %.3f 中位 %.3f max %.2f ==' % (sum(F) / len(F), sorted(F)[len(F) // 2], max(F)))
w('')
w('== 低 tS（<1.25）但已入池的样本（前 20，看平台到底收不收）==')
low = sorted([r for r in rows if r.get('tS') is not None and r['tS'] < 1.25], key=lambda r: r['tS'])
for r in low[:20]:
    w('   tS=%6.2f  S=%.2f F=%.2f TO=%.4f  %-8s dec=%-4s %s'
      % (r['tS'], r['S'] or 0, r['F'] or 0, r['TO'] or 0, r['u'], r['dec'], r['neu']))
w('   （共 %d 条 tS<1.25 已入池）' % len(low))
OUT.close()
print('pool_metrics done rows=%d' % len(rows))
