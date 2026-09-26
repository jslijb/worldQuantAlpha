# -*- coding: utf-8 -*-
"""换挡靶排雷器
目的：在选靶做中性化换挡前，先判断"该骨架的换挡空间是否已被已提交的 alpha 占用"。
判据：把表达式里的 subindustry|sector|industry|market 归一化 → 骨架指纹。
      若同一指纹下已有【已提交】的 alpha，则这个骨架的换挡轮次已经被吃过，
      再对同骨架换挡 = 撞自己（0920 实证 akbWaOZ9 vs A_MAR corr 0.9979）。
输出：可换挡靶清单（corr 0.70~0.80 且骨架未被占）
"""
import io, json, os, re, glob, datetime

ROOT = r'D:\Python\worldquant'
AD = os.path.join(ROOT, '_autologs')
MD = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'mined')
LED = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'SUBMITTED_LEDGER.csv')
L = []

NEU = re.compile(r'\b(subindustry|sector|industry|market)\b', re.I)


def fp(code):
    return NEU.sub('@N@', code)


# ---------- 1. mined 全库 ----------
recs = {}
for fn in os.listdir(MD):
    if not fn.endswith('.json'):
        continue
    cid = fn[:-5]
    try:
        d = json.load(io.open(os.path.join(MD, fn), encoding='utf-8'))
    except Exception:
        continue
    code = ((d.get('regular') or {}).get('code') or '')
    st = d.get('settings') or {}
    isd = d.get('is') or {}
    recs[cid] = dict(aid=str(d.get('id') or ''), code=code,
                     fp=fp(code) if code else '', neu=st.get('neutralization'),
                     uni=st.get('universe'), dec=st.get('decay'),
                     S=isd.get('sharpe'), F=isd.get('fitness'), TO=isd.get('turnover'))

# ---------- 2. 台账（已提交） ----------
sub = set()
for i, ln in enumerate(io.open(LED, encoding='utf-8-sig')):
    p = ln.rstrip('\n').split(',')
    if i and p and p[0].strip():
        sub.add(p[0].strip())

# 指纹 -> 已提交条目
fp_sub = {}
for cid, r in recs.items():
    if r['aid'] in sub and r['fp']:
        fp_sub.setdefault(r['fp'], []).append((cid, r['neu'], r['S'], r['F']))

# ---------- 3. 判决日志里的 corr 实测 ----------
corr = {}
for f in glob.glob(os.path.join(AD, 'exempt_*.log')):
    try:
        for ln in io.open(f, encoding='utf-8', errors='replace'):
            if 'corr_max=' not in ln:
                continue
            m = re.search(r'([A-Za-z0-9]{8,10})\s+(\S+)\s+SF=', ln)
            mc = re.search(r'corr_max=([\d.]+)', ln)
            if m and mc:
                cid, n = m.group(2), float(mc.group(1))
                if cid not in corr or n < corr[cid]:
                    corr[cid] = n
    except Exception:
        pass

L.append('时间 %s' % datetime.datetime.now())
L.append('mined %d 条；台账唯一已提交 %d 条；判决日志覆盖 %d 个 cid'
         % (len(recs), len(sub), len(corr)))
L.append('')

# ---------- 4. 分档 ----------
# 4a. 已实测 corr 在 0.70~0.80 的候选
band = [(cid, c) for cid, c in corr.items() if 0.70 <= c <= 0.80]
L.append('=' * 100)
L.append('【A】实测 corr ∈ [0.70, 0.80] 的候选 %d 条 —— 换挡的目标区间' % len(band))
L.append('%-40s %-6s %-12s %-7s %-7s %-7s %s' % ('cid', 'corr', '当前中性化', 'S', 'F', 'TO', '骨架是否已被提交占用'))
free, taken = [], []
for cid, c in sorted(band, key=lambda x: x[1]):
    r = recs.get(cid)
    if not r:
        L.append('%-40s %-6s %s' % (cid[:40], c, '(mined 里无此文件)'))
        continue
    hit = fp_sub.get(r['fp'], [])
    tag = ('★ 已被占: ' + ', '.join('%s(%s)' % (h[0], h[1]) for h in hit[:3])) if hit else '✔ 空闲'
    (taken if hit else free).append(cid)
    L.append('%-40s %-6s %-12s %-7s %-7s %-7s %s'
             % (cid[:40], c, r['neu'], r['S'], r['F'], r['TO'], tag))
L.append('')
L.append('⇒ 空闲（可换挡）%d 条；已被占（换挡=撞自己）%d 条' % (len(free), len(taken)))
L.append('   空闲清单: %s' % ', '.join(free))

# 4b. 空闲骨架的可用档位
L.append('')
L.append('=' * 100)
L.append('【B】空闲靶的档位建议（当前档 → 建议档）')
BY = {'SUBINDUSTRY': ['MARKET', 'SECTOR', 'INDUSTRY'],
      'SECTOR': ['MARKET', 'SUBINDUSTRY', 'INDUSTRY'],
      'INDUSTRY': ['MARKET', 'SECTOR', 'SUBINDUSTRY'],
      'MARKET': ['SECTOR', 'SUBINDUSTRY', 'INDUSTRY'],
      'NONE': ['MARKET', 'SECTOR']}
for cid in free:
    r = recs.get(cid)
    if not r:
        continue
    L.append('  %-40s %-12s → %s   (S=%s F=%s TO=%s corr=%.4f)'
             % (cid[:40], r['neu'], '/'.join(BY.get(str(r['neu']), ['MARKET', 'SECTOR'])),
                r['S'], r['F'], r['TO'], corr[cid]))

io.open(os.path.join(AD, '_shade_target.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok free=%d taken=%d' % (len(free), len(taken)))
