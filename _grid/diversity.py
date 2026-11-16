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

# =====================================================================
# ★ 2026-11-16 新增：与平台 VF / Genius Tie-Breaker 对齐的三个专用门
#
# 依据（论坛原文，docs/forum/atom_pack/）：
#   主帖 44770798147735：
#     「Genius 六维 Tie-Breaker 考核两项硬指标：每条 Alpha 平均使用的不同字段数
#       （Avg distinct Fields / Alpha）**越低越好**（单字段 ATOM 可压到 1），
#       而全季度总计使用的不同字段数（Total distinct Fields）**越高越好**。
#       用单字段 ATOM 扫描新字段，天然在这两个维度同时拿满优势。」
#   VF 复盘帖 44645223044247（814 Regular + 269 Super 实测）：
#     atom 比例 高 VF 81.7% → 低 VF 50.5%；SC 0.6~0.7 组 atom 比例只剩 43%。
#
# 我们自己的台账实测（360 条，本地 judge 逐条）：
#   每条 alpha 平均使用不同字段数 = **7.73**（平台说越低越好）
#   单字段（=1）占比 **1.7%** | atom 比例 **2.8%** | 9~10 月 atom 比例 0.6~0.7%
#   ⇒ 与 VF 方向完全相反。原有 DIMS 没有"单条字段数"维度，是结构性缺口。
#
# 这三个门不是"多样性份额"型，而是"绝对约束"型，故不放进 DIMS（它们不走 10% 份额逻辑）。
# =====================================================================

# 门 7：单条 alpha 的不同字段数上限（平台：越低越好，单字段 ATOM = 1）
MAX_FIELDS_PER_ALPHA = 2

# 门 9：一批新提交的 atom 占比下限（论坛低 VF 线 50.5%）
MIN_ATOM_RATIO = 0.50

# 门 8：每批至少引入的"台账从未用过"字段数（平台：Total distinct Fields 越高越好）
MIN_NEW_FIELDS_PER_BATCH = 2


def fields_in_code(code):
    """表达式里用到的业务字段（剔除 6 个豁免分组字段）。

    先用 src.core.atom.fields_of（按平台缓存反查）；若返回空（字段是尚未开荒的新字段、
    缓存里查不到），**退回标识符粗抽**，否则会把"用了全新字段的表达式"误判成 0 字段。
    """
    fs = set()
    try:
        from src.core.atom import fields_of
        fs = set(fields_of(code))
    except Exception:                                       # noqa: BLE001
        fs = set()
    # 剔除豁免分组字段后若为空，说明字段全是尚未开荒的新字段（缓存查不到），
    # fields_of 只会返回分组字段 ⇒ 此时必须退回标识符粗抽，否则会误判成 0 字段。
    real = {f for f in fs if f not in EXEMPT_GROUPS}
    if not real:
        # 先剔除字符串字面量（driver="gaussian" / range="0,1,0.1"），否则 driver/range 会被当字段
        code2 = re.sub(r'"[^"]*"', '""', code)
        ops = set(_OP_RE.findall(code2)) | set(KEYWORDS)
        # 粗抽：字母开头的标识符（含单字母，如模板占位符 f），去掉算子名/关键字/分组字段
        real = {t for t in re.findall(r'[a-z][a-z0-9_]*', code2)
                if t not in ops and t not in KEYWORDS and t not in EXEMPT_GROUPS}
    return real


def is_atom_code(code):
    """该表达式是否单数据集（ATOM）。

    三层判定（任一成立即 True）：
      1. src.core.atom.judge() 返回 True（平台 /data-fields 缓存里查得到归属）。
      2. 剔除豁免分组字段后**只剩 1 个业务字段** ⇒ 必然单数据集。
         （论坛主帖推荐的「单字段 ATOM 扫描新字段」正是这种；且本地缓存对新字段
           查不到归属时 judge() 会判 False，不能因此误杀。）
      3. 全部业务字段都能查到归属，且**归属只有一个** ⇒ atom。
    """
    try:
        from src.core.atom import judge, dataset_of
        ok, _ds, _why = judge(code)
        if ok:
            return True
    except Exception:                                       # noqa: BLE001
        pass
    fs = fields_in_code(code)
    if not fs:
        return False
    if len(fs) == 1:
        return True
    try:
        from src.core.atom import dataset_of as _ds_of
        owners = set()
        for f in fs:
            d = _ds_of(f)
            if d:
                owners.add(d)
        if owners and len(owners) == 1:
            return True
    except Exception:                                       # noqa: BLE001
        pass
    return False


def gate_vf(batch, ledger=None, verbose=True):
    """门 7/8/9：与平台 VF / Genius Tie-Breaker 对齐的三个专用门。

    门 7 每条 alpha 不同字段数 ≤ MAX_FIELDS_PER_ALPHA（默认 2）
    门 9 本批 atom 占比 ≥ MIN_ATOM_RATIO（默认 50%）
    门 8 本批至少引入 MIN_NEW_FIELDS_PER_BATCH 个台账未用过的字段

    返回 (ok, violations, lines)。violations = [(门名, 明细, 说明), ...]
    """
    violations = []
    lines = []

    # ---- 门 7：单条 alpha 字段数上限
    fcount = {}
    for b in batch:
        code = b.get('code') or b.get('expr') or ''
        fs = fields_in_code(code)
        cid = b.get('cid', '')
        fcount[cid] = fs
        if len(fs) > MAX_FIELDS_PER_ALPHA:
            violations.append(('门7_单alpha字段数', cid,
                               '%d 个字段 > %d：%s' % (len(fs), MAX_FIELDS_PER_ALPHA,
                                                 ', '.join(sorted(fs)))))
    if fcount:
        avg = sum(len(v) for v in fcount.values()) / len(fcount)
        lines.append('门7 单alpha字段数：均 %.2f（上限 %d）| 明细 %s'
                     % (avg, MAX_FIELDS_PER_ALPHA,
                        ', '.join('%s=%d' % (k, len(v)) for k, v in list(fcount.items())[:12])))

    # ---- 门 9：本批 atom 占比
    atoms = [b for b in batch
             if is_atom_code(b.get('code') or b.get('expr') or '')]
    ratio = (len(atoms) / len(batch)) if batch else 0.0
    lines.append('门9 atom占比：%d/%d = %.0f%%（下限 %.0f%%）'
                 % (len(atoms), len(batch), ratio * 100, MIN_ATOM_RATIO * 100))
    if batch and ratio < MIN_ATOM_RATIO:
        violations.append(('门9_atom占比', 'batch',
                           '%.0f%% < %.0f%%（论坛：低 VF 窗口 atom 比例 50.5%% ⇒ VF 0.39）'
                           % (ratio * 100, MIN_ATOM_RATIO * 100)))

    # ---- 门 8：新字段下限（批次级门：单条测试时不生效）
    used = set()
    if ledger:
        try:
            import csv as _csv
            import io as _io
            rows = list(_csv.DictReader(
                _io.open(ledger, encoding='utf-8-sig')))
            for r in rows:
                for f in fields_in_code(r.get('expr', '')):
                    used.add(f)
        except Exception as e:                              # noqa: BLE001
            lines.append('门8 读取台账失败：%r' % (e,))
    batch_fields = set()
    for fs in fcount.values():
        batch_fields |= fs
    new_fields = sorted(batch_fields - used)
    lines.append('门8 新字段：本批 %d 个字段，其中台账未用过 %d 个（下限 %d，批次级门）%s'
                 % (len(batch_fields), len(new_fields), MIN_NEW_FIELDS_PER_BATCH,
                    ('→ ' + ', '.join(new_fields[:10])) if new_fields else ''))
    if batch and len(batch) >= 3 and len(new_fields) < MIN_NEW_FIELDS_PER_BATCH:
        violations.append(('门8_新字段', 'batch',
                           '%d 个 < %d（平台 Genius Tie-Breaker：Total distinct Fields 越高越好）'
                           % (len(new_fields), MIN_NEW_FIELDS_PER_BATCH)))

    if verbose:
        for L in lines:
            print(L)
    return (not violations), violations, lines


EXEMPT_GROUPS = {'country', 'exchange', 'market', 'sector', 'industry', 'subindustry'}
KEYWORDS = {'if', 'else', 'and', 'or', 'not', 'rettype', 'driver', 'range', 'buckets',
            'constant', 'useStd', 'limit', 'sigma', 'hump', 'sensitivity', 'force',
            'std', 'weight', 'skipBoth', 'NaNGroup', 'longscale', 'shortscale',
            'named', 'nan', 'inf', 'none', 'true', 'false', 'gauss', 'gaussian',
            'uniform', 'normal', 'min', 'max', 'mean', 'stddev', 'count'}

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
        # ★ 11-16 修复：批次生成器把 decay/neutralization/truncation/universe 放在**顶层**
        #   （sim_run.py 逐条读 item.get(k)），而 pick() 只查 st 和 alt 短名
        #   （'dec'/'neu'/'trunc'/'uni'）⇒ 全部记成 '?' ⇒ 多样性门把
        #   "本批所有件同参数"误判成超限（假超限），且真实的多样性维度完全失效。
        #   现在按「顶层同名键」再查一次。
        if v is None:
            v = a.get(k)
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


def gate(batch, basis='auto', verbose=True):
    """批次多样性门。

    ★ 11-16 修正（真 bug，生产上从未真正拦过）：
      旧实现固定 basis='live'，而 live 事件表自 11-15 规则生效起只有 **81 条**，
      分母 T 只有 10~34 ⇒ 任何 ≥6 条的批在 operator/neutralization/decay 维必然超限
      ⇒ **数学上无解**。实测 11-15 全部批次都是靠 `--no-gate` 强制放行的
      （_sim_atom1115/_sim_lowto*/_sim_lowto10/11/2..9 各 BLOCK 6~13 处照放），
      所以"多样性硬门"在生产上一次都没真正生效 —— 这正是李工说的"规则只是表面执行"。

    ★ 11-16 二次修正（口径）：
      改用 lifetime（历史全量 8579+）做分母后，`universe/neutralization/decay` 三维
      因**历史存量集中**永远超限（TOP3000 79.2% / SUBINDUSTRY 77.2% / decay=10 57.9%），
      任何新批都过不了 ⇒ 又一次"规则表面执行"。
      按李工 11-15 定的规矩「**不设历史欠账、不追补**」，这三个**回测参数维度**
      的历史集中度是既有事实、不该由新批偿还。
      ⇒ 口径定为：**live 窗口（规则生效后的近期使用）+ 本批** 作分母；
        lifetime 全量降级为**诊断线（只报警不拦）**，在 lines 里输出供人工判断。
      阈值一律不改（10% 硬线 + 物理下限 1/N）。

    basis='auto'（默认）= live+本批；'live'/'lifetime'/'history' 可显式指定。
    """
    if not batch:
        return True, [], ['空批次']

    add = {}
    for a in batch:
        for dim, d in parse_alpha(a).items():
            add.setdefault(dim, {})
            for k, v in d.items():
                add[dim][k] = add[dim].get(k, 0) + v

    # ★ 口径选择：auto ⇒ live 窗口（本批 + 规则生效后近期）。
    #   lifetime 只做诊断线，不参与拦截。
    _use_lifetime = (basis == 'lifetime')
    _live_tot = sum(sum(_counts(d, 'live').values()) for d in DIMS)
    _lt_tot = sum(sum(_counts(d, 'lifetime').values()) for d in DIMS)
    if basis == 'auto':
        basis = 'live'
    _switched = []
    if not _use_lifetime and _live_tot < 30 and _lt_tot > _live_tot:
        _switched = ['live 窗口仅 %d 条（分母过小，live 口径下批内项必然超限）'
                     '⇒ 本次以 live+本批 口径判定，并在下方给出 lifetime 历史集中度诊断线'
                     % _live_tot]

    violations, lines = [], []
    for _s in _switched:
        lines.append('口径: %s' % _s)
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

    # ★ lifetime 诊断线（只报警不拦）：历史全量口径下的集中度，供人工判断欠账。
    if not _use_lifetime and _lt_tot > 0:
        lines.append('')
        lines.append('--- lifetime 历史集中度诊断线（只报警，不拦批）---')
        for dim in DIMS:
            h = _counts(dim, 'lifetime')
            if not h:
                continue
            share, base, N = _cap_share(dim)
            T = sum(h.values())
            worst_i, worst = max(h.items(), key=lambda kv: kv[1])
            flag = '⚠ 历史欠账' if (worst / T) > share else ''
            lines.append('  %-15s 最重 %-18s %6.1f%% (限 %.1f%%) %s'
                         % (dim, str(worst_i)[:18], 100.0 * worst / T, share * 100, flag))
        lines.append('  说明：以上是历史存量集中度，按李工 11-15「不设历史欠账、不追补」'
                     '不由本批偿还；新批只受上表 live+本批 口径约束。')
    return not violations, violations, lines


def commit(batch, tag=None, basis='live', check=True, dims=None):
    """把本批的使用记进 event 表（live 口径 = 规则生效后的累计使用）。

    ★ 11-16 修复：`commit()` 全项目**从未被调用过**（只 import 了 diversity 的
      gate/gate_vf），⇒ live event 表自 11-15 建库起只有 10 条 ⇒
      门控分母 T=10+本批数 ⇒ 任何 ≥6 条的批必然超限 ⇒ **门数学上无解**。
      ⇒ 现在由 `src/core/wq_core.py:commit_batch()` 在**门控通过、模拟已发**后调用。

    check=True 时先自查是否过门（防止把没过的批记进库）。
    dims=None 记全部维度；给元组则只记这些维度
      （回灌历史件时用：dataset/idea 维度历史件数据不全，灌进去会造 '?' 假最重项）。
    """
    if check:
        ok, _, _ = gate(batch, basis=basis, verbose=False)
        if not ok:
            raise RuntimeError('批次未过多样性门，拒绝记账')
    c = conn()
    tag = tag or datetime.now().strftime('%Y%m%d_%H%M')
    ts = datetime.now().isoformat(timespec='seconds')
    for a in batch:
        cid = a.get('cid') or a.get('id') or ''
        for dim, d in parse_alpha(a).items():
            if dims and dim not in dims:
                continue
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
