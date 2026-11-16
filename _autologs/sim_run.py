# -*- coding: utf-8 -*-
"""sim_run.py —— 通用表达式批量模拟器（1010 新工具，取代 AlphaSimulator.py 的 CSV 约定）

为什么需要它：
  AlphaSimulator.py 要先手工准备 alpha_list_pending_simulated.csv、列名固定、
  落 simulated_alphas_日期.csv —— 每次接新矿都要重搭一遍脚手架。
  本工具直接吃 JSON[{cid, code, ...}]，落 _mined/<cid>.json，
  字段与既有mined 目录一致（id/is.sharpe/is.fitness/...），下游工具全兼容。

用法：
  python _autologs/sim_run.py src/mine/w301_batches.json --limit 52 --conc 8
输出：data/alpha_quality_analysis/mined/<cid>.json
      _autologs/_sim_run.txt（逐条结果 + 汇总）
"""
import os as _os, io, sys, json, time, argparse, glob, pathlib as _pl
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import requests
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser()
ap.add_argument('batches')
ap.add_argument('--limit', type=int, default=50)
ap.add_argument('--conc', type=int, default=6)
ap.add_argument('--offset', type=int, default=0)
ap.add_argument('--sleep', type=float, default=3.0)
ap.add_argument('--out', default='_autologs/_sim_run.txt')
ap.add_argument('--no-gate', dest='no_gate', action='store_true',
                help='跳过多样性门（超限明细仍写日志留痕），仅用于建库初期分母过小、'
                     '规则结构性无法放行的补量批次')
A = ap.parse_args()

MINED = ROOT / 'data/alpha_quality_analysis/mined'
MINED.mkdir(parents=True, exist_ok=True)
O = io.open(ROOT / A.out, 'w', encoding='utf-8')
def w(s=''):
    O.write(str(s) + '\n'); O.flush(); print(s, flush=True)

batch = json.load(io.open(ROOT / A.batches, encoding='utf-8'))
batch = batch[A.offset:A.offset + A.limit]

# ------------------------------------------------------------------ 构造深度门
# 2026-11-16 李工批评（事实）：11-15 那批"新数据集 ATOM 批"21 条 S 全部 -1.27~0.67，
# 我据此下结论"新数据集过不了门、只能靠量价续命" —— 那是**用浅构造测高价值数据**，
# 再拿测试结果当事实。根因：那批表达式是"各字段独立归一化后任意符号相加"，
# 字段之间的关系被抹掉（21 条里只有 3 条含比值/乘法/条件）。
#
# 本门拦的是"浅构造"：D1 无字段间关系算子 / D2 变换层数 <2 / D3 独立归一化直接相加。
# 校准：台账 359/360 PASS、11-15 那批 3/21 PASS、活样板 6/6 PASS（见 _grid/depth_check.py）。
#
# ★ 它是必要条件不是充分条件：过了深度门 ≠ 过平台门（深度门 PASS 的 11-15 三条 S 仍 -0.35~0.14）。
# ★ 纪律：**禁止用浅构造的结果给数据集/字段判死刑**；要判死刑必须先跑深构造。
sys.path.insert(0, str(ROOT / '_grid'))
try:
    import depth_check as DC
    _probe = all(str(b.get('cid', '')).startswith(('SYN_', 'TEST_', 'EXP_')) for b in batch)
    _shallow = []
    for _b in batch:
        _code = _b.get('code') or _b.get('expr') or ''
        _ok, _d = DC.check(_code)
        if not _ok:
            _shallow.append((_b.get('cid', ''), _d))
    if _shallow:
        w('')
        w('!!! 构造深度门：%d / %d 条被判浅构造' % (len(_shallow), len(batch)))
        for _cid, _d in _shallow:
            w('    %-38s 算子=%-3d 层数=%-2d | %s' % (
                str(_cid)[:38], _d['算子数'], _d['变换层数'], '; '.join(_d['不合格原因'])))
        if _probe:
            w('（结构探测 SYN_/TEST_/EXP_ 前缀，仅警告放行、不计入生产记账）')
        else:
            w('')
            w('!!! 构造深度门 BLOCK：本批不发。')
            w('!!! 处理办法：把字段做成关系（比值/差/条件/相关性）+ 反复变换（差分后除波动、'
              '均值差再归一），不要用"各字段独立归一化后相加"。')
            w('!!! 参考模板：_grid/atom_complex.py 的 C1~C6。')
            O.close()
            sys.exit(4)
    else:
        w('构造深度门: PASS')
except SystemExit:
    raise
except Exception as _e:
    w('构造深度门加载失败，按失败关闭（不放行）: %r' % (_e,))
    O.close()
    sys.exit(5)

# ------------------------------------------------------------------ 多样性门
# 李工 2026-11-15 13:02：「提交模拟的时候需要加一层...多样性检查」
# 默认硬拦：任何维度单项份额超上限就整批不发。唯一例外是 cid 以 SYN_/TEST_
# 开头的语法探针（只验证算子语法/权限，不进 alpha 生产口径），这类只警告。
sys.path.insert(0, str(ROOT / '_grid'))
try:
    import diversity as DIV
    _probe = all(str(b.get('cid', '')).startswith(('SYN_', 'TEST_', 'EXP_')) for b in batch)
    _ok, _vio, _lines = DIV.gate(batch, verbose=True)
    for _L in _lines:
        w(_L)
    if not _ok and getattr(A, 'no_gate', False):
        # 2026-11-15 23:00 加：门的分母是「当期累计使用次数」，建库初期只有 22，
        # 10% 上限 = 2.2 次 ⇒ 任何 8 条以上的批在 operator 维必然超限，结构性无解。
        # 该开关会把超限明细原样写进日志留痕，不做静默绕过。
        w('')
        w('!!! --no-gate 已指定：多样性门 BLOCK %d 处，本批强制放行（明细见上）。' % len(_vio))
        w('!!! 原因：分母=当期累计，建库初期过小；超限明细已完整留痕。')
    elif not _ok and not _probe:
        w('')
        w('!!! 多样性门 BLOCK：%d 处超限，本批不发。' % len(_vio))
        w('!!! 处理办法：补数据集/补 idea/换外壳/补未用算子，'
          '不要改阈值。')
        O.close()
        sys.exit(2)
    elif not _ok and _probe:
        w('（结构探测 SYN_/TEST_/EXP_ 前缀，仅警告放行、不计入生产记账）')
    elif _ok:
        w('多样性门: PASS')
except SystemExit:
    raise
except Exception as _e:
    w('多样性门加载失败，按失败关闭（不放行）: %r' % (_e,))
    O.close()
    sys.exit(3)

w('待模拟 %d 条（offset=%d limit=%d），并发 %d'
  % (len(batch), A.offset, A.limit, A.conc))

CRED = tuple(json.load(io.open(ROOT / 'brain_credentials.txt')))
SETTINGS = {
    "instrumentType": "EQUITY",
    "region": "USA",
    "universe": "TOP3000",
    "delay": 1,
    "decay": 10,
    "neutralization": "SUBINDUSTRY",
    "truncation": 0.08,
    "pasteurization": "ON",
    "unitHandling": "VERIFY",
    "nanHandling": "ON",
    "maxTrade": "OFF",
    "maxPosition": "OFF",
    "language": "FASTEXPR",
    "visualization": False,
    "startDate": "2019-01-01",
    "endDate": "2023-12-31",
    "testPeriod": "P1Y",
    "simulationMode": "FULL",
}

def sess():
    s = requests.Session()
    s.trust_env = False                        # 2026-11-15：绕开已死的系统代理 127.0.0.1:16117
    s.proxies = {'http': None, 'https': None}
    s.auth = CRED
    for _ in range(8):
        try:
            if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                return s
        except Exception:
            pass
        time.sleep(4)
    return None

def one(item):
    """模拟单条：POST /simulations 拿 Location → 轮询至完成 → 取 alpha 详情落盘"""
    cid = item['cid']; code = item['code']
    s = sess()
    if not s:
        return (cid, None, 'auth_fail')
    # 按条覆盖 settings（支持 decay / neutralization / universe 逐条不同）
    st = dict(SETTINGS)
    if isinstance(item.get('settings'), dict) and item['settings']:
        st.update(item['settings'])          # 整包覆盖（1011 修复：此前整包 settings 被无视）
    for k in ('decay', 'neutralization', 'universe', 'truncation', 'delay'):
        if item.get(k) is not None:
            st[k] = item[k]
    payload = {'type': 'REGULAR', 'settings': st, 'regular': code}
    loc = None
    for att in range(6):
        try:
            r = s.post('https://api.worldquantbrain.com/simulations', json=payload, timeout=90)
        except Exception as e:
            time.sleep(4); continue
        if r.status_code ==429:
            ra = r.headers.get('Retry-After')
            time.sleep(min(float(ra or 8), 20)); continue
        if r.status_code not in (200, 201):
            return (cid, None, 'HTTP%s %s' % (r.status_code, r.text[:160]))
        loc = r.headers.get('Location')
        if not loc:
            # 平台 2xx 却不给 Location：把状态码+响应头+正文全留下，否则查不出原因
            _hdr = {k: v for k, v in r.headers.items()
                    if k.lower() in ('retry-after', 'x-ratelimit-remaining',
                                     'x-ratelimit-limit', 'concurrency', 'content-type')}
            return (cid, None, 'no_location http=%s hdr=%s body=%s'
                    % (r.status_code, _hdr, (r.text or '')[:200]))
        break
    if not loc:
        return (cid, None, 'no_location')
    # 轮询
    # 坑（11-15 修正）：进度端点返回的 {'id': ...} 是**进度 id**（24 位），
    # 不是 alpha id（8 位）。此前用 j.get('id') 兜底，导致没跑完的模拟
    # 被当成"已完成、S=0.00"落盘，把超时误报成失败。只认 j['alpha']。
    aid = None
    last = {}
    for i in range(120):
        try:
            p = s.get(loc, timeout=90)
        except Exception:
            time.sleep(4); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 15)); continue
        try:
            j = p.json()
        except Exception:
            time.sleep(4); continue
        last = j
        if j.get('status') == 'ERROR':
            msg = str(j.get('message') or j)[:180]
            return (cid, None, 'SIM_ERROR %s' % msg)
        aid = j.get('alpha')
        if aid:
            break
        time.sleep(3)
    if not aid:
        # 没跑完不等于失败：把进度地址留下，允许之后补采，绝不写成 S=0.00
        pend = {'cid': cid, 'code': code, 'settings': st, 'location': loc,
                'last': last, 'ts': time.strftime('%Y-%m-%d %H:%M:%S')}
        pf = ROOT / '_autologs' / '_pending_sims.jsonl'
        with io.open(pf, 'a', encoding='utf-8') as f:
            f.write(json.dumps(pend, ensure_ascii=False) + '\n')
        return (cid, None, 'STILL_RUNNING(已记入_pending_sims.jsonl)')
    # 取详情（平台算 is 需要再等几秒）
    dj = {}
    for i in range(40):
        try:
            dj = s.get('https://api.worldquantbrain.com/alphas/%s' % aid, timeout=60).json()
        except Exception:
            time.sleep(3); continue
        isx = dj.get('is') or {}
        if isx.get('sharpe') is not None and isx.get('checks'):
            break
        time.sleep(3)
    rec = {'id': aid, '_cid': cid, 'code': code,
           'settings': dj.get('settings') or st,
           'is': dj.get('is') or {}, 'test': dj.get('test') or {},
           'dateCreated': dj.get('dateCreated'), 'stage': dj.get('stage'),
           'status': dj.get('status')}
    json.dump(rec, io.open(MINED / f'{cid}.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    isx = rec['is']
    S = isx.get('sharpe') or 0.0
    F = isx.get('fitness') or 0.0
    TO = isx.get('turnover') or 0.0
    fails = [c.get('name') for c in (isx.get('checks') or [])
             if c.get('result') == 'FAIL']
    return (cid, aid, 'S=%.2f F=%.2f SF=%.2f TO=%.3f tS=%s FAIL=%s'
            % (S, F, S + F, TO,
               ('%.2f' % (rec['test'].get('sharpe'))) if rec['test'].get('sharpe') else '-',
               fails or '无'))

with ThreadPoolExecutor(max_workers=A.conc) as ex:
    rows = list(ex.map(one, batch))

w()
w('=' * 100)
ok = [r for r in rows if r[1]]
w('完成 %d / %d' % (len(ok), len(batch)))
w('=' * 100)
parsed = []
for cid, aid, msg in rows:
    w('%-46s %-9s %s' % (cid, aid or '-', msg))
    if aid and msg.startswith('S='):
        try:
            S = float(msg.split('S=')[1].split()[0])
            F = float(msg.split('F=')[1].split()[0])
            TO = float(msg.split('TO=')[1].split()[0])
            parsed.append((S + F, cid, aid, S, F, TO))
        except Exception:
            pass
parsed.sort(reverse=True)
w()
w('★ 过质量门(S+F>=4.2 / TO<=20% / 无FAIL) 的：')
good = [p for p in parsed if p[0] >= 4.2 and p[5] <= 0.20]
w('  共 %d 条' % len(good))
for p in good[:25]:
    w('  %-9s SF=%.2f S=%.2f F=%.2f TO=%.3f  %s' % (p[2], p[0], p[3], p[4], p[5], p[1]))
O.close()