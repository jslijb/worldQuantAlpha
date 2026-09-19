# -*- coding: utf-8 -*-
import io, glob, json
names = ['A_xr_I', 'A_xr_C', 'A_xr_V', 'A_intc_I', 'A_intc_C', 'A_debt_I', 'A_acc_I',
         'A_int_I', 'A_lnoq_I', 'A_g12_I', 'P_int5', 'P_int15', 'P_int30',
         'P_int10I', 'P_int10C', 'P_int10V']
out = []
for n in names:
    fs = glob.glob(f'data/alpha_quality_analysis/mined/*_{n}.json') + \
         glob.glob(f'data/alpha_quality_analysis/mined/{n}.json')
    best = None
    for f in fs:
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        isd = d.get('is', {}) or {}
        s = isd.get('sharpe') or 0
        ft = isd.get('fitness') or 0
        fails = [c.get('name') for c in (isd.get('checks') or []) if isinstance(c, dict) and c.get('result') == 'FAIL']
        cid = d.get('_cid') or f.split('/')[-1].split(chr(92))[-1][:-5]
        if cid == n or cid.endswith('_' + n):
            cur = (s + ft, cid, d.get('id'), s + ft, ts if False else (d.get('test') or {}).get('sharpe'), fails)
            if best is None or cur[0] > best[0]:
                best = cur
    if best:
        out.append('%-10s id=%s SF=%.2f tS=%s FAIL=%s' % (n, best[2], best[3], best[4], best[5]))
    else:
        out.append('%-10s NOT FOUND' % n)
io.open(r'_autologs\q7.txt', 'w', encoding='utf-8').write('\n'.join(out))
