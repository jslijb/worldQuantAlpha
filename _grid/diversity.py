# -*- coding: utf-8 -*-
"""diversity.py —— 本地多样性库 v2（7 维，SQLite）

李工 2026-11-15 指令：
  13:02「提交模拟的时候需要加一层，数据集，idea，算子，回测相关的参数等，多样性检查…
        从此刻开始建立本地多样性库…任何一个频次的阀值不能超过 10%…
        使用率始终是动态的」
  13:06「库建立好了，用研究顾问阶段提交的模拟的数据填充。记住多样性我们之前定义了
        7 个维度。你不能只搞算子哦」

7 个维度（AGENTS.md §多样化架构 v2 原文是「市场+idea+算子+universe+decay+中性化」；
市场因 8 进程各守一市而"定死"不计，按李工 13:02 点名的"数据集"补入，
并把"回测相关参数"里唯一没被覆盖的 truncation 补上，合成 7 维）：
  1 dataset        2 idea        3 operator     4 universe
  5 neutralization 6 decay       7 truncation
shell（外壳族）降为算子维的附属标记，不单列一维 —— 否则就成了"只盯算子"。

两种分母（本文件最重要的设计决定，已向李工报备）：
  · history 分母：研究顾问阶段 8569 条历史模拟。实测 TOP3000 占 79%、
    SUBINDUSTRY 占 77%、decay=10 占 58%。若拿它当门限分母，回灌后任何新 alpha
    都会被永久拒绝（死锁）。故 history 只作「用过/没用过」的基线，不参与门限。
  · live 分母：自 2026-11-15 起的新增使用，门限按它算。"分母涨了已到顶的项解禁"
    依然成立，且不会被历史锁死。
  `python diversity.py report --basis lifetime` 可看 lifetime 口径对照。

用法：
  python _grid/diversity.py init                # 登记 7 维可用库
  python _grid/diversity.py backfill <json>     # 用研究顾问阶段历史模拟填充
  python _grid/diversity.py report              # 谁用了多少次 / 还剩哪些没用
  python _grid/diversity.py gate <batch.json>   # 提交前拦截
  python _grid/diversity.py commit <batch.json> # 通过后记账
"""
import io
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DB = os.path.join(HERE, 'diversity.db')
DATA = os.path.join(ROOT, 'data', 'alpha_quality_analysis')
FIELD_MAP_PATH = os.path.join(HERE, '_field_ds_map.json')

DIMS = ('dataset', 'idea', 'operator', 'universe', 'neutralization', 'decay', 'truncation')
DIM_CN = {'dataset': '数据集', 'idea': 'idea', 'operator': '算子', 'universe': 'universe',
          'neutralization': '中性化', 'decay': 'decay', 'truncation': 'truncation'}
RULE = {d: 0.10 for d in DIMS}

EXEMPT_GROUPS = {'country', 'exchange', 'market', 'sector', 'industry', 'subindustry'}
KEYWORDS = {'if', 'else', 'and', 'or', 'not', 'rettype', 'driver', 'range', 'buckets',
            'constant', 'useStd', 'limit', 'sigma', 'hump', 'sensitivity', 'force',
            'std', 'weight', 'skipBoth', 'NaNGroup', 'longscale', 'shortscale'}

_FIELD_MAP = None


def field_map():
    global _FIELD_MAP
    if _FIELD_MAP is None:
        try:
            _FIELD_MAP = json.load(io.open(FIELD_MAP_PATH, encoding='utf-8'))
        except Exception:                                  # noqa: BLE001
            _FIELD_MAP = {}
    return _FIELD_MAP


# ---------------------------------------------------------------- 底层
def conn():
    c = sqlite3.connect(DB)
    c.execute("""CREATE TABLE IF NOT EXISTS dim_item(
        dim TEXT NOT NULL, item TEXT NOT NULL, source TEXT, added TEXT,
        PRIMARY KEY(dim, item))""")
    c.execute("""CREATE TABLE IF NOT EXISTS event(
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, cid TEXT, batch TEXT,
        dim TEXT, item TEXT, n INTEGER, basis TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS rule(
        dim TEXT PRIMARY KEY, share_cap REAL)""")
    for d, v in RULE.items():
        c.execute("INSERT OR REPLACE INTO rule(dim, share_cap) VALUES(?,?)", (d, v))
    c.commit()
    return c


def register(items, dim, source='auto'):
    c = conn()
    n = 0
    for it in items:
        cur = c.execute("INSERT OR IGNORE INTO dim_item(dim,item,source,added) VALUES(?,?,?,?)",
                        (dim, str(it), source, datetime.now().isoformat(timespec='seconds')))
        n += cur.rowcount
    c.commit()
    c.close()
    return n


def _items(dim):
    c = conn()
    r = [x[0] for x in c.execute("SELECT item FROM dim_item WHERE dim=?", (dim,))]
    c.close()
    return r


def _counts(dim, basis='live'):
    c = conn()
    if basis == 'lifetime':
        q, a = "SELECT item, SUM(n) FROM event WHERE dim=? GROUP BY item", (dim,)
    else:
        q, a = ("SELECT item, SUM(n) FROM event WHERE dim=? AND basis=? GROUP BY item",
                (dim, basis))
    d = {k: v for k, v in c.execute(q, a)}
    c.close()
    return d


# ---------------------------------------------------------------- 表达式 -> 7 维
_OP_RE = re.compile(r'\b([a-z][a-z0-9_]*)\s*\(')


def infer_dataset(code):
    """字段名反查数据集：全同 -> 该集；多个 -> MIXED:...；查不到 -> ?"""
    fm = field_map()
    hit = {}
    for tok in set(re.findall(r'[a-z][a-z0-9_]{2,}', code)):
        ds = fm.get(tok)
        if ds:
            hit[ds] = hit.get(ds, 0) + 1
    if not hit:
        return '?'
    if len(hit) == 1:
        return next(iter(hit))
    top = sorted(hit.items(), key=lambda kv: -kv[1])
    return 'MIXED:' + '+'.join(k for k, _ in top[:3])


def parse_alpha(a):
    code = a.get('code') or a.get('expr') or a.get('regular') or ''
    if isinstance(code, list):
        code = ' '.join(map(str, code))
    code = str(code)
    st = a.get('settings') or a.get('st') or {}

    ops = [o for o in _OP_RE.findall(code) if o not in KEYWORDS]
    ds = a.get('dataset') or infer_dataset(code)

    def pick(k, alt):
        v = st.get(k)
        if v is None:
            v = a.get(alt)
        return '?' if v is None else str(v)

    # idea：必须显式登记。
    # ★ 2026-11-16 修正：原先的兜底是 `cid.split('_')[0]` —— 台账 212 种 batch 前缀，
    #   等于"换批次名就能绕门"（李工批评"规则只是表面执行"的机械原因之一）。
    #   现在：取不到 idea_id 就记 '?'，由 gate 判违规（'?' 达到上限即拦批）。
    idea = a.get('idea_id') or a.get('idea') or a.get('kernel')
    if not idea:
        idea = '?'
    return {
        'dataset': {ds: 1},
        'idea': {idea: 1},
        'operator': {o: ops.count(o) for o in set(ops)},
        'universe': {pick('universe', 'uni'): 1},
        'neutralization': {pick('neutralization', 'neu'): 1},
        'decay': {pick('decay', 'dec'): 1},
        'truncation': {pick('truncation', 'trunc'): 1},
    }


# ---------------------------------------------------------------- 判定
def _cap_share(dim):
    c = conn()
    row = c.execute("SELECT share_cap FROM rule WHERE dim=?", (dim,)).fetchone()
    n = c.execute("SELECT COUNT(*) FROM dim_item WHERE dim=?", (dim,)).fetchone()[0]
    c.close()
    base = row[0] if row else 0.10
    return max(base, (1.0 / n) if n else 0.0), base, n


def gate(batch, basis='live', verbose=True):
    if not batch:
        return True, [], ['空批次']
    add = {}
    for a in batch:
        for dim, d in parse_alpha(a).items():
            add.setdefault(dim, {})
            for k, v in d.items():
                add[dim][k] = add[dim].get(k, 0) + v

    violations, lines = [], []
    for dim in DIMS:
        hist = _counts(dim, basis)
        share, base, N = _cap_share(dim)
        T = sum(hist.values()) + sum(add.get(dim, {}).values())
        if T == 0:
            lines.append('%-15s 无数据' % dim)
            continue
        # 上限次数 = max(ceil(10%*T), ceil(T/N))
        # 前者是李工的 10% 硬线；后者是"整数均分"下限——N 项不可能每项都少于 ceil(T/N)。
        # N>=10 时两者等价于 10%；N<10（中性化7/universe3/truncation4）时退化为均分，
        # 否则 10 条批次在中性化维数学上无解（2/10=20%>14.3%）。
        import math
        cap_cnt = max(math.ceil(share * T), math.ceil(T / N) if N else 0)
        worst, worst_i = 0.0, None
        for item, n in add.get(dim, {}).items():
            cnt = hist.get(item, 0) + n
            s = cnt / T
            if s > worst:
                worst, worst_i = s, item
            if cnt > cap_cnt:
                violations.append((dim, item, cnt, T, s, share))
        _capcnt = max(math.ceil(share * T), math.ceil(T / N) if N else 0)
        _worst_cnt = max([hist.get(k, 0) + v for k, v in add.get(dim, {}).items()] or [0])
        lines.append('%-15s 本批 %3d / 分母 %5d | 最重 %-16s %5.1f%% | 限 %.1f%% 且 <=%d 次 (库 %d 项) %s'
                     % (dim, sum(add.get(dim, {}).values()), T, str(worst_i)[:16],
                        worst * 100, share * 100, _capcnt, N,
                        'OK' if _worst_cnt <= _capcnt else 'FAIL'))
    if verbose:
        for L in lines:
            print(L)
        if violations:
            print('\n超限明细：')
            for dim, item, cnt, T, s, share in violations:
                print('  [%s] %s = %d/%d = %.1f%% > %.1f%%'
                      % (dim, DIM_CN.get(dim, dim), cnt, T, s * 100, share * 100))
    return not violations, violations, lines


def commit(batch, tag=None, basis='live'):
    ok, _, _ = gate(batch, basis=basis, verbose=False)
    if not ok:
        raise RuntimeError('批次未过多样性门，拒绝记账')
    c = conn()
    tag = tag or datetime.now().strftime('%Y%m%d_%H%M')
    ts = datetime.now().isoformat(timespec='seconds')
    for a in batch:
        cid = a.get('cid') or a.get('id') or ''
        for dim, d in parse_alpha(a).items():
            for k, v in d.items():
                c.execute("INSERT INTO event(ts,cid,batch,dim,item,n,basis) VALUES(?,?,?,?,?,?,?)",
                          (ts, cid, tag, dim, str(k), v, basis))
    c.commit()
    c.close()
    return len(batch)


# ---------------------------------------------------------------- 报表
def report(basis='live', dims=None, show_unused=True, top=12):
    dims = dims or DIMS
    out = []
    for dim in dims:
        live = _counts(dim, 'live')
        life = _counts(dim, 'lifetime')
        items = _items(dim)
        T, TL = sum(live.values()), sum(life.values())
        share, base, N = _cap_share(dim)
        used = [k for k in set(list(life) + list(live)) if k in items]
        unused = [k for k in items if life.get(k, 0) == 0 and live.get(k, 0) == 0]
        out.append('')
        out.append('=' * 78)
        out.append('[%s] %s   库 %d 项 | 历史用过 %d 项 | 从未用过 %d 项'
                   % (DIM_CN.get(dim, dim), dim, N, len(used), len(unused)))
        out.append('  历史累计 %d 次(不参与门限) | 当期分母 %d 次 | 份额上限 %.1f%%'
                   % (TL, T, share * 100))
        if TL:
            out.append('  %-26s %8s %8s %8s' % ('项', '历史', '当期', '当期份额'))
            for k, v in sorted(life.items(), key=lambda kv: -kv[1])[:top]:
                lv = live.get(k, 0)
                s = (lv / T) if T else 0.0
                out.append('  %-26s %8d %8d %7.1f%% %s%s'
                           % (str(k)[:26], v, lv, s * 100,
                              '#' * min(18, int(s * 100)),
                              ' <超限>' if s > share + 1e-9 else ''))
        try:
            from op_ban import active_bans
            _b = active_bans()
            if _b and dim == 'operator':
                out.append('  禁用中(不计入分母): ' + ', '.join(
                    '%s(%s~%s)' % (b[0], b[1], b[2]) for b in _b))
        except Exception:                                   # noqa: BLE001
            pass
        if show_unused and unused:
            out.append('  从未用过还可用的(%d): %s%s'
                       % (len(unused), ', '.join(sorted(unused)[:36]),
                          ' ...' if len(unused) > 36 else ''))
    return '\n'.join(out)


# ---------------------------------------------------------------- 初始化 / 回灌
def init():
    n = {}
    p = os.path.join(DATA, 'operators_usa.json')
    if os.path.exists(p):
        ops = [o['name'] for o in json.load(io.open(p, encoding='utf-8'))]
        try:
            from op_ban import is_banned
            ops = [o for o in ops if not is_banned(o + '(x)')]
        except Exception:                                   # noqa: BLE001
            pass
        n['operator'] = register(ops, 'operator', 'operators_usa.json')

    # 数据集池：优先用平台真实权限清单（GET /data-sets 拉到的 289 个），
    # 旧的 datasets_full.json 只有 14 个，会把 96% 的可用数据集漏在分母之外。
    p_perm = os.path.join(DATA, 'datasets_perm_usa.json')
    p = os.path.join(DATA, 'datasets_full.json')
    if os.path.exists(p_perm):
        n['dataset'] = register([o['id'] for o in json.load(io.open(p_perm, encoding='utf-8'))],
                                'dataset', 'datasets_perm_usa.json')
    elif os.path.exists(p):
        n['dataset'] = register([o['id'] for o in json.load(io.open(p, encoding='utf-8'))],
                                'dataset', 'datasets_full.json')

    try:
        mk = json.load(io.open(os.path.join(HERE, 'markets.json'), encoding='utf-8'))
        n['universe'] = register(sorted(mk.get('USA', {}).get('universes') or []),
                                 'universe', 'markets.json[USA]')
    except Exception as e:                                  # noqa: BLE001
        print('universe 登记失败', e)

    # COUNTRY 从池里剔除：USA/TOP3000 实测 POST 返回 HTTP400（不支持），
    # 留着只会虚增可选数、把实际集中度洗成合规（11-15 实测两次 400）。
    n['neutralization'] = register(
        ['NONE', 'MARKET', 'SECTOR', 'INDUSTRY', 'SUBINDUSTRY', 'STATISTICAL'],
        'neutralization', 'mine_grid.NEUTS[USA可用]')

    decays = {'0', '10', '15', '40', '45', '90'}
    try:
        har = json.load(io.open(os.path.join(ROOT, '_autologs', '_harvest_1113.json'),
                                encoding='utf-8'))
        decays |= {str(x['dec']) for x in har if x.get('dec') is not None}
    except Exception:                                       # noqa: BLE001
        pass
    n['decay'] = register(sorted(decays, key=lambda s: int(s)), 'decay', '历史实测取值')
    n['truncation'] = register(['0.01', '0.05', '0.08', '0.1'], 'truncation', '手填')

    try:
        sys.path.insert(0, os.path.join(ROOT, 'src', 'knowledge'))
        from idea_generator import MECHANISMS
        ids = [eid for m in MECHANISMS for eid, *_ in m.get('atoms', [])]
        n['idea'] = register(ids, 'idea', 'idea_generator.MECHANISMS')
    except Exception as e:                                  # noqa: BLE001
        print('idea 登记失败', e)
    print('登记结果（新增项数）:', n)


def backfill(path, limit=0):
    """用研究顾问阶段历史模拟填充。basis=history，不参与门限。"""
    har = json.load(io.open(path, encoding='utf-8'))
    if limit:
        har = har[:limit]
    c = conn()
    ts = datetime.now().isoformat(timespec='seconds')
    n_ev = 0
    for a in har:
        cid = a.get('aid') or a.get('cid') or ''
        for dim, d in parse_alpha(a).items():
            for k, v in d.items():
                c.execute("INSERT INTO event(ts,cid,batch,dim,item,n,basis) VALUES(?,?,?,?,?,?,?)",
                          (ts, cid, 'backfill_RC', dim, str(k), v, 'history'))
                n_ev += 1
    c.commit()
    c.close()
    return len(har), n_ev


# ---------------------------------------------------------------- CLI
if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if cmd == 'init':
        init()
        print(report(show_unused=False))
    elif cmd == 'backfill':
        cnt, ev = backfill(sys.argv[2])
        print('回灌 %d 条历史 alpha，写入 %d 条维度记录' % (cnt, ev))
        print(report(show_unused=False))
    elif cmd == 'report':
        basis = 'lifetime' if 'lifetime' in sys.argv else 'live'
        print(report(basis=basis))
    elif cmd in ('gate', 'commit'):
        batch = json.load(io.open(sys.argv[2], encoding='utf-8'))
        ok, v, _ = gate(batch)
        print('\n判定:', 'PASS' if ok else 'BLOCK (%d 处超限)' % len(v))
        if ok and cmd == 'commit':
            print('已记账', commit(batch, tag=os.path.basename(sys.argv[2])), '条')
    else:
        print(__doc__)
