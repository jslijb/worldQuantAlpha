# -*- coding: utf-8 -*-
"""mech_gate.py — 机制去重门（2026-11-15）

╔══════════════════════════════════════════════════════════════════════════╗
║ ⚠️ 判据已作废（2026-11-15 21:3x 实测推翻），请改用 _grid/corr_gate.py    ║
║                                                                          ║
║ 证伪证据（_grid/replay_corr.py，341 条真实 PnL，1235 日窗口）：           ║
║   字段 Jaccard>=0.5 判为「同源」的 20 条：两两 PnL corr 中位 0.2718，     ║
║                                          组合 Sharpe 4.176              ║
║   判为「跨源」的 20 条（20 个不同字段族各 1 条）：                        ║
║                                          两两 PnL corr 中位 0.3309，     ║
║                                          组合 Sharpe 3.747              ║
║   ⇒ 字段同源的 PnL 反而更分散；「字段跨源」策略组合 Sharpe 五组最差      ║
║     （3.494，低于随机 4.090）。字段集合不是 PnL 相关的代理。              ║
║                                                                          ║
║ 源数口径也随之作废：字段口径 63 源（最大 268 条 78.6%），                 ║
║                     PnL corr>=0.7 口径 274 源（最大 17 条 5.0%）。       ║
║                                                                          ║
║ 保留用途：只做「字段重复度粗筛」，帮人看这条表达式在字段层像不像旧件。    ║
║            **不得用它放行或拦截提交。** 放行判据见 corr_gate.py。         ║
║ 详细论证：docs/methodology/DeltaS对账_组合增量门槛实测_20261115.md §6     ║
╚══════════════════════════════════════════════════════════════════════════╝

原始设计说明（保留，供追溯）：
    实测 355 条已提交 alpha 只来自 70 个字段族（Jaccard>=0.5），最大一族占 275 条（77.5%）。
    selfCorr 中位 0.6467，>0.60 的占 72.5%。
    病根不是单条质量（S 中位 2.30 / F 1.90 / margin 28.9bps 全都达标），
    是「同一个机制被交了 275 次」。旧的门全是判单条指标，没有一道判「这条是不是新的」。

它做什么：
    给一条表达式，算出它的「机制指纹」= 数据字段集合（剔除 pv1 通用字段与 6 个豁免分组字段），
    然后与台账里已提交的全部 alpha 比对，返回：
      - 最像的那条 alpha + Jaccard
      - 该候选属于哪个已有机制（机制清单里的编号）
      - 判定：NEW / BORDER / DUPLICATE

判定线（依据 docs/methodology/Alpha挖掘法_从24篇置顶帖反推_20261115.md §4.2）：
    Jaccard < 0.30   NEW        新机制，可交
    0.30 ~ 0.50      BORDER     同族不同表述，只允许「该族已交 <= 2 条」时通过
    >= 0.50          DUPLICATE  同机制，禁交

用法：
    python _grid/mech_gate.py "group_rank(ts_zscore(fnd6_xrent/assets,60),subindustry)"
    python _grid/mech_gate.py --file cands.json          # [{"cid":..,"code":..}, ...]
    python _grid/mech_gate.py --file cands.json --top 5  # 每条打印最像的 5 条

依赖：data/alpha_quality_analysis/all_fields_usa_top3000.json（13,373 字段）+ 台账 CSV
⚠ 字段表是 USA/TOP3000 的。跑 EUR/ASI 的候选时，未收录的字段会被漏掉 —— 此时结果偏乐观，
  脚本会打印「未识别字段数」提醒，不要忽略。
"""
import argparse
import collections
import csv
import io
import json
import os
import re
import sys

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS_JSON = os.path.join(PROJ, 'data', 'alpha_quality_analysis', 'all_fields_usa_top3000.json')
LEDGER = os.path.join(PROJ, 'data', 'alpha_quality_analysis', 'SUBMITTED_LEDGER.csv')

# pv1 通用字段 + 官方豁免的 6 个分组字段 —— 不构成机制指纹
DROP = {
    'close', 'open', 'high', 'low', 'volume', 'vwap', 'returns', 'cap', 'adv20',
    'sharesout', 'dividend', 'split', 'country', 'exchange', 'market', 'sector',
    'industry', 'subindustry', 'currency',
}


def load_fields(path=FIELDS_JSON):
    d = json.load(io.open(path, encoding='utf-8'))
    # 结构: {field_id: {"id":..,"ds":..,"type":..,"cov":..,"uc":..}}
    return d


def make_matcher(fields):
    toks = sorted([k for k in fields if len(k) >= 3], key=len, reverse=True)
    pat = re.compile(r'(?<![A-Za-z0-9_])(' + '|'.join(re.escape(t) for t in toks) + r')(?![A-Za-z0-9_])')
    return pat


def fingerprint(code, pat, fields):
    """返回 (机制指纹, 全字段指纹, 数据集集合, 未识别 token 数)。

    机制指纹 = 字段集合剔除 pv1 通用字段（否则任何含 close 的表达式都会互相撞）。
    全字段指纹 = 不剔除。纯价量表达式机制指纹为空时，退用全字段指纹 —— 这样所有
    纯 pv1 表达式会互相判同族，这是对的：它们本来就是同一个数据集。

    未识别 token：表达式里像字段名但不在字段表中的标识符（排除算子名）。
    这是「字段表不全」的告警信号，不是错误。
    """
    fs_all = set(m.group(1) for m in pat.finditer(code or ''))
    fs = fs_all - DROP
    base = fs if fs else fs_all
    dss = set(fields[x]['ds'] for x in base if x in fields and 'ds' in fields[x])
    ops = _known_ops()
    unknown = 0
    for t in re.findall(r'[A-Za-z_][A-Za-z0-9_]{2,}', code or ''):
        if t in fields or t in ops or t in DROP:
            continue
        unknown += 1
    return fs, fs_all, dss, unknown


_OPS = None


def _known_ops():
    global _OPS
    if _OPS is None:
        _OPS = set('''
        abs add arctan arc_tan arcsin arccos ceiling divide exp floor fraction inverse log
        log_diff max min multiply power reverse sign signed_power sqrt subtract densify
        nan_mask nan_out nan_to_zero purge replace s_log_1p sigmoid tanh bucket vec_avg
        vec_sum if_else is_nan less greater equal and or not filter trade_when kth_element
        rank zscore scale winsorize quantile normalize group_rank group_zscore group_neutralize
        group_scale group_mean group_sum group_max group_min group_std_dev group_count
        group_backfill group_extra ts_arg_max ts_arg_min ts_av_diff ts_backfill ts_corr
        ts_count_nans ts_covariance ts_decay_exp_window ts_decay_linear ts_delay ts_delta
        ts_ir ts_kurtosis ts_max ts_max_diff ts_mean ts_median ts_min ts_min_max_cps
        ts_min_max_diff ts_moment ts_partial_corr ts_percentage ts_product ts_quantile
        ts_rank ts_regression ts_returns ts_scale ts_skewness ts_std_dev ts_step ts_sum
        ts_target_tvr_decay ts_target_tvr_hump ts_zscore ts_entropy ts_theilsen ts_triple_corr
        ts_count ts_entropy ts_co_kurtosis ts_co_skewness ts_corr ts_covariance
        hump hump_decay vec_ir vec_max vec_min vec_count vec_kurtosis vec_skewness
        vec_powersum vec_norm regression_neut vector_neut vector_proj inst_pnl convert
        trade_when last_diff_value days_from_last_change generate_stats combo_a
        stats group_cartesian_product
        '''.split())
    return _OPS


def load_ledger():
    rows = list(csv.reader(io.open(LEDGER, encoding='utf-8-sig')))
    hdr = [h.strip() for h in rows[0]]
    idx = {h: i for i, h in enumerate(hdr)}
    out = []
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        out.append(dict(id=r[idx['id']], expr=r[idx['expr']],
                        S=r[idx['S']], F=r[idx['F']],
                        d=(r[idx['dateSubmitted']] or '')[:10]))
    return out


def jac(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def judge(code, fields, pat, ledger_fp, top=3, border_max_in_family=2):
    fs, fs_all, dss, unknown = fingerprint(code, pat, fields)
    base = fs if fs else fs_all
    if not base:
        return dict(verdict='NO_FIELD', jaccard=0.0, nearest=None, n_fields=0,
                    datasets=[], unknown=unknown, family_size=0, note='表达式里没识别到任何数据字段')
    scored = sorted(((jac(base, x['fs']), x) for x in ledger_fp), key=lambda t: -t[0])
    best_j, best = scored[0] if scored else (0.0, None)
    fam = [x for j, x in scored if j >= 0.5]
    if best_j >= 0.5:
        verdict = 'DUPLICATE'
    elif best_j >= 0.3:
        verdict = 'BORDER' if len(fam) < border_max_in_family else 'DUPLICATE'
    else:
        verdict = 'NEW'
    return dict(verdict=verdict, jaccard=round(best_j, 4), nearest=best, n_fields=len(base),
                datasets=sorted(dss), unknown=unknown, family_size=len(fam),
                pv_only=(not fs), top=[(round(j, 4), x) for j, x in scored[:top]])


def fmt(res, code):
    v = res['verdict']
    icon = {'NEW': '✓ NEW', 'BORDER': '~ BORDER', 'DUPLICATE': '✗ DUPLICATE', 'NO_FIELD': '? NO_FIELD'}[v]
    print('%s  jaccard=%.4f  fields=%d  datasets=%s  family=%d' % (
        icon, res['jaccard'], res['n_fields'], '+'.join(res['datasets']) or '-',
        res['family_size']))
    if res['unknown']:
        print('       ⚠ 未识别标识符 %d 个（字段表可能不含该区字段，结果偏乐观）' % res['unknown'])
    if res.get('pv_only'):
        print('       （纯 pv1 表达式：机制指纹为空，按全部字段判定 —— 同族 pv 会互相撞，这是对的）')
    for j, x in res.get('top') or []:
        print('       %.3f  %-12s %s  %s' % (j, x['id'], x['d'], (x['expr'] or '')[:90]))
    if v == 'NEW':
        print('       → 新机制，可进下一步（相关性 + 组合增量 + 单条质量）')
    elif v == 'BORDER':
        print('       → 同族不同表述。仅当该族已交 < %d 条才放行，否则改机制' % 2)
    elif v == 'DUPLICATE':
        print('       → 禁交。想留这条就得换字段族，不是换参数')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('code', nargs='?', help='单条表达式')
    ap.add_argument('--file', help='JSON: [{"cid":..,"code":..}, ...]')
    ap.add_argument('--top', type=int, default=3)
    ap.add_argument('--quiet', action='store_true', help='只打汇总')
    a = ap.parse_args()

    fields = load_fields()
    pat = make_matcher(fields)
    ledger = load_ledger()
    ledger_fp = []
    for x in ledger:
        fs, fs_all, dss, _ = fingerprint(x['expr'], pat, fields)
        ledger_fp.append(dict(x, fs=(fs if fs else fs_all), dss=dss))
    print('字段表 %d 个 | 台账 %d 条 | 机制指纹已算好\n' % (len(fields), len(ledger_fp)))

    codes = []
    if a.file:
        for item in json.load(io.open(a.file, encoding='utf-8')):
            codes.append((item.get('cid') or item.get('id') or '?', item.get('code') or ''))
    elif a.code:
        codes.append(('inline', a.code))
    else:
        ap.error('给一条表达式，或用 --file')

    tally = collections.Counter()
    for cid, code in codes:
        res = judge(code, fields, pat, ledger_fp, top=a.top)
        tally[res['verdict']] += 1
        if not a.quiet:
            print('=== %s' % cid)
            print('    %s' % (code or '')[:150])
            fmt(res, code)
            print()
    print('汇总: ' + '  '.join('%s=%d' % (k, v) for k, v in tally.most_common()))


if __name__ == '__main__':
    main()
