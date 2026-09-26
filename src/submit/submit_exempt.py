# -*- coding: utf-8 -*-
"""submit_exempt.py —— 带"豁免线"的相关性判决提交器

0920 三次修正（实证 j2Az8n0E，结论见下）：**两条路都成立，且以"直通"为主**。
   曾经误判成"豁免线是假的"，原因是只看了本地对手名单、没看平台判决书。
   读全文 _verdict_j2Az8n0E.txt 后确认：其对手含 kqVp6wnO(S=2.51)，
   豁免线 = 1.1 × 2.51 = 2.761 > 候选 S=2.60 → **本就该被拒，规则没被推翻**。
   结论：
     ① 直通：本地 corr ≤ 0.685（平台 ≈ 本地 +0.005，仍 < 0.70）→ 稳。
     ② 豁免：本候选 S ≥ 1.10 × max(本地 corr≥0.66 对手的 S) → 平台放行。
        **前提是"对手集合必须收全"**（CORR_FLOOR=0.66 就是为此，收漏一个人
        就会把豁免线算低 → 本地放行、平台 403）。
   当前池子里 326 个达标候选：直通路 1 个、豁免路 0 个 —— 因为对手 S 普遍是 3.x 级，
   豁免线要 3.3+ 而我们候选封顶 2.83。所以现实里只有"降 corr"这一条路能走通。

两个阈值（0920 二次修正，务必分清）：
  · CORR_FLOOR  = 0.66  —— 收哪些对手进名单（本地低估会漏人，宁可多收）
  · CORR_DIRECT = 0.685 —— 判定能否直通（本地 +0.005 偏移后仍 < 0.70）

旧工具 auto_submit_passers.py 只实现了直通、把 corr>0.7 的全砍掉 —— 那部分没错；
真正的工具级根因是**把两个阈值混成一个变量**，导致本地 0.66~0.685 的合法直通候选被误杀。

用法：
  python src/submit/submit_exempt.py 'w218_*' --min-f 2.0 --max-to 0.20 --limit 10 --dry
  python src/submit/submit_exempt.py '*' --min-f 2.0 --max-to 0.20 --tag 0920-rank
"""
import os as _os, pathlib as _pl, sys, json, glob, time, subprocess, statistics as st

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

# —— 自带 UTF-8 日志：PowerShell 的 *> 重定向会把中文按 CP936 读成 UTF-16 搞乱，
#    所以判决记录由脚本自己落盘，不再依赖 shell 重定向。
_LOGF = _pl.Path('_autologs') / ('exempt_' + time.strftime('%m%d_%H%M%S') + '.log')
_LOGF.parent.mkdir(exist_ok=True)
_LF = open(_LOGF, 'a', encoding='utf-8')


def _log(*a, **kw):
    kw.pop('flush', None)
    s = ' '.join(str(x) for x in a)
    print(s, flush=True)
    _LF.write(s + '\n'); _LF.flush()

MINED = 'data/alpha_quality_analysis/mined'
PC = 'data/alpha_quality_analysis/pnl'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
POOL_S = 'data/alpha_quality_analysis/pool_s.json'
PY = sys.executable

ARGS = sys.argv[1:]
PAT = ARGS[0] if ARGS and not ARGS[0].startswith('-') else '*'


def opt(name, default):
    for a in ARGS:
        if a == name:
            return ARGS[ARGS.index(a) + 1]
        if a.startswith(name + '='):
            return a.split('=', 1)[1]
    return default


MIN_SF = float(opt('--min-sf', 4.0))
MIN_TS = float(opt('--min-ts', 1.25))
MIN_F = float(opt('--min-f', 0.0))
MAX_TO = float(opt('--max-to', 1.0))
LIMIT = int(opt('--limit', 10))
EXEMPT_RATIO = float(opt('--exempt', 1.10))
# ⚠ 0920 修正：地板必须比平台阈值 0.70 更低。
# 本地 corr 与平台有偏移（实测本地 0.7314 → 平台 0.7367），
# 用 0.70 当场板会**漏掉对手**：平台报 kqVp6wnO 的 corr 0.7184，本地可能只算到 0.69x，
# 于是对手集合少一人 → max 对手 S 取小 → 豁免线算低 → 本地放行、平台拒
# （实证 j2Az8n0E：本地只见 MPaPe0oo S2.30 判"需 2.53 放行"，平台实际 max 对手 S 是
#   kqVp6wnO 2.51 → 需 2.761 → 被拒）。用 0.66 宁可多收对手，保守判定。
CORR_FLOOR = float(opt('--corr-floor', 0.66))
# ⚠⚠ 0920 四次修正（**最终定稿**）：0.66 地板是对的，0.705 那个"修正"是 bug。
#   实证 blbpYLb6 判决书（_autologs/verdict_blbpYLb6.out）：
#     records = [mLmOPGap 0.9022/S2.57, vRjG1Jzw 0.7461/S1.79,
#                1YwKML56 0.7434/S2.21, **pwRwWoJ3 0.7052/S3.33**]
#     → 豁免线 = 1.1 × 3.33 = 3.663 > S 2.87 → 平台拒
#   而本地 pwRwWoJ3 的 corr 落在 [0.66, 0.705) —— 正是被 CORR_COUNT=0.705 剔掉的那条！
#   ⇒ 平台收录地板就是 0.70（含 0.7052），本地换算要留 +0.005~0.02 余量 → **收与算都用同一批**。
#   ⇒ CORR_COUNT 默认改回与 CORR_FLOOR 相同（0.66），保留参数只为诊断对比。
CORR_COUNT = float(opt('--corr-count', 0.66))
# ⚠ 0920 二次修正：**两个阈值必须拆开**，之前用一个变量把两件事搅在一起了。
#   · CORR_FLOOR  = 0.66 —— 只用于"收哪些对手进候选名单"（宁可多收，平台阈值 0.70，
#     本地低估时会漏人，j2Az8n0E 就是漏了 kqVp6wnO 才把豁免线算低）。
#   · CORR_DIRECT = 0.685 —— 用于判定"能不能直通"（本地 ≤0.685 + 平台偏移 ≈+0.005
#     → 平台 ≤0.690 < 0.70，安全）。把 floor 降到 0.66 时误把直通门槛也降到了 0.66，
#     结果本地 0.66~0.685 这批本该直通的候选全被塞进豁免分支按 1.1× 判死
#     （实证：A_SEC 本地 0.6650、A_w15 0.6805、A_win30 0.6810 —— 全被误杀）。
CORR_DIRECT = float(opt('--corr-direct', 0.685))
DRY = '--dry' in ARGS
TAG = opt('--tag', 'exempt')

import requests
sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
# ⚠ 0920 修正：原为裸 assert，本机沙箱代理（HTTPS_PROXY=127.0.0.1:xxxxx）抖动时
#   TLS 握手会抛 SSLEOFError 直接把整个脚本打死（实测连挂两次，13 分钟前的批次还正常）。
#   改为带退避重试。pnl() 早就有 8 次重试，只有这里是裸的 —— 补上。
_auth_ok = False
for _att in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication',
                     timeout=60).status_code == 201:
            _auth_ok = True
            break
    except Exception as _e:
        print('auth retry %d: %s %s' % (_att, type(_e).__name__, str(_e)[:80]))
    time.sleep(3 * (_att + 1))
assert _auth_ok, '认证连续 6 次失败（网络/代理抖动，非平台故障）'


def pnl(aid, refresh=False):
    f = _pl.Path(PC) / f'{aid}.json'
    if f.exists() and not refresh:
        return {k: float(v) for k, v in json.load(open(f, encoding='utf-8')).items()}
    j = None
    for att in range(8):
        r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        ra = r.headers.get('Retry-After')
        try:
            j = r.json()
            if j.get('records'):
                break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if not j or not j.get('records'):
        raise RuntimeError(f'pnl 端点未返回数据: {aid}')
    rec = j.get('records') or []
    d = {}
    prev = None
    for r in rec:
        cum = float(r[1])
        d[str(r[0])] = cum - (prev if prev is not None else cum)
        prev = cum
    json.dump(d, open(f, 'w', encoding='utf-8'))
    return d


def pool_ids():
    ids = []
    for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
        aid = ln.split(',')[0].strip('"')
        if aid and aid not in ids:
            ids.append(aid)
    return ids


def pool_s(ids):
    """池成员 Sharpe（平台实况，带缓存）"""
    cache = {}
    if _pl.Path(POOL_S).exists():
        try:
            cache = json.load(open(POOL_S, encoding='utf-8'))
        except Exception:
            cache = {}
    dirty = False
    for aid in ids:
        if aid in cache and cache[aid]:
            continue
        try:
            d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
            cache[aid] = (d.get('is') or {}).get('sharpe')
            dirty = True
            time.sleep(0.25)
        except Exception:
            pass
    if dirty:
        json.dump(cache, open(POOL_S, 'w', encoding='utf-8'), indent=1)
    return cache


def corr(a, b):
    ks = set(a) & set(b)
    if len(ks) < 300:
        return None
    ks = sorted(ks)
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v - mx) ** 2 for v in x) ** .5; sy = sum((v - my) ** 2 for v in y) ** .5
    if not sx or not sy:
        return None
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(ks))) / (sx * sy)


submitted = set(pool_ids())
cands = []
for f in sorted(glob.glob(f'{MINED}/{PAT}.json')):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid or aid in submitted:
        continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    TO = i.get('turnover') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < MIN_SF or (t.get('sharpe') or 0) < MIN_TS or fa:
        continue
    if F < MIN_F or TO > MAX_TO:
        continue
    # 排名导向（李工 0920）：F 已综合 sharpe×收益÷换手，按 F 排序才是提排名，
    # 旧口径按 S+F 排序会优先挑出高换手炸弹（TO 40%+，margin 仅 5~8bp）。
    cands.append(dict(cid=d.get('_cid', _pl.Path(f).stem), aid=aid, SF=S + F,
                      tS=t.get('sharpe'), S=S, F=F, TO=TO,
                      ret=i.get('returns') or 0, margin=i.get('margin') or 0,
                      decay=d.get('_decay'), neut=d.get('_neut')))

_log(f'匹配 {PAT}：达标候选 {len(cands)} 条（豁免比 {EXEMPT_RATIO}，直通线 {CORR_DIRECT}，'
     f'收对手地板 {CORR_FLOOR}，算线用 {CORR_COUNT}，F≥{MIN_F}，TO≤{MAX_TO*100:.0f}%）', flush=True)
if cands:
    _log('  候选池按 Fitness 排序（排名导向）：', flush=True)
    for c in sorted(cands, key=lambda x: -x['F'])[:12]:
        _log(f"    {c['cid']:26s} S={c['S']:.2f} F={c['F']:.2f} tS={c['tS']:.2f} "
             f"TO={c['TO']*100:5.1f}% margin={c['margin']*1e4:5.1f}bp", flush=True)
P = {}
miss = []
ids = pool_ids()
for aid in ids:
    try:
        P[aid] = pnl(aid)
    except Exception:
        miss.append(aid)
if miss:
    _log(f'⚠ 池子有 {len(miss)} 条取不到 PnL（多为刚提交、PnL 未发布）→ 跳过这些对手继续：{miss[:6]}', flush=True)
PS = pool_s(ids)
_log(f'池子 {len(P)} 条（S 已知 {sum(1 for v in PS.values() if v)} 条）', flush=True)

n_ok = 0
for c in sorted(cands, key=lambda x: -x['F']):
    if n_ok >= LIMIT:
        break
    aid = c['aid']
    try:
        x = pnl(aid)
    except Exception as e:
        _log(f"  {aid} PnL 取不到 {e}", flush=True)
        continue
    time.sleep(1.2)
    # 收集该候选所有 corr >= floor 的对手
    rivals = []
    for q, p in P.items():
        v = corr(x, p)
        if v is not None and v >= CORR_FLOOR:
            rivals.append((v, q, PS.get(q)))
    if not rivals:
        _log(f"  ✓ {aid} {c['cid']:26s} SF={c['SF']:.2f} tS={c['tS']:.2f} corr<{CORR_FLOOR} → 直通提交", flush=True)
        need = None
    else:
        # 真实最大 corr（不是"最高 S 对手"的 corr）—— 直通判据看的是这个
        cmax, qc, sc = max(rivals, key=lambda t: t[0])
        if cmax < CORR_DIRECT:
            rv = ' '.join('%s(S=%.2f,corr=%.4f)' % (q, s, v)
                          for v, q, s in sorted(rivals, key=lambda t: -t[0])[:5])
            _log(f"  ✓ {aid} {c['cid']:26s} SF={c['SF']:.2f} S={c['S']:.2f} corr_max={cmax:.4f}<{CORR_DIRECT} → 直通提交 | 最高对手[{rv}]", flush=True)
            need = None
        else:
            known = [r for r in rivals if r[2]]
            if not known:
                _log(f"  ? {aid} {c['cid']:26s} 对手 S 未知 → 跳过", flush=True)
                continue
            vmax, qmax, smax = max(known, key=lambda t: t[2])
            need = EXEMPT_RATIO * smax
            # 0920 三次修正：豁免线只用"平台口径"对手算（corr >= CORR_COUNT），
            # 不能把 0.66~0.705 的高 S 对手算进来（实测平台不算，见文件头）。
            cnt = [r for r in rivals if r[0] >= CORR_COUNT and r[2]]
            if not cnt:
                need_c = None
            else:
                _, qc2, sc2 = max(cnt, key=lambda t: t[2])
                need_c = EXEMPT_RATIO * sc2
            # 把全部对手列出来（0920 加）—— 只看 max 那条无法发现"漏对手"的 bug
            rv = ' '.join('%s(S=%.2f,corr=%.4f)' % (q, s, v)
                          for v, q, s in sorted(known, key=lambda t: -(t[2] or 0))[:5])
            rv2 = ' '.join('%s(S=%.2f,corr=%.4f)' % (q, s, v)
                           for v, q, s in sorted(cnt, key=lambda t: -(t[2] or 0))[:5])
            if need_c is None:
                _log(f"  ★ {aid} {c['cid']:26s} SF={c['SF']:.2f} S={c['S']:.2f} corr_max={cmax:.4f} "
                     f"平台口径(corr>={CORR_COUNT})对手为空(旧口径 need={need:.2f}) → 豁免放行 | 旧名单[{rv}]", flush=True)
            elif c['S'] < need_c:
                _log(f"  ✗ {aid} {c['cid']:26s} SF={c['SF']:.2f} S={c['S']:.2f} corr_max={cmax:.4f} "
                     f"撞{qc2}(S={sc2}) 需≥{need_c:.2f}(旧口径需≥{need:.2f}) → 不够 | 有效对手[{rv2}] 全名单[{rv}]", flush=True)
                continue
            else:
                _log(f"  ★ {aid} {c['cid']:26s} SF={c['SF']:.2f} S={c['S']:.2f} corr_max={cmax:.4f} "
                     f"撞{qc2}(S={sc2}) 需≥{need_c:.2f}(旧口径需≥{need:.2f}) → 豁免放行 | 有效对手[{rv2}]", flush=True)
    if DRY:
        continue
    r = subprocess.run([PY, 'src/submit/submit_v3.py', aid, f'{TAG}-{c["cid"]}'],
                       capture_output=True, text=True, timeout=600)
    tail = (r.stdout or '').strip().splitlines()
    _log('    ' + (tail[-1] if tail else (r.stderr or '')[:200]), flush=True)
    if 'ACCEPTED' in (r.stdout or ''):
        n_ok += 1
        submitted.add(aid)
        P[aid] = x
        PS[aid] = c['S']
        json.dump(PS, open(POOL_S, 'w', encoding='utf-8'), indent=1)
    time.sleep(3)

_log(f'submit_exempt 完成：本轮提交 {n_ok} 条', flush=True)
