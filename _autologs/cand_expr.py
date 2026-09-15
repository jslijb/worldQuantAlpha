# -*- coding: utf-8 -*-
"""读出高潜候选的表达式，为降权改造做准备"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

TARGETS = ['w114_o', 'w115_l', 'w115_k', 'w116_c', 'w118_b', 'w119_f', 'w114_d', 'w116_g']
out = []
for cid in TARGETS:
    p = f'data/alpha_quality_analysis/mined/{cid}.json'
    if not os.path.exists(p):
        out.append(f'{cid}: 文件不存在'); continue
    d = json.load(open(p, encoding='utf-8'))
    b = d.get('is') or {}; te = d.get('test') or {}
    st = d.get('settings') or {}
    out.append(f"=== {cid} {d.get('id')} S={b.get('sharpe')} F={b.get('fitness')} "
               f"tS={te.get('sharpe')} T={b.get('turnover')} ===")
    out.append(f"  settings: neut={st.get('neutralization')} decay={st.get('decay')} "
               f"trunc={st.get('truncation')} univ={st.get('universe')} reg={st.get('region')}")
    out.append(f"  {d.get('regular', {}).get('code')}")
    out.append('')

# 统计各候选与"共享腿"的吻合度
out.append('=== 共享腿出现情况 ===')
LEGS = {
    'cash45': 'ts_av_diff(cash/assets, 45)',
    'ev45': 'ts_av_diff(cashflow_op/enterprise_value, 45)',
    'pv_close2': '-ts_delta(close, 2)',
    'pv_vol60': 'volume/ts_mean(volume, 60)',
}
import glob
cnt = {k: 0 for k in LEGS}
tot = 0
for f in glob.glob('data/alpha_quality_analysis/mined/w11*.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    e = (d.get('regular') or {}).get('code') or ''
    if not e:
        continue
    tot += 1
    for k, pat in LEGS.items():
        if pat in e:
            cnt[k] += 1
out.append(f'w11x 池共 {tot} 条')
for k, v in cnt.items():
    out.append(f'  {k:12} {v:3} 条 ({v/max(tot,1)*100:.0f}%)')

open('_autologs/cand_expr.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
