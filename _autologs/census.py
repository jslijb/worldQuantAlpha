# -*- coding: utf-8 -*-
"""census.py —— 全库普查：本地到底有多少候选、多少过闸、多少实测过墙

回答李工 0920 提问：「待提交 3500+，在这 3500 个里提夏普+降换手，是不是就能提交？」
本脚本核实三件事：
  1) 「3500+」这个数从哪来（本地挖矿产物 vs 平台账号可视数）
  2) 过质量闸门（S+F>=4.0 / tS>=1.25 / 无 FAIL / F>=1.8）的真实条数
  3) 有实测 corr 记录的候选里，过相关墙（corr_max<=0.685）的有几条
输出 _autologs/_census.txt
"""
import io, os, csv, json, re, collections, statistics as st

ROOT = 'D:/Python/worldquant/'
L = []
def w(s=''):
    L.append(s)

# ---------- 0. 解码 _cnt_dry.out（PowerShell 重定向产物）----------
src = ROOT + '_autologs/_cnt_dry.out'
if os.path.exists(src):
    raw = io.open(src, 'rb').read()
    txt, enc = None, '?'
    for e in ('utf-8', 'utf-16', 'gbk'):
        try:
            txt = raw.decode(e); enc = e; break
        except Exception:
            pass
    if txt is None:
        txt, enc = raw.decode('latin-1'), 'latin-1'
    w('== 0. _cnt_dry.out (enc=%s, %d bytes) ==' % (enc, len(raw)))
    lines = txt.replace('\r', '').strip().splitlines()
    for ln in lines[-60:]:
        w('  ' + ln.rstrip())
    w('')

# ---------- 1. data/ 下 json 分布 ----------
dist = collections.Counter()
for dp, dn, fn in os.walk(ROOT + 'data'):
    c = sum(1 for f in fn if f.endswith('.json'))
    if c:
        dist[dp.replace(ROOT, '')] = c
w('== 1. data/ 下 json 分布 ==')
for k, v in dist.most_common(30):
    w('  %-56s %d' % (k, v))
w('  合计 %d' % sum(dist.values()))
w('')

# ---------- 2. 台账 ----------
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
sub_rows, sub_ids = 0, []
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if r and r[0].strip():
            sub_rows += 1
            sub_ids.append(r[0].strip())
sub = set(sub_ids)
w('== 2. 台账 ==')
w('  行数 %d  唯一 id %d' % (sub_rows, len(sub)))
w('')

# ---------- 3. mined 全库扫描 ----------
MINED = ROOT + 'data/alpha_quality_analysis/mined/'
allj, ok, dup = [], 0, 0
seen = set()
for dp, dn, fn in os.walk(MINED):
    for x in fn:
        if not x.endswith('.json'):
            continue
        allj.append(os.path.join(dp, x))
recs = []
for p in allj:
    try:
        d = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid:
        continue
    if aid in seen:
        dup += 1
    seen.add(aid)
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    TO = i.get('turnover') or 0; R = i.get('returns') or 0
    tS = t.get('sharpe') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    recs.append(dict(aid=aid, S=S, F=F, TO=TO, R=R, tS=tS, fail=fa,
                     sub=aid in sub, path=os.path.basename(p)))
w('== 3. mined 全库 ==')
w('  json 文件 %d  解析成功 %d  唯一 id %d  重复 id %d' % (len(allj), len(recs), len(seen), dup))
w('  其中已在台账（已提交过）%d' % sum(1 for r in recs if r['sub']))
gate = [r for r in recs if not r['sub'] and r['S'] + r['F'] >= 4.0 and r['tS'] >= 1.25
        and not r['fail'] and r['F'] >= 1.8]
w('  未提交 + 过质量闸门(S+F>=4, tS>=1.25, 无FAIL, F>=1.8)：%d' % len(gate))
w('')

# ---------- 4. 过闸候选的 S / TO 分布 ----------
if gate:
    w('== 4. 过闸候选 S / F / TO 分布 ==')
    for k in ('S', 'F', 'TO', 'tS'):
        v = sorted(r[k] for r in gate)
        w('  %-3s 中位 %.3f 均值 %.3f p90 %.3f p99 %.3f max %.3f'
          % (k, v[len(v)//2], st.mean(v), v[int(len(v)*0.9)], v[int(len(v)*0.99)], v[-1]))
    w('')
    w('  == S 分桶（豁免线要求 S >= 1.10 x 对手S；对手 S 最高 3.45 -> 需 3.80）==')
    b = collections.Counter()
    for r in gate:
        s = r['S']
        kk = '>=3.80' if s >= 3.80 else ('>=3.66' if s >= 3.66 else ('>=3.30' if s >= 3.30 else ('>=3.00' if s >= 3.00 else '<3.00')))
        b[kk] += 1
    for kk in ['>=3.80', '>=3.66', '>=3.30', '>=3.00', '<3.00']:
        w('    %-8s %d' % (kk, b[kk]))
    w('')
    w('  == TO 分布（换手只经 Fitness 进入，分母地板 0.125）==')
    b2 = collections.Counter()
    for r in gate:
        to = r['TO']
        kk = '<=0.125(地板)' if to <= 0.125 else ('0.125-0.20' if to <= 0.20 else ('0.20-0.35' if to <= 0.35 else '>0.35'))
        b2[kk] += 1
    for kk in ['<=0.125(地板)', '0.125-0.20', '0.20-0.35', '>0.35']:
        w('    %-14s %d' % (kk, b2[kk]))
    w('')

# ---------- 5. 判决日志：实测 corr ----------
RIVAL = re.compile(r'([A-Za-z0-9]{6,12})\(S=([\d.]+),corr=([\d.]+)\)')
HEAD = re.compile(r'(?:\u2717|\u2605|\u2713|\?)\s+([A-Za-z0-9]{6,12})\s+(\S+?)\s+SF=([\d.]+)\s+S=([\d.]+)\s+corr_max=([\d.]+)')
allrec = {}
logs = 0
for x in sorted(os.listdir(ROOT + '_autologs')):
    if not re.match(r'exempt_.*\.log$', x):
        continue
    logs += 1
    for ln in io.open(ROOT + '_autologs/' + x, encoding='utf-8', errors='ignore'):
        m = HEAD.search(ln)
        if not m:
            continue
        aid, cid, SF, S, cmax = m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5))
        rivals = [(a, float(s), float(c)) for a, s, c in RIVAL.findall(ln)]
        if not rivals:
            continue
        allrec[aid] = dict(aid=aid, cid=cid, SF=SF, S=S, cmax=cmax, rivals=rivals)
w('== 5. 判决日志实测 corr（%d 个日志文件）==' % logs)
w('  解析到 %d 条（去重）' % len(allrec))
b3 = collections.Counter()
for r in allrec.values():
    c = r['cmax']
    kk = '<=0.685(直通)' if c <= 0.685 else ('0.685-0.70' if c <= 0.70 else ('0.70-0.80' if c <= 0.80 else ('0.80-0.90' if c <= 0.90 else '>0.90')))
    b3[kk] += 1
for kk in ['<=0.685(直通)', '0.685-0.70', '0.70-0.80', '0.80-0.90', '>0.90']:
    w('  %-14s %d' % (kk, b3[kk]))
ok70 = [r for r in allrec.values() if r['rivals'] and r['S'] >= 1.10 * max(x[1] for x in r['rivals'] if x[2] >= 0.70 or True)]
w('  按 0.70 口径已达豁免线（S >= 1.10 x max对手S）：%d 条' % len(ok70))
for r in ok70:
    w('    %s %-22s S=%.2f need=%.2f corr_max=%.4f' % (r['aid'], r['cid'], r['S'], 1.10 * max(x[1] for x in r['rivals']), r['cmax']))
w('  直通（corr_max<=0.685）：%d 条' % sum(1 for r in allrec.values() if r['cmax'] <= 0.685))
w('')

# ---------- 6. 结论行 ----------
w('== 6. 一句话结论 ==')
w('  本地 json 总产出 %d 条 → 唯一 %d 条 → 过质量闸门未提交 %d 条 → 实测过相关墙 %d 条'
  % (len(allj), len(seen), len(gate), sum(1 for r in allrec.values() if r['cmax'] <= 0.685)))

io.open(ROOT + '_autologs/_census.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
