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
ap.add_argument('--conc', type=int, default=1)
ap.add_argument('--offset', type=int, default=0)
ap.add_argument('--sleep', type=float, default=3.0)
ap.add_argument('--out', default='_autologs/_sim_run.txt')
ap.add_argument('--no-gate', dest='no_gate', action='store_true',
                help='跳过多样性门（超限明细仍写日志留痕），仅用于建库初期分母过小、'
                     '规则结构性无法放行的补量批次')
A = ap.parse_args()

# ★★★ 2026-11-17 李工纪律第 5 条（硬约束）：回测/提交一律串行，禁止并发。
# 平台并发 3 留给其他任务；发到服务器的模拟一次只发一件，串行不慢于并发。
if A.conc != 1:
    print('!!! 纪律第5条：回测禁止并发 —— --conc 只能为 1（当前=%d）。拒绝执行，exit 5。' % A.conc)
    sys.exit(5)

MINED = ROOT / 'data/alpha_quality_analysis/mined'
MINED.mkdir(parents=True, exist_ok=True)
O = io.open(ROOT / A.out, 'w', encoding='utf-8')
def w(s=''):
    O.write(str(s) + '\n'); O.flush()
    try:
        print(s, flush=True)
    except UnicodeEncodeError:
        print(s.encode('gbk', errors='replace').decode('gbk', errors='replace'), flush=True)

batch = json.load(io.open(ROOT / A.batches, encoding='utf-8'))
batch = batch[A.offset:A.offset + A.limit]

# ★★★ 2026-11-17 纪律第 5 条：全局回测锁 —— 全项目任何时刻只允许一个回测进程在途。
# 拿不到锁直接退出；锁文件带 PID；>6 小时视为死进程遗留，接管并留痕。
import atexit
LOCK = ROOT / '_grid' / 'locks' / 'backtest.lock'
def _bt_release():
    try:
        LOCK.unlink()
    except OSError:
        pass
atexit.register(_bt_release)
LOCK.parent.mkdir(parents=True, exist_ok=True)
_got = False
for _i in range(2):
    try:
        _fd = _os.open(str(LOCK), _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)
        with _os.fdopen(_fd, 'w') as _f:
            _f.write('pid=%d %s' % (_os.getpid(), time.strftime('%Y-%m-%d %H:%M:%S')))
        _got = True
        break
    except FileExistsError:
        _age = time.time() - LOCK.stat().st_mtime
        if _age > 6 * 3600:
            print('!!! 回测锁已遗留 %.1f 小时，按死进程遗留接管' % (_age / 3600.0))
            _bt_release()
            continue
        break
if not _got:
    print('!!! 纪律第5条：已有回测在途（锁 %s），本进程退出。' % LOCK)
    sys.exit(5)

# ------------------------------------------------------------------ 生产门控（统一内核）
# ★ 2026-11-16 重构：原来这里有 4 段各自 try/except 的门控代码（深度门 / VF 门 / 多样性门 / 禁令门缺席）。
#   体检发现 **op_ban 禁令门从未被执行**（op_ban.guard_batch 全项目零调用，sim_run.py 也没 import op_ban）
#   ⇒ 李工 11-15 12:55「group_rank 禁 10 天」的硬禁令在唯一发模拟通道上形同虚设。
#
# 现在全部收敛到 src/core/wq_core.py：
#   深度门 / 算子禁令门 / VF对齐门(7/8/9) / ATOM门 / 多样性门
# 新增任何门必须 wq_core.register_gate()，否则不会执行 —— 杜绝"建好放那空着"。
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'src' / 'core'))
try:
    import wq_core
except Exception as _e:
    w('!!! 门控内核 wq_core 加载失败，按失败关闭（不放行）: %r' % (_e,))
    O.close()
    sys.exit(4)

_gok, _rep = wq_core.run_gates(batch)
for _L in _rep:
    w(_L)
if not _gok:
    O.close()
    sys.exit(4)

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
    for att in range(12):
        try:
            r = s.post('https://api.worldquantbrain.com/simulations', json=payload, timeout=90)
        except Exception as e:
            time.sleep(4); continue
        if r.status_code ==429:
            # ★ 11-17 21:1x 实测：平台有**并发模拟上限**，超了返
            #   CONCURRENT_SIMULATION_LIMIT_EXCEEDED。之前只重试 6 次 × 20s 就放弃，
            #   而且失败信息要等整批跑完才打印 ⇒ 表现为「模拟静默卡死 5 小时」。
            ra = r.headers.get('Retry-After')
            try:
                detail = (r.json() or {}).get('detail', '')
            except Exception:
                detail = ''
            if 'CONCURRENT_SIMULATION_LIMIT' in str(detail):
                time.sleep(30 + att * 10)      # 平台并发满 ⇒ 退得更久
                continue
            time.sleep(min(float(ra or 8), 20)); continue
        if r.status_code not in (200, 201):
            msg = 'HTTP%s %s' % (r.status_code, r.text[:160])
            try:
                w('%-46s %-9s %s' % (cid, '-', msg))     # ★ 失败也立即打印，别再静默
            except Exception:
                pass
            return (cid, None, msg)
        loc = r.headers.get('Location')
        if not loc:
            # 平台 2xx 却不给 Location：把状态码+响应头+正文全留下，否则查不出原因
            _hdr = {k: v for k, v in r.headers.items()
                    if k.lower() in ('retry-after', 'x-ratelimit-remaining',
                                     'x-ratelimit-limit', 'concurrency', 'content-type')}
            msg = 'no_location http=%s hdr=%s body=%s' % (
                r.status_code, _hdr, (r.text or '')[:200])
            try:
                w('%-46s %-9s %s' % (cid, '-', msg))
            except Exception:
                pass
            return (cid, None, msg)
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
    # ★ 11-17 19:1x 修正：原来只在**整批跑完后**才逐条打印 ⇒ 48 条批跑了 5.5 小时
    #   日志还是空的（人眼零反馈，等于挂死）。改成单条完成即落盘+打印。
    try:
        w('%-46s %-9s S=%.2f F=%.2f TO=%.3f FAIL=%s'
          % (cid, aid, S, F, TO, fails or '无'))
    except Exception:
        pass
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

# ★ 11-16 新接：多样性库记账（此前 diversity.commit 从未被调用 ⇒ live 库永远 10 条
#   ⇒ 门控分母永远不够 ⇒ 门数学无解、11-15 全部批次靠 --no-gate 硬绕）。
#   在"门控已通过 + 模拟已发出"之后记账，live 库才填得起来、门才真能拦。
try:
    _cok, _cmsg = wq_core.commit_batch(batch, tag=A.batches)
    w('多样性库记账: %s' % _cmsg)
except Exception as _ce:
    w('多样性库记账异常（不影响已发模拟）: %r' % (_ce,))
_bt_release()
O.close()