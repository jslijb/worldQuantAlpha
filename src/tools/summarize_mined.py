import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import json, glob, sys
pat = sys.argv[1] if len(sys.argv) > 1 else 'w6*'
for f in sorted(glob.glob(rf'data/alpha_quality_analysis/mined/{pat}.json')):
    d = json.load(open(f, encoding='utf-8'))
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    ok = all(c.get('result') in ('PASS', 'PENDING') for c in b.get('checks', []))
    print('%-8s %-9s S=%.2f F=%.2f SF=%.2f T=%s testS=%s checks=%s' % (
        d.get('_cid'), d.get('id'), S, F, S + F, b.get('turnover'), te.get('sharpe'), 'OK' if ok else 'FAIL'))
