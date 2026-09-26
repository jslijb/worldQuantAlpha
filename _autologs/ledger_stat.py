# -*- coding: utf-8 -*-
"""台账口径统计：唯一 id / 当日（美东）计数 / 最近提交明细。"""
import csv, io, sys

R = io.open('_autologs/_ledger_stat.txt', 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


rows = list(csv.reader(io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
h = rows[0]
log('header: %s' % h)
di = h.index('dateSubmitted') if 'dateSubmitted' in h else -1
ids = []
for r in rows[1:]:
    if r and r[0] and r[0] not in ids:
        ids.append(r[0])
log('rows: %d   unique id: %d' % (len(rows) - 1, len(ids)))

if di >= 0:
    for day in ('2026-09-19', '2026-09-20'):
        t = [r for r in rows[1:] if len(r) > di and r[di].startswith(day)]
        log('%s: %d' % (day, len(t)))
    log('')
    log('--- 0920 明细 ---')
    t = [r for r in rows[1:] if len(r) > di and r[di].startswith('2026-09-20')]
    for i, r in enumerate(t, 1):
        try:
            sf = float(r[2]) + float(r[3])
        except Exception:
            sf = 0
        log('%2d. %-10s S=%-5s F=%-5s SF=%.2f  %s' % (i, r[0], r[2], r[3], sf, r[di][:19]))

log('')
log('--- 最后 6 行原始 ---')
for r in rows[-6:]:
    log(str(r[:4]) + ' | ' + (r[di][:19] if len(r) > di else ''))
