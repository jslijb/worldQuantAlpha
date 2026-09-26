# -*- coding: utf-8 -*-
"""x244 判决对手诊断：查出 corr 对手在池子的身份（cid/表达式/设置）"""
import io, json, os

ROOT = r'D:\Python\worldquant'
MD = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'mined')
LED = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'SUBMITTED_LEDGER.csv')
L = []

# 1) mined 目录建 id -> 记录
byid = {}
for fn in os.listdir(MD):
    if not fn.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MD, fn), encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id') or d.get('alpha_id')
    if aid:
        byid[str(aid)] = (fn, d)

# 2) 台账
sub = {}
for i, ln in enumerate(io.open(LED, encoding='utf-8-sig')):
    p = ln.rstrip('\n').split(',')
    if i == 0:
        L.append('台账表头: %s' % p[:8])
        continue
    if p and p[0].strip():
        sub[p[0].strip()] = p

OPP = ['O0N5o3Nv', 'omL8Mazn', 'O0N55k1Y', '6Xr2eQaJ', 'zq8jl99K',
       '6Xjmjr7G', 'kqVp6wnO', 'LLNXEe7L', '6Xr2eQaJ']

L.append('')
L.append('对手 id 身份（x244 判决里出现过的）')
L.append('%-10s %-6s %-30s %s' % ('aid', '在台账', 'mined文件/cid', '设置'))
for a in sorted(set(OPP)):
    inled = '是' if a in sub else '否'
    fn, d = byid.get(a, ('(mined里没有)', {}))
    cid = d.get('cid') or d.get('name') or (fn[:-5] if fn != '(mined里没有)' else '-')
    st = d.get('settings') or {}
    sett = '%s/%s/d%s' % (st.get('universe'), st.get('neutralization'), st.get('decay'))
    isd = d.get('is') or {}
    m = 'S=%s F=%s' % (isd.get('sharpe'), isd.get('fitness'))
    L.append('%-10s %-6s %-30s %-24s %s' % (a, inled, str(cid)[:30], sett, m))

# 3) 池内 107 条里，id 同时在 mined 的，看有多少是 x174 / w215 / w162 系
L.append('')
L.append('--- 池内 107 条里能追到 mined 的（按 cid 前缀归类）---')
pref = {}
for aid in sub:
    if aid in byid:
        cid = byid[aid][1].get('cid') or byid[aid][0][:-5]
        k = str(cid).split('_')[0]
        pref.setdefault(k, []).append((aid, cid))
L.append('台账 %d 行唯一 %d id；能在 mined 里查到的 %d 条' % (len(sub), len(set(sub)), sum(len(v) for v in pref.values())))
for k in sorted(pref, key=lambda x: -len(pref[x]))[:20]:
    L.append('  %-14s %2d 条  %s' % (k, len(pref[k]), ', '.join(a for a, _ in pref[k][:8])))

io.open(os.path.join(ROOT, '_autologs', '_oppo.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
