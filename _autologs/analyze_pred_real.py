# -*- coding: utf-8 -*-
"""分析 leg_lab pred corr vs 实测 corr 的偏移结构（0918, 33 个判决观测点）"""
import io, re, json, glob, csv, os

os.chdir(r'D:\Python\worldquant')

# 1) 判决记录：cid -> (real_corr, opponent)  日志是 utf-8 存的但 PS 误标
judged = {}
logs = ['judge_w196.log','judge_w196_04.log','judge_x196.log','judge_w197.log',
        'judge_w198.log','judge_x163.log']
pat = re.compile(r'((?:w19[678]|x19[36])_\S+)\s+SF=([\d.]+)\s+tS=([\d.]+)\s+corr=([\d.]+)')
opp_pat = re.compile(r'corr=[\d.]+\s+\S*?([A-Za-z0-9]{7,9})(?:\s|$)')
for lg in logs:
    p = '_autologs/' + lg
    if not os.path.exists(p):
        continue
    raw = open(p, 'rb').read()
    for enc in ('utf-8', 'utf-16', 'gbk'):
        try:
            t = raw.decode(enc)
            if 'corr=' in t:
                break
        except Exception:
            continue
    for m in pat.finditer(t):
        om = opp_pat.search(t, m.start(), m.end() + 40)
        opp = om.group(1) if om else '?'
        judged[m.group(1)] = (float(m.group(4)), opp, float(m.group(2)), float(m.group(3)))

# 2) pred：从 search_combos json 找 maxcorr（按 _from_anchor / cid 前缀对应）
preds = {}
def load_pred(path, cidmap):
    d = json.load(open(path, encoding='utf-8'))
    for k, v in d.items():
        cid = cidmap.get(k, k)
        if isinstance(v, dict) and 'maxcorr' in v:
            preds[cid] = (float(v['maxcorr']), float(v.get('S', 0)), len(v.get('legs', v.get('weights', []))) if isinstance(v.get('legs', v.get('weights')), list) else -1)

# w196: per-anchor files -> merged w196_00.. 按 sorted 顺序编号
w196_merged = {}
i = 0
for a in ['M_debt','M_tstk','M_intc','M_accI','M_intI','M_cfoQ','M_lnoq']:
    p = '_autologs/search_combos_w196_%s.json' % a
    if os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
        for k, v in sorted(d.items()):
            w196_merged['w196_%02d' % i] = (float(v['maxcorr']), float(v.get('S', 0)))
            i += 1
for cid, (mc, s) in w196_merged.items():
    if cid in judged:
        preds[cid] = (mc, s)

# w197: merged file
if os.path.exists('_autologs/search_combos_w197.json'):
    d = json.load(open('_autologs/search_combos_w197.json', encoding='utf-8'))
    for k, v in d.items():
        if k in judged:
            preds[k] = (float(v['maxcorr']), float(v.get('S', 0)))
# w198
if os.path.exists('_autologs/search_combos_w198.json'):
    d = json.load(open('_autologs/search_combos_w198.json', encoding='utf-8'))
    for k, v in d.items():
        if k in judged:
            preds[k] = (float(v['maxcorr']), float(v.get('S', 0)))
# x196 / x163: 转换产物, pred = 原始 cid 的 maxcorr
for src, dst in [('w196_11','x196_00'),('w196_11','x196_01'),('w196_12','x196_02'),('w196_12','x196_03')]:
    pass  # x196 pred 需要查原始 w196 json
if os.path.exists('_autologs/search_combos_w196.json'):
    d = json.load(open('_autologs/search_combos_w196.json', encoding='utf-8'))
    for k, v in d.items():
        for jk in judged:
            if jk.startswith('x196'):
                pass

# x163 那条: vRrwaX7z 对应 cid 可能是 x163_w27lnoqxrent_MAR 之类
# 从 mined json 里找 _base_corr
for f in glob.glob('data/alpha_quality_analysis/mined/x16*.json') + glob.glob('data/alpha_quality_analysis/mined/x19*.json'):
    d = json.load(open(f, encoding='utf-8'))
    cid = os.path.basename(f)[:-5]
    if cid in judged and '_base_corr' in d and cid not in preds:
        preds[cid] = (float(d['_base_corr']), None)

# 3) 配对分析
rows = []
for cid, (rc, opp, sf, ts) in sorted(judged.items()):
    if cid in preds:
        pc = preds[cid][0]
        rows.append((cid, pc, rc, rc - pc, opp, sf))

out = ['配对观测 %d / 判决 %d' % (len(rows), len(judged)), '']
out.append('%-10s %7s %7s %7s  %s' % ('cid','pred','real','delta','opponent'))
for cid, pc, rc, dl, opp, sf in sorted(rows, key=lambda r: r[3]):
    out.append('%-10s %7.4f %7.4f %+7.4f  %s' % (cid, pc, rc, dl, opp))
dl = [r[3] for r in rows]
if dl:
    import statistics as st
    out.append('')
    out.append('delta: n=%d mean=%+.4f min=%+.4f max=%+.4f stdev=%.4f' % (len(dl), st.mean(dl), min(dl), max(dl), st.pstdev(dl)))
    # delta 与 pred 的相关性（低 pred 是否真的偏移小？）
    xs = [r[1] for r in rows]
    if len(xs) > 2 and st.pstdev(xs) > 0:
        mx, my = st.mean(xs), st.mean(dl)
        cov = sum((a-mx)*(b-my) for a, b in zip(xs, dl)) / len(xs)
        r_corr = cov / (st.pstdev(xs) * st.pstdev(dl))
        out.append('corr(delta, pred) = %.3f' % r_corr)
io.open('_autologs/r6.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('done')
