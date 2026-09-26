# -*- coding: utf-8 -*-
"""汇总高F低换手候选的表达式/参数，用于换中性化破相关。"""
import json, io, glob, os

OUT = '_autologs/highF_pool.txt'
R = io.open(OUT, 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


groups = ['w158_*', 'w189_*', 'w182_*', 'w53_*', 'w55_*', 'w51_*', 'w52_*', 'w54_*', 'w48_*', 'w49_*', 'w188_*', 'w196_*', 'w193_*', 'w228_*', 'n160_*']
seen = {}
for g in groups:
    for f in sorted(glob.glob('data/alpha_quality_analysis/mined/%s.json' % g)):
        try:
            d = json.load(io.open(f, encoding='utf-8'))
        except Exception:
            continue
        i = d.get('is') or {}; t = d.get('test') or {}
        S = i.get('sharpe') or 0; F = i.get('fitness') or 0; TO = i.get('turnover') or 0
        fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
        if S + F < 4.0 or (t.get('sharpe') or 0) < 1.25 or fa:
            continue
        cid = d.get('_cid') or os.path.basename(f)[:-5]
        seen[cid] = dict(aid=d.get('id'), S=S, F=F, TO=TO, tS=t.get('sharpe') or 0,
                         margin=i.get('margin') or 0, ret=i.get('returns') or 0,
                         dd=i.get('drawdown') or 0,
                         neut=d.get('_neut'), decay=d.get('_decay'),
                         expr=((d.get('regular') or {}).get('code') or ''))

log('达标候选（SF>=4.0, tS>=1.25, 无FAIL）：%d 条' % len(seen))
log('')
for cid, v in sorted(seen.items(), key=lambda kv: -kv[1]['F']):
    log('%-30s %s S=%.2f F=%.2f tS=%.2f TO=%5.1f%% margin=%5.1fbp ret=%.1f%% DD=%.1f%% neut=%s decay=%s' % (
        cid, v['aid'], v['S'], v['F'], v['tS'], v['TO'] * 100, v['margin'] * 1e4,
        v['ret'] * 100, v['dd'] * 100, v['neut'], v['decay']))
    log('    ' + v['expr'])
log('')
log('=== 去重后的表达式骨架 ===')
uniq = {}
for cid, v in seen.items():
    uniq.setdefault(v['expr'], []).append(cid)
for e, ids in sorted(uniq.items(), key=lambda kv: -len(kv[1])):
    log('[%d 条] %s' % (len(ids), ', '.join(ids[:6])))
    log('  ' + e)
