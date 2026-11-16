# -*- coding: utf-8 -*-
"""scan_checks.py — 批量拉平台 /alphas/{id}/check，统计真实 FAIL 分布

为什么必须这一步：
    本地 mined json 里的 is.checks 是**模拟当时**的快照，不含后来新增的门
    （IS_LADDER_SHARPE / OLD_SIMULATION / SELF_CORRELATION / PROD_CORRELATION）。
    实测 LL9YRO2e（S=3.55）：本地看着能交，平台 check 直接 IS_LADDER_SHARPE FAIL + OLD_SIMULATION FAIL。

口径：
    只有 result == 'FAIL' 才算死。PENDING / WARNING / ERROR 都不算。
"""
import sys, os, json, io, glob, time, argparse, collections, datetime as dt
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.session import Brain

API = 'https://api.worldquantbrain.com'
MINED = 'data/alpha_quality_analysis/mined'


def load_cands(top):
    subs = set()
    s = Brain().s
    for stage in ('OS', 'IS'):
        off = 0
        while True:
            r = s.get(API + '/users/self/alphas',
                      params={'stage': stage, 'limit': 100, 'offset': off}, timeout=40)
            if r.status_code != 200:
                break
            for x in (r.json().get('results') or []):
                subs.add(x['id'])
            if off >= 1000:
                break
            off += 100
    cands = []
    for p in glob.glob(os.path.join(MINED, '*.json')):
        try:
            d = json.load(io.open(p, encoding='utf-8'))
        except Exception:
            continue
        aid = d.get('id')
        if not aid or aid in subs or d.get('dateSubmitted'):
            continue
        if str(d.get('status')) != 'UNSUBMITTED':
            continue
        isd = d.get('is') or {}
        try:
            S = float(isd.get('sharpe')); F = float(isd.get('fitness')); T = float(isd.get('turnover'))
        except (TypeError, ValueError):
            continue
        if F < 1.5 or T > 0.70 or S < 2.0:
            continue
        # 2026-11-15 加：模拟超约 1 个月必被 OLD_SIMULATION 拒（实测 80/80 全踩）
        if (d.get('dateCreated') or '')[:10] < '2026-10-16':
            continue
        st = d.get('settings') or {}
        cands.append(dict(id=aid, S=S, F=F, T=T, margin=isd.get('margin'),
                          region=st.get('region'), universe=st.get('universe'),
                          created=(d.get('dateCreated') or '')[:10],
                          cid=os.path.basename(p)[:-5]))
    seen = set(); u = []
    for c in cands:
        if c['id'] in seen:
            continue
        seen.add(c['id']); u.append(c)
    u.sort(key=lambda c: -c['S'])
    return u[:top], s


def get_checks(s, aid, tries=2):
    for _ in range(tries):
        try:
            r = s.get(API + '/alphas/%s/check' % aid, timeout=40)
        except Exception as e:
            return None, str(e)[:60]
        if r.status_code == 429 or r.headers.get('Retry-After'):
            time.sleep(min(float(r.headers.get('Retry-After') or 5), 15))
            continue
        if r.status_code != 200:
            return None, 'HTTP%d' % r.status_code
        txt = (r.text or '').strip()
        if not txt:
            time.sleep(2); continue
        try:
            j = r.json()
        except Exception:
            time.sleep(2); continue
        checks = (j.get('is') or {}).get('checks') or []
        return checks, None
    return None, 'empty'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--top', type=int, default=200)
    ap.add_argument('--sleep', type=float, default=0.8)
    a = ap.parse_args()

    cands, s = load_cands(a.top)
    print('待检候选 %d 条（S>=2.0 / F>=1.5 / TO<=70%% / 未提交）\n' % len(cands))

    failcnt = collections.Counter()
    keep = []
    for i, c in enumerate(cands, 1):
        checks, err = get_checks(s, c['id'])
        if checks is None:
            print('%3d %-10s %-4s S=%.2f  ERR %s' % (i, c['id'], c['region'], c['S'], err))
            time.sleep(a.sleep); continue
        fails = [(x.get('name'), x.get('value'), x.get('limit')) for x in checks
                 if x.get('result') == 'FAIL']
        pend = [x.get('name') for x in checks if x.get('result') == 'PENDING']
        for f in fails:
            failcnt[f[0]] += 1
        c['fails'] = fails
        c['pending'] = pend
        c['nchecks'] = len(checks)
        ok = (len(fails) == 0)
        if ok:
            keep.append(c)
        print('%3d %-10s %-4s S=%-5.2f F=%-5.2f TO=%-5.1f%% %s %s' % (
            i, c['id'], c['region'], c['S'], c['F'], c['T'] * 100,
            'OK  ' if ok else 'FAIL',
            '' if ok else '|'.join('%s(%s/%s)' % (n, v, l) for n, v, l in fails)))
        time.sleep(a.sleep)

    print('\n=== FAIL 类型分布 ===')
    for k, n in failcnt.most_common():
        print('  %-28s %d' % (k, n))
    print('\n=== 无 FAIL 的候选 %d 条 ===' % len(keep))
    for c in keep:
        print('  %-10s %-4s S=%.2f F=%.2f TO=%.1f%% created=%s pending=%s' % (
            c['id'], c['region'], c['S'], c['F'], c['T'] * 100, c['created'],
            ','.join(c['pending'])[:50]))
    io.open('_logs/scan_checks.json', 'w', encoding='utf-8').write(
        json.dumps(dict(all=cands, keep=keep, failcnt=dict(failcnt)), ensure_ascii=False, indent=1))
    print('\n落盘 _logs/scan_checks.json')


if __name__ == '__main__':
    main()
