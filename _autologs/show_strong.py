# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl, json, glob
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
MINED = 'data/alpha_quality_analysis/mined'
want = ['1YXQJRoX', 'VkagZle0', 'Xgb59aRb', 'JjNZ3Rbm', 'XgbgNwna', 'qMx9ZPaP', 'wpY3Yxvd', '9qjQWk3V', 'JjNlZEmx', 'Vkan1Ek5', '1YX6MA0M']
out = []
found = {}
for f in glob.glob(f'{MINED}/*.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    if d.get('id') in want:
        found[d['id']] = d
for aid in want:
    d = found.get(aid)
    if not d:
        out.append(f'{aid}  <未找到>'); continue
    i = d.get('is') or {}; t = d.get('test') or {}
    out.append(f"=== {aid}  S={i.get('sharpe')} F={i.get('fitness')} tS={t.get('sharpe')} cid={d.get('_cid')}")
    out.append('    ' + str((d.get('regular') or {}).get('code')))
    out.append('')
open('_autologs/strong_cands.out', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
