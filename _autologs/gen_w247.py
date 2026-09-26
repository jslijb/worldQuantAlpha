# -*- coding: utf-8 -*-
"""gen_w247.py —— 「桶分组 + TOP1000」双杠杆批量生成（可传 cid）

为什么这么做：
  · 杠杆 A「桶分组」：`9qX3M2mq_v2` subindustry 0.72+ → 波动率桶 平台 0.6846 入池（实证）
  · 杠杆 B「换小池」：TOP1000 版对池子 corr 塌到 0.45~0.64（0921 实证入池 2 条）
  · 两个杠杆此前只各自单打过，**从没叠加**。且 A 会改分组结构 ⇒ 与已入池的
    平分组 TOP1000 版（MPakMndk / 1YXJeQoW）应进一步脱钩（自撞是今天主要损耗：
    x246 两条分别撞 MPakMndk 0.8346 / 1YXJeQoW 0.7319）。

用法：python _autologs/gen_w247.py XgbgNwna,qMxM5j1A,... [--neut MARKET]
输出：_autologs/leg_combos_w247.json（喂 mine_batch181.py --combos）
"""
import os as _os, pathlib as _pl, sys, json, io, re
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

API = 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
BVOL = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'
BDV = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
rev = re.compile(r', (subindustry|industry|sector)\)')

args = [a for a in sys.argv[1:] if not a.startswith('--')]
IDS = [x.strip() for x in (args[0] if args else '').split(',') if x.strip()]
NEUT = None
for i, a in enumerate(sys.argv):
    if a == '--neut':
        NEUT = sys.argv[i + 1]

data = json.load(io.open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
byid = {a['id']: a for a in data}

combos = {}
rep = []
for sid in IDS:
    a = byid.get(sid)
    if not a:
        rep.append('%-11s 未在 all_unsubmitted.json 找到' % sid); continue
    expr = (a.get('regular') or {}).get('code') or ''
    if not expr:
        rep.append('%-11s 无表达式' % sid); continue
    st = a.get('settings') or {}
    b = a.get('is') or {}
    base = dict(neutralization=NEUT or st.get('neutralization') or 'SUBINDUSTRY',
                decay=st.get('decay') if st.get('decay') is not None else 10,
                truncation=st.get('truncation') if st.get('truncation') is not None else 0.08,
                delay=st.get('delay') if st.get('delay') is not None else 1)
    rep.append('%-11s S=%.2f F=%.2f TO=%.3f 组参数命中 %d 处  neut=%s dec=%s'
               % (sid, b.get('sharpe') or 0, b.get('fitness') or 0, b.get('turnover') or 0,
                  len(rev.findall(expr)), base['neutralization'], base['decay']))
    for tag, bk in (('bvol_u1k', BVOL), ('bdv_u1k', BDV)):
        e2, n = rev.subn(', %s)' % bk, expr)
        if n == 0:
            continue
        m = dict(base)
        m['expr'] = e2
        m['universe'] = 'TOP1000'
        m['_note'] = '桶分组(%s)+TOP1000（源 %s）' % ('波动率' if bk == BVOL else '成交额', sid)
        combos['%s__%s' % (sid, tag)] = m

io.open('_autologs/leg_combos_w247.json', 'w', encoding='utf-8').write(
    json.dumps(combos, ensure_ascii=False, indent=1))
rep.append('')
rep.append('w247 combos = %d（%d 源 × 2 桶）' % (len(combos), len(IDS)))
io.open('_autologs/_w247_gen.txt', 'w', encoding='utf-8').write('\n'.join(rep) + '\n')
print('ok %d' % len(combos))
