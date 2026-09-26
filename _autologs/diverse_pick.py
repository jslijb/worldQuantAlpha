# -*- coding: utf-8 -*-
"""diverse_pick.py —— 从过闸候选里按"字段集合骨架"分簇，每簇取最高 F 的代表

目的：u1000 批次 top20 全挤在同一簇（xrent+cash45+cfoev45），导致小池版互相撞（corr 0.9+）。
换池要吃到量，源必须来自**不同簇**。
"""
import os as _os, pathlib as _pl, json, io, re, collections
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

data = json.load(io.open('data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json', encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])

FIELDS = ('assets cashflow_op cash enterprise_value cap volume close returns open high low vwap '
          'adv20 fnd6_xrent fnd6_pstkl fnd6_txtubadjust fn_accrued_liab_curr_a fnd6_newqv1300_glcea12 '
          'fnd6_newqv1300_cimiiq liabilities_curr annual_intangible fnd6_newa2v1300_ni fnd6_mfma2_revt '
          'news_short_interest news_open_gap forward_price_30 forward_price_90 debt sales').split()


def fields_of(code):
    """抽出表达式里用到的字段（排除算子/关键词）"""
    toks = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', code or ''))
    keep = set()
    for t in toks:
        tl = t.lower()
        if tl in ('group_rank', 'group_neutralize', 'rank', 'ts_av_diff', 'ts_delta', 'ts_mean',
                  'ts_rank', 'ts_std_dev', 'ts_delay', 'ts_zscore', 'ts_sum', 'ts_decay_linear',
                  'bucket', 'range', 'subindustry', 'sector', 'industry', 'market', 'if_else',
                  'abs', 'log', 'sign', 'signed_power', 'winsorize', 'normalize', 'quantile',
                  'ts_arg_min', 'ts_arg_max', 'hump', 'nan', 'div', 'add', 'sub', 'mul', 'vec_avg'):
            continue
        if re.match(r'^[a-z]', tl) and len(tl) > 2:
            keep.add(tl)
    return tuple(sorted(keep))


rows = []
for a in data:
    st = a.get('settings') or {}
    b = a.get('is') or {}
    te = a.get('test') or {}
    if st.get('universe') != 'TOP3000':
        continue
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    TO = b.get('turnover'); tS = te.get('sharpe') or 0
    if fa or S + F < 4.0 or tS < 1.25 or F < 2.0 or (TO or 9) > 0.20:
        continue
    code = (a.get('regular') or {}).get('code') or ''
    if not code:
        continue
    rows.append(dict(id=a['id'], F=F, S=S, TO=TO, tS=tS, code=code, fs=fields_of(code),
                     neu=st.get('neutralization'), dec=st.get('dec')))

# 按字段集合分簇
clu = collections.defaultdict(list)
for r in rows:
    clu[r['fs']].append(r)

L = []
L.append('TOP3000 过闸候选 %d 条 → 字段骨架簇 %d 个' % (len(rows), len(clu)))
L.append('=' * 120)
order = sorted(clu.items(), key=lambda x: -max(r['F'] for r in x[1]))
for i, (fs, rs) in enumerate(order[:24]):
    rs.sort(key=lambda x: -x['F'])
    L.append('[簇 %02d] n=%-3d 代表 %s  S=%.2f F=%.2f TO=%.4f tS=%.2f  %s'
             % (i + 1, len(rs), rs[0]['id'], rs[0]['S'], rs[0]['F'], rs[0]['TO'] or 0, rs[0]['tS'],
                rs[0]['neu']))
    L.append('        字段: %s' % ', '.join(fs)[:150])
    L.append('        代表表达式: %s' % rs[0]['code'][:170])

reps = [rs[0]['id'] for fs, rs in order[:20]]
L.append('')
L.append('每簇代表（去重后前 20 个簇的 id，可直接喂 mine_univ_convert --ids）：')
L.append(','.join(reps))
io.open('_autologs/_diverse_pick.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done clusters=%d' % len(clu))
