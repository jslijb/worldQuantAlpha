# -*- coding: utf-8 -*-
"""combo_gen.py —— 挖矿组合生成器的共享脚手架（从 15 个 mine_wNNN 脚本提取，消除复制粘贴）

提供：根目录定位 / 路径常量 / cid2id / 认证会话 / 带缓存的 PnL 拉取 /
     池子与腿库装载 / 日期对齐与协方差矩阵 / 组合落盘。

各批次脚本只保留自己独有的 EXPR 字典 + 枚举/权重/过滤逻辑，脚手架全部调这里。
提取依据：mine_w200_intraday.py 与 mine_w203_expand.py 的脚手架逐字一致。
"""
import os as _os, pathlib as _pl, csv, json, time, itertools
import numpy as np
import requests

MINED = 'data/alpha_quality_analysis/mined'
PCACHE = 'data/alpha_quality_analysis/pnl'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'


def project_root():
    """向上找含凭据的目录并切过去（脚本层级变了也不用改）。"""
    _p = _pl.Path(__file__).resolve()
    for _d in [_p.parent, *_p.parents]:
        if (_d / 'brain_credentials.txt').exists():
            _os.chdir(_d)
            return _d
    return _pl.Path.cwd()


def cid2id(cid):
    """8 位 alpha id 原样返回；别名 / 组合 cid 去 mined 目录反查真实 id。"""
    if len(cid) == 8 and cid.isalnum():
        return cid
    p = _pl.Path(MINED) / f'{cid}.json'
    if p.exists():
        d = json.load(open(p, encoding='utf-8'))
        if d.get('id'):
            return d['id']
    for h in _pl.Path(MINED).glob('*.json'):
        try:
            d = json.load(open(h, encoding='utf-8'))
        except Exception:
            continue
        if d.get('_cid') == cid and d.get('id'):
            return d['id']
    return None


_SESS = None
def session():
    """缓存的认证会话；首次调用用凭据登录。"""
    global _SESS
    if _SESS is None:
        s = requests.Session()
        s.auth = tuple(json.load(open('brain_credentials.txt')))
        assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201
        _SESS = s
    return _SESS


def get_pnl(aid):
    """带本地缓存的 PnL 拉取；缓存命中不联网（离线可复现）。"""
    cp = _pl.Path(PCACHE) / f'{aid}.json'
    if cp.exists():
        try:
            return json.load(open(cp, encoding='utf-8'))
        except Exception:
            pass
    s = session()
    for _ in range(6):
        try:
            r = s.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        except Exception:
            time.sleep(5); continue
        if r.status_code != 200 or r.headers.get('Retry-After'):
            time.sleep(float(r.headers.get('Retry-After') or 4)); continue
        try:
            j = r.json()
        except Exception:
            time.sleep(3); continue
        recs = sorted((str(x[0]), float(x[1])) for x in (j.get('records') or [])
                      if len(x) >= 2 and x[1] is not None)
        if len(recs) < 60:
            time.sleep(3); continue
        ser = {recs[k][0]: recs[k][1] - recs[k - 1][1] for k in range(1, len(recs))}
        json.dump(ser, open(cp, 'w', encoding='utf-8'))
        return ser
    return None


def load_pool():
    """从台账装载已提交 alpha 的 PnL（池子）；拉取失败的报警。"""
    pool, missing = {}, []
    for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
        if row and len(row[0]) == 8 and row[0].isalnum() and row[0] not in pool:
            v = get_pnl(row[0])
            if v:
                pool[row[0]] = v
            else:
                missing.append(row[0])
    if missing:
        print(f'WARN 以上成员不在池内，pred 会漏掉与它们的碰撞: {missing}')
    return pool, missing


def load_legs(legs):
    """装载腿库 PnL；返回 {leg: pnl}（只含拉取成功的）。"""
    load = {}
    for l in legs:
        aid = cid2id(l)
        if not aid:
            print(f'WARN 腿 {l} 无 id'); continue
        p = get_pnl(aid)
        if not p:
            print(f'WARN 腿 {l} 无 PnL'); continue
        load[l] = p
    return load


def align_dates(pool, load):
    """池 ∩ 腿 的日期对齐，返回矩阵与索引（各批次生成器共用）。"""
    dates = None
    for ps in list(pool.values()) + list(load.values()):
        ds = set(ps)
        dates = ds if dates is None else (dates & ds)
    dates = sorted(dates)
    T = len(dates)
    assert T >= 400, f'对齐日期仅 {T} 天，不足 400'
    legs = list(load.keys())
    Lraw = np.vstack([[load[l][d] for d in dates] for l in legs])
    pids = list(pool)
    Pm = np.vstack([[pool[q][d] for d in dates] for q in pids])
    Pm = Pm - Pm.mean(axis=1, keepdims=True)
    Psd = Pm.std(axis=1, ddof=1, keepdims=True); Psd[Psd == 0] = 1
    Pz = Pm / Psd
    Mmat = Pz @ Lraw.T / T
    Gm = Lraw @ Lraw.T / T
    idx = {l: i for i, l in enumerate(legs)}
    return {'dates': dates, 'T': T, 'legs': legs, 'Lraw': Lraw, 'Mmat': Mmat,
            'Gm': Gm, 'idx': idx, 'pids': pids}


def dump_combos(comb, outp):
    json.dump(comb, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'已落盘 {outp}（{len(comb)} 条）')
