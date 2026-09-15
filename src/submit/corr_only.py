# -*- coding: utf-8 -*-
"""只读 corr 预检：查指定 alpha(或 mined 里的 batch 前缀) 与在产池的相关性。
   绝不提交、绝不写台账 —— 用于实验判读。

   ★ 0915 关键修正：平台 API 限流 = 60 请求/分钟（响应头 RateLimit-Limit: 60）。
     一条候选轮询 3~4 次，47 条候选 ≈ 190 请求 → 必然触发 429，
     而 429 在旧脚本里被当成 "TIMEOUT"，造成"服务故障"的重大误判。
     本版：① 请求最小间隔 MIN_INTERVAL 秒（60/分钟 的 1.3 倍裕度）
           ② 429 按 RateLimit-Reset / Retry-After 退避重试
           ③ 打印限流余量，便于诊断

用法：
    python src/submit/corr_only.py w122_             # 该前缀下全部 mined 候选
    python src/submit/corr_only.py akLp3pzW 883wqwVX # 直接给 alpha id
"""
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests, json, time, glob, sys, csv

OUT = 'data/alpha_quality_analysis/mined'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

MIN_INTERVAL = 1.3          # 秒/请求（平台上限 60/分钟）
_last_req = [0.0]
_rl_state = {'limit': None, 'remaining': None}

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def _throttled_get(url, max_wait=200.0):
    """带限流感知的 GET：固定间隔 + 429 退避"""
    t_start = time.time()
    while time.time() - t_start < max_wait:
        gap = time.time() - _last_req[0]
        if gap < MIN_INTERVAL:
            time.sleep(MIN_INTERVAL - gap)
        try:
            r = sess.get(url)
        except Exception:
            time.sleep(3); continue
        _last_req[0] = time.time()
        _rl_state['limit'] = r.headers.get('RateLimit-Limit')
        _rl_state['remaining'] = r.headers.get('RateLimit-Remaining')
        if r.status_code == 429:
            rst = r.headers.get('RateLimit-Reset') or r.headers.get('Retry-After')
            try:
                w = float(rst)
            except Exception:
                w = 20.0
            w = max(5.0, min(w + 1.5, 90.0))
            print(f'    [限流] HTTP 429，等待 {w:.0f}s 后重试'
                  f'（余量 {_rl_state["remaining"]}/{_rl_state["limit"]}）', flush=True)
            time.sleep(w)
            continue
        return r
    return None


def corr_precheck(aid, budget_sec=180.0):
    """返回 (max_corr, strict_line, detail)。
       200 + Retry-After + 空 body = 平台正在现算，继续轮询（正常 3~4 次即出）。"""
    t0 = time.time()
    n = 0
    while time.time() - t0 < budget_sec:
        n += 1
        r = _throttled_get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
        if r is None:
            continue
        if r.status_code != 200:
            time.sleep(3); continue
        if not r.text:
            ra = r.headers.get('Retry-After')
            time.sleep(max(MIN_INTERVAL, min(float(ra), 6.0)) if ra else 1.5)
            continue
        try:
            recs = (r.json() or {}).get('records') or []
        except Exception:
            time.sleep(2); continue
        if not recs:
            time.sleep(2); continue
        max_corr, max_id, hot_S, hot_id = 0.0, '', 0.0, ''
        for rec in recs:
            c = rec[5] if len(rec) > 5 else 0
            s_ = rec[6] if len(rec) > 6 else 0
            if c > max_corr:
                max_corr, max_id = c, rec[0]
            if c >= 0.7 and s_ > hot_S:
                hot_S, hot_id = s_, rec[0]
        return (max_corr, 1.10 * hot_S,
                f'max={max_id}@{max_corr:.4f} | 热对手最高S={hot_id}@{hot_S} '
                f'(轮询{n}次/{time.time()-t0:.1f}s)')
    return None, None, f'TIMEOUT({budget_sec:.0f}s, 轮询{n}次)'


def main():
    args = sys.argv[1:]
    if not args:
        print('用法: corr_only.py <前缀|alpha_id> ...'); return 1

    done = set()
    with open(LEDGER, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row.get('id'):
                done.add(row['id'].strip())

    items = []
    for a in args:
        if len(a) == 8 and a.isalnum():
            items.append((a, a, None, None, None, '  '))
            continue
        files = sorted(glob.glob(f'{OUT}/{a}*.json'))
        if not files:
            print(f'[warn] 前缀 {a} 未匹配到 mined 文件'); continue
        for f in files:
            try:
                d = json.load(open(f, encoding='utf-8'))
            except Exception:
                continue
            aid = d.get('id')
            if not aid:
                continue
            b = d.get('is') or {}; te = d.get('test') or {}
            S = b.get('sharpe') or 0; F = b.get('fitness') or 0
            fails = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
            tS = te.get('sharpe')
            q = 'OK ' if ((S + F) >= 4.0 and (tS or 0) >= 1.25 and not fails) else 'X  '
            items.append((d.get('_cid') or _os.path.basename(f)[:-5], aid,
                          S, round(S + F, 2), tS, q))

    print(f'待预检 {len(items)} 条（限速 {MIN_INTERVAL}s/请求，平台上限 60/分钟）', flush=True)
    print(f"{'cid':10} {'id':10} {'S+F':>6} {'tS':>6} {'质量':>4} {'corr':>8} {'豁免线':>8}  判定")
    res = []
    for cid, aid, S, SF, tS, q in items:
        mc, line, detail = corr_precheck(aid)
        if mc is None:
            print(f'{cid:10} {aid:10} {str(SF):>6} {str(tS):>6} {q:>4}      -        -  TIMEOUT', flush=True)
            res.append({'cid': cid, 'id': aid, 'corr': None, 'detail': detail})
            continue
        if mc < 0.7:
            verdict = '★ 可提交(直通)'
        elif S is not None and S >= line:
            verdict = '豁免可提交'
        else:
            verdict = '封死'
        print(f'{cid:10} {aid:10} {SF:6.2f} {str(tS):>6} {q:>4} {mc:8.4f} {line:8.3f}  {verdict}', flush=True)
        res.append({'cid': cid, 'id': aid, 'S': S, 'SF': SF, 'tS': tS,
                    'corr': mc, 'line': line, 'verdict': verdict, 'detail': detail})

    json.dump(res, open('_autologs/corr_only_out.json', 'w'), ensure_ascii=False, indent=1)
    n_ok = sum(1 for r in res if str(r.get('verdict', '')).startswith('★'))
    n_ex = sum(1 for r in res if r.get('verdict') == '豁免可提交')
    print(f'\n=== 汇总：可直通 {n_ok} / 可豁免 {n_ex} / 封死 {len(res)-n_ok-n_ex} ===')
    return 0


if __name__ == '__main__':
    sys.exit(main())
