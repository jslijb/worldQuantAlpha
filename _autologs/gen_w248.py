# -*- coding: utf-8 -*-
"""gen_w248.py —— TOP1000 + decay 阶梯（把差 0.06 的候选顶过豁免线）

背景（0921 判决）：
  `kqoQ2l2d`（x246_E5p5NVkR_TOP1）S=2.35 / F=1.76 / TO=18.4% / tS=1.68，corr_max 0.7319
  唯一对手 = **1YXJeQoW(S=2.19)**（今天刚入池）→ 豁免线只需 1.1×2.19 = **2.41**
  ⇒ **只差 0.06 S**。豁免路在"对手 S 低"时是活的（这条对手 S 只有 2.19）。

decay 阶梯是已验证的"提 S"手段（跷跷板：S↑ 同时 TO↑）⇒ 必须复核 TO ≤ 20%。
本批只跑 decay {12, 10, 8}（源 decay=14），观察 S 是否跨过 2.41 而 TO 仍 ≤20%。
"""
import os as _os, pathlib as _pl, sys, json, io
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

API = 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
CID = sys.argv[1] if len(sys.argv) > 1 else 'E5p5NVkR'
DECAYS = [int(x) for x in (sys.argv[2].split(',') if len(sys.argv) > 2 else ['12', '10', '8'])]

data = json.load(io.open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
byid = {a['id']: a for a in data}
a = byid.get(CID)
assert a, '未找到 ' + CID
expr = (a.get('regular') or {}).get('code') or ''
st = a.get('settings') or {}
b = a.get('is') or {}

combos = {}
for d in DECAYS:
    combos['%s__u1k_d%d' % (CID, d)] = dict(
        expr=expr, universe='TOP1000',
        neutralization=st.get('neutralization') or 'SUBINDUSTRY',
        decay=d,
        truncation=st.get('truncation') if st.get('truncation') is not None else 0.08,
        delay=st.get('delay') if st.get('delay') is not None else 1,
        _note='TOP1000 + decay=%d（源 %s 原 decay=%s，为顶过豁免线 2.41）'
              % (d, CID, st.get('decay')))

io.open('_autologs/leg_combos_w248.json', 'w', encoding='utf-8').write(
    json.dumps(combos, ensure_ascii=False, indent=1))
rep = ['源 %s  S=%.2f F=%.2f TO=%.4f tS=%.2f  原 decay=%s > 目标线 2.41（对手 1YXJeQoW S=2.19）'
       % (CID, b.get('sharpe') or 0, b.get('fitness') or 0, b.get('turnover') or 0,
          (a.get('test') or {}).get('sharpe') or 0, st.get('decay')),
       'combos = %d  decay=%s' % (len(combos), DECAYS)]
io.open('_autologs/_w248_gen.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('ok %d' % len(combos))
