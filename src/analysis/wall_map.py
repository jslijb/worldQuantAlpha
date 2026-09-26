# -*- coding: utf-8 -*-
"""wall_map.py —— 墙图分析器

从历次 submit_exempt 判决日志里抽取 (候选, 自己S, corr, 挡路的对手id, 对手S)，
汇总出：
  ① 每面墙（对手）挡掉了多少候选 —— 谁是真墙
  ② 低夏普靶区（S ≤ 2.4 的池成员）—— 豁免线最低、最好打的方向
  ③ 候选与墙的对照表，供下一批设计几何时参考

用法：python src/analysis/wall_map.py
"""
import os as _os, pathlib as _pl, json, re, glob, collections

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

POOL_S = 'data/alpha_quality_analysis/pool_s.json'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

# 判决行形如（中文被 PowerShell 重定向搞乱，但 ASCII 部分完好）：
#   ✗ 9qjAA08K w228_f  SF=6.27 S=3.26 corr=0.7018 撞0mR2K6lr(S=3.45) 需≥3.80 → 不够
ROW = re.compile(r'([A-Za-z0-9]{8})\s+(\S+)\s+SF=([\d.]+)\s+S=([\d.]+)\s+corr=([\d.]+)')
RIVAL = re.compile(r'([A-Za-z0-9_]{6,12})\(S=([\d.]+)\)')


def ungarble(raw: bytes) -> str:
    """PowerShell 把 Python 的 UTF-8 输出按 CP936 解码后写成 UTF-16 → 回转"""
    txt = raw.decode('utf-16', errors='ignore')
    if 'SF=' not in txt:
        txt = raw.decode('utf-8', errors='ignore')
    if '\ufffd' in txt or any('\u4e00' <= ch <= '\u9fff' for ch in txt[:400]):
        pass
    try:
        back = txt.encode('cp936', errors='ignore').decode('utf-8', errors='ignore')
        if back.count('SF=') >= txt.count('SF=') and '撞' in back + txt:
            return back
    except Exception:
        pass
    return txt


triples = []
logs = sorted(set(glob.glob('_autologs/*exempt*.txt') + glob.glob('_autologs/*_exempt.txt')
                  + glob.glob('_autologs/exempt_*.log')))
for f in logs:
    txt = ungarble(open(f, 'rb').read())
    for ln in txt.splitlines():
        m = ROW.search(ln)
        if not m:
            continue
        aid, cid, sf, s, corr = m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5))
        rm = RIVAL.search(ln)
        if rm:
            rs = float(rm.group(2))
            # 与编码无关的判据：工具只在 S >= 1.1×对手S 时才提交
            passed = s >= 1.1 * rs - 0.02
            triples.append((cid, s, corr, rm.group(1), rs, 'passed' if passed else 'blocked'))
        else:
            triples.append((cid, s, corr, None, None, 'passed'))

pool = {}
if _pl.Path(POOL_S).exists():
    pool = {k: v for k, v in json.load(open(POOL_S, encoding='utf-8')).items() if v}

# 台账里的表达式，用来解读墙是什么几何
expr = {}
rows = open(LED, encoding='utf-8-sig').read().splitlines()[1:]
for ln in rows:
    aid = ln.split(',')[0].strip('"')
    if aid and aid not in expr:
        expr[aid] = ln

out = []
out.append('=' * 78)
out.append('① 真墙排行（按挡掉的候选数）')
out.append('=' * 78)
wall = collections.Counter(t[3] for t in triples if t[3])
seen_c = collections.defaultdict(set)
for t in triples:
    if t[3]:
        seen_c[t[3]].add(t[0])
for aid, n in wall.most_common(25):
    out.append(f'  挡 {len(seen_c[aid]):3d} 次  {aid}  S={pool.get(aid)}  {expr.get(aid, "")[:95]}')

out.append('')
out.append('=' * 78)
out.append('② 低夏普靶区（豁免线 = 1.1×S，越低越好打）')
out.append('=' * 78)
low = sorted([(v, k) for k, v in pool.items() if v <= 2.45])
for v, k in low:
    out.append(f'  S={v:.2f}  线={1.1*v:.2f}  {k}  {expr.get(k, "")[:90]}')

out.append('')
out.append('=' * 78)
out.append('③ 命中记录（过了的）')
out.append('=' * 78)
for t in triples:
    if t[5] == 'passed' and t[3] is None:
        out.append(f'  {t[0]:34s} S={t[1]:.2f} corr={t[2]:.4f} → 直通')
    elif t[5] == 'passed':
        out.append(f'  {t[0]:34s} S={t[1]:.2f} corr={t[2]:.4f} 撞{t[3]}(S={t[4]}) 线={1.1*t[4]:.2f} → 豁免放行')

out.append('')
out.append(f'样本 {len(triples)} 条判决，其中放行 {sum(1 for t in triples if t[5]=="passed")} 条')
open('_autologs/wall_map.out', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:6]))
print('written _autologs/wall_map.out', len(triples))
