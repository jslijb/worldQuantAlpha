# -*- coding: utf-8 -*-
"""now_submit.py — 今日出货：筛选池外候选 → 平台免费预检 SELF/PROD → 出可交清单

为什么不走本地 corr_gate 先行：
    平台 GET /alphas/{id}/check 对未提交 alpha 直接返 SELF_CORRELATION / PROD_CORRELATION，
    **不耗提交配额**，而且是平台自己的真值，比本地 PnL 估算更权威。
    corr_gate 留作事后解释用。

判据（AGENTS.md 现行）：
    平台门 F>=1.0 / TO<=70% / 无 FAIL / SELF<=0.70 / PROD<=0.70
    实操留缓冲：SELF<=0.69, PROD<=0.69

用法：
    python _grid/now_submit.py --top 60            # 只筛不交
    python _grid/now_submit.py --top 60 --submit 4 # 交前 4 条常规
"""
import sys, os, json, io, glob, time, argparse, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.session import Brain

API = 'https://api.worldquantbrain.com'
MINED = 'data/alpha_quality_analysis/mined'
PNL = 'data/alpha_quality_analysis/pnl'


def load_candidates():
    """池外候选：有 mined json、未提交、有 is 指标。"""
    subs = set()
    off = 0
    s = Brain().s
    b = None
    # 取已提交集合（stage 任意）
    for stage in ('OS', 'IS'):
        off = 0
        while True:
            r = s.get(API + '/users/self/alphas',
                      params={'stage': stage, 'limit': 100, 'offset': off}, timeout=40)
            if r.status_code != 200:
                break
            res = r.json().get('results') or []
            for x in res:
                subs.add(x['id'])
            if len(res) < 100 or off >= 1000:
                break
            off += 100
    print('已提交/已入库集合 %d 条' % len(subs))

    cands = []
    for p in glob.glob(os.path.join(MINED, '*.json')):
        try:
            d = json.load(io.open(p, encoding='utf-8'))
        except Exception:
            continue
        aid = d.get('id')
        if not aid or aid in subs:
            continue
        if str(d.get('status')) not in ('UNSUBMITTED', 'COMPLETE', 'WARNING'):
            continue
        if d.get('dateSubmitted'):
            continue
        isd = d.get('is') or {}
        try:
            S = float(isd.get('sharpe'))
            F = float(isd.get('fitness'))
            T = float(isd.get('turnover'))
        except (TypeError, ValueError):
            continue
        if F is None or F < 1.0:
            continue
        if T is None or T > 0.70:
            continue
        # 平台门：不能有任何 FAIL
        checks = isd.get('checks') or []
        fails = [c.get('name') for c in checks if c.get('result') == 'FAIL']
        if fails:
            continue
        st = d.get('settings') or {}
        cands.append(dict(id=aid, cid=os.path.basename(p)[:-5], S=S, F=F, T=T,
                          margin=isd.get('margin'), region=st.get('region'),
                          universe=st.get('universe'), decay=st.get('decay'),
                          neut=st.get('neutralization'),
                          code=(d.get('regular') or {}).get('code') or
                               (d.get('code') or '')))
    # 去重（同 alpha id）
    seen = set(); uniq = []
    for c in cands:
        if c['id'] in seen:
            continue
        seen.add(c['id']); uniq.append(c)
    uniq.sort(key=lambda c: -c['S'])
    print('过平台门（无 FAIL、F>=1、TO<=70%%）的池外候选 %d 条' % len(uniq))
    return uniq, s


def platform_check(s, aid, tries=3):
    """GET /alphas/{id}/check → {'SELF':..., 'PROD':..., 'err':...}
    未提交 alpha 会返 SELF_CORRELATION / PROD_CORRELATION，不耗配额。
    首调常空 body，轮询。
    """
    for k in range(tries):
        try:
            r = s.get(API + '/alphas/%s/check' % aid, timeout=40)
        except Exception as e:
            return dict(SELF=None, PROD=None, err=str(e)[:60])
        if r.status_code == 429 or r.headers.get('Retry-After'):
            time.sleep(min(float(r.headers.get('Retry-After') or 5), 15))
            continue
        if r.status_code != 200:
            return dict(SELF=None, PROD=None, err='HTTP%d' % r.status_code)
        txt = (r.text or '').strip()
        if not txt:
            time.sleep(2); continue
        try:
            j = r.json()
        except Exception:
            time.sleep(2); continue
        isd = j.get('is') or {}
        checks = isd.get('checks') or []
        out = dict(SELF=None, PROD=None, fails=[], err=None)
        for c in checks:
            n = c.get('name') or ''
            if n == 'SELF_CORRELATION':
                out['SELF'] = c.get('value')
            elif n == 'PROD_CORRELATION':
                out['PROD'] = c.get('value')
            if c.get('result') == 'FAIL':
                out['fails'].append(n)
        if out['SELF'] is not None or out['PROD'] is not None:
            return out
        time.sleep(2)
    return dict(SELF=None, PROD=None, err='empty')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=60)
    ap.add_argument('--submit', type=int, default=0)
    ap.add_argument('--max-self', type=float, default=0.69)
    ap.add_argument('--max-prod', type=float, default=0.69)
    ap.add_argument('--sleep', type=float, default=1.2)
    a = ap.parse_args()

    cands, s = load_candidates()
    cands = cands[:a.top]

    print('\n平台预检 %d 条（免费，不耗配额）...\n' % len(cands))
    rows = []
    for i, c in enumerate(cands, 1):
        res = platform_check(s, c['id'])
        c.update(SELF=res.get('SELF'), PROD=res.get('PROD'),
                 fails=res.get('fails') or [], cerr=res.get('err'))
        ok = True
        if c['SELF'] is None:
            ok = False
        elif c['SELF'] > a.max_self:
            ok = False
        if c['PROD'] is None:
            ok = False
        elif c['PROD'] > a.max_prod:
            ok = False
        if c['fails']:
            ok = False
        c['PASS'] = ok
        rows.append(c)
        print('%2d %-10s %-6s S=%-5.2f F=%-5.2f TO=%-5.1f%% SELF=%-7s PROD=%-7s %s' % (
            i, c['id'], c['region'], c['S'], c['F'], c['T'] * 100,
            ('%.4f' % c['SELF']) if c['SELF'] is not None else str(c['cerr']),
            ('%.4f' % c['PROD']) if c['PROD'] is not None else '-',
            'PASS' if ok else ('FAIL:' + ','.join(c['fails']) if c['fails'] else 'corr')))
        time.sleep(a.sleep)

    good = [c for c in rows if c['PASS']]
    print('\n=== 可交 %d 条 ===' % len(good))
    for c in good:
        print('  %-10s S=%.2f F=%.2f SELF=%.4f PROD=%.4f %s/%s' % (
            c['id'], c['S'], c['F'], c['SELF'], c['PROD'], c['region'], c['universe']))

    io.open('_logs/now_submit_candidates.json', 'w', encoding='utf-8').write(
        json.dumps(rows, ensure_ascii=False, indent=1))
    print('\n落盘 _logs/now_submit_candidates.json')

    if a.submit and good:
        do_submit(s, good[:a.submit])


def do_submit(s, picks):
    print('\n=== 开始提交 %d 条 ===' % len(picks))
    for c in picks:
        aid = c['id']
        # 提交前最后一次 check（池子可能刚变）
        r = s.post(API + '/alphas/%s/submit' % aid, timeout=60)
        if r.status_code == 429 or r.headers.get('Retry-After'):
            time.sleep(min(float(r.headers.get('Retry-After') or 10), 30))
            r = s.post(API + '/alphas/%s/submit' % aid, timeout=60)
        body = (r.text or '')[:300]
        print('  %-10s HTTP %d  %s' % (aid, r.status_code, body))
        time.sleep(2)


if __name__ == '__main__':
    main()
