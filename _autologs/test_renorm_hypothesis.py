# -*- coding: utf-8 -*-
"""验证机制假设：偏移 delta 是否随引擎腿权重占比上升（重整化集中效应）"""
import os, json, re, glob
os.chdir(r'D:\Python\worldquant')
out = []

# 引擎腿签名（cash45 / cfoev45 是质量引擎，也是公共相关来源）
ENGINE_KEYS = ['cash', 'cfoev', 'cfo_', 'cashflow']

def combo_info(cid):
    """从各 combo json / mined json 里找该候选的腿构成"""
    # 1) merged jsons
    for jf in ['_autologs/search_combos_w197.json', '_autologs/search_combos_w198.json']:
        if os.path.exists(jf):
            d = json.load(open(jf, encoding='utf-8'))
            if cid in d:
                return d[cid]
    # 2) w196 per-anchor
    i = 0
    for a in ['M_debt','M_tstk','M_intc','M_accI','M_intI','M_cfoQ','M_lnoq']:
        p = '_autologs/search_combos_w196_%s.json' % a
        if os.path.exists(p):
            d = json.load(open(p, encoding='utf-8'))
            for k, v in sorted(d.items()):
                if 'w196_%02d' % i == cid:
                    return v
                i += 1
    # 3) mined json 的 expr
    p = 'data/alpha_quality_analysis/mined/%s.json' % cid
    if os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
        return {'expr': d.get('regular', '')}
    return None

def engine_share(v):
    """引擎腿权重占比：从 expr 里粗估（出现 cash/cfoev 项的字符权重难精确，先看 expr 文本密度）"""
    e = str(v.get('expr', ''))
    if not e:
        return None
    # 粗口径：引擎关键词出现的次数 / 表达式长度（千分比）
    hits = sum(e.count(k) for k in ENGINE_KEYS)
    return hits, len(e)

# 判决观测（从 r6 结果重建：cid -> delta）
obs = {
 'w196_11': 0.1755, 'w196_04': 0.1867, 'w196_12': 0.1997, 'w196_15': 0.2310,
 'w196_00': 0.2492, 'w198_01': 0.2879, 'w198_03': 0.3055, 'w196_18': 0.3066,
 'w196_02': 0.3157, 'w198_00': 0.3161, 'w198_02': 0.3207, 'w198_04': 0.3398,
 'w197_00': 0.3732, 'w197_01': 0.3736, 'w196_08': 0.3906,
}

rows = []
for cid, dl in sorted(obs.items()):
    v = combo_info(cid)
    if v is None:
        rows.append((cid, dl, None, 'NO COMBO'))
        continue
    es = engine_share(v)
    legs = v.get('weights') or v.get('legs')
    rows.append((cid, dl, es, 'legs=%s' % (len(legs) if isinstance(legs, list) else '?')))

for r in rows:
    out.append('%-9s delta=%+.4f engine_hits/len=%s %s' % (r[0], r[1], r[2], r[3]))

# 相关性：engine 密度 vs delta
import statistics as st
xs = [r[2][0] / r[2][1] * 1000 for r in rows if r[2]]
ys = [r[1] for r in rows if r[2]]
if len(xs) > 2 and st.pstdev(xs) > 0:
    mx, my = st.mean(xs), st.mean(ys)
    cov = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / len(xs)
    out.append('')
    out.append('corr(engine_density, delta) = %.3f  (n=%d)' % (cov / (st.pstdev(xs) * st.pstdev(ys)), len(xs)))

open('_autologs/r9.txt', 'w', encoding='utf-8').write('\n'.join(out))
