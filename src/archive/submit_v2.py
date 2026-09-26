# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 通用串行提交器 v2：扫描 mined 目录未提交候选 -> 质量过滤 -> 动态 corr 预检 -> 直通/豁免 -> 提交 -> 台账追加
# 关键修正：豁免线 = 1.10 x max(对手S | corr>=0.7)（旧版误用 max-corr 那一个对手的 S，偏宽松）
import requests, json, time, os, csv, glob, sys

OUT = 'data/alpha_quality_analysis/mined'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
BATCH = sys.argv[1] if len(sys.argv) > 1 else 'batch114'
scans = sys.argv[2:] if len(sys.argv) > 2 else ['w114_']

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def ledger_ids():
    ids = set()
    with open(LEDGER, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            if row.get('id'): ids.add(row['id'].strip())
    return ids

def append_ledger(aid, expr, S, F, T, R, DD, ds, decay, neut, tag):
    with open(LEDGER, 'a', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow([aid, expr, S, F, T, R, DD, '', ds, decay, neut, tag])

def corr_precheck(aid, budget_sec=150.0):
    """返回 (max_corr, strict_line, detail)；耐心窗口拉长以扛住平台队列积压
    0915 修正：加 wall-clock 时间预算。原实现最坏 200 次 × sleep(10s) = 33 分钟空转
    （实测已出现 `corr TIMEOUT，跳过`）；而正常情况仅需 3~4 次轮询（4~6 秒）即返回 records，
    150 秒预算足够，超出即判 TIMEOUT 跳过。"""
    _t0 = time.time()
    for _ in range(200):
        if time.time() - _t0 > budget_sec:
            break
        try:
            r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
        except Exception:
            time.sleep(10); continue
        if r.status_code == 200 and r.headers.get('Retry-After'):
            time.sleep(min(float(r.headers['Retry-After']), 20)); continue
        if r.status_code != 200:
            time.sleep(15); continue
        try: j = r.json()
        except Exception: time.sleep(10); continue
        recs = j.get('records') or []
        if not recs:
            time.sleep(10); continue
        max_corr, max_id = 0.0, ''
        hot_S, hot_id = 0.0, ''
        for rec in recs:
            c = rec[5] if len(rec) > 5 else 0
            s_ = rec[6] if len(rec) > 6 else 0
            if c > max_corr: max_corr, max_id = c, rec[0]
            if c >= 0.7 and s_ > hot_S: hot_S, hot_id = s_, rec[0]
        return max_corr, 1.10 * hot_S, f'max={max_id}@{max_corr:.3f} | 热对手最高S={hot_id}@{hot_S}'
    return None, None, 'TIMEOUT'

def quality_ok(d):
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    tS = te.get('sharpe') or 0
    if S + F < 4.0 or tS < 1.25: return False, f'SF={S+F:.2f} tS={tS}'
    for c in b.get('checks', []):
        if c.get('result') == 'FAIL': return False, f"check:{c.get('name')}"
    return True, 'ok'

def alpha_active(aid):
    try:
        d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    except Exception:
        return None
    if d.get('status') == 'ACTIVE' or d.get('stage') == 'OS':
        return d
    return None

def submit(aid):
    r = sess.post(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
    if r.status_code not in (200, 201):
        return None, f'POST {r.status_code} {r.text[:150]}'
    loc = r.headers.get('Location') or f'https://api.worldquantbrain.com/alphas/{aid}/submit'
    for i in range(120):
        # 每 4 轮直接核 alpha 真实状态（提交接口常返回 status=None 假死锁）
        if i % 4 == 3:
            d = alpha_active(aid)
            if d: return d, 'ACTIVE(via-alpha)'
        p = sess.get(loc)
        ra = p.headers.get('Retry-After')
        if ra: time.sleep(min(float(ra), 30)); continue
        try: j = p.json()
        except Exception: time.sleep(8); continue
        st = j.get('status') or ''
        if st == 'ACTIVE' or j.get('stage') == 'OS':
            d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
            return d, 'ACTIVE(submit-api)'
        if st in ('FAIL', 'DEPRECATED'):
            return None, f'{st} {json.dumps(j)[:200]}'
        time.sleep(8)
    d = alpha_active(aid)
    if d: return d, 'ACTIVE(after-timeout)'
    return None, 'PENDING/TIMEOUT'

def main():
    done = ledger_ids()
    cands = []
    files = []
    for pre in scans:
        files += sorted(glob.glob(f'{OUT}/{pre}*.json'))
    for f in files:
        try: d = json.load(open(f))
        except Exception: continue
        aid = d.get('id')
        if not aid or aid in done: continue
        ok, why = quality_ok(d)
        b = d.get('is') or {}; te = d.get('test') or {}
        print(f"{d.get('_cid')} {aid} S={b.get('sharpe')} F={b.get('fitness')} tS={te.get('sharpe')} {'OK' if ok else 'X '+why}", flush=True)
        if ok: cands.append(d)
    print(f'=== 达标待提: {len(cands)} ===', flush=True)
    okc = 0
    for d in cands:
        aid = d.get('id'); b = d.get('is') or {}
        S = b.get('sharpe') or 0
        mc, line, detail = corr_precheck(aid)
        if mc is None:
            print(f'{aid} corr TIMEOUT，跳过', flush=True); continue
        print(f'{d.get("_cid")} {aid} S={S:.2f} corr={mc:.4f} 豁免线={line:.3f} [{detail}]', flush=True)
        if mc >= 0.7 and S < line:
            print(f'  -> 封死（corr>={0.7} 且 S {S:.2f} < {line:.3f}）', flush=True); continue
        reason = '直通(corr<0.7)' if mc < 0.7 else '豁免(S达线)'
        dd, msg = submit(aid)
        if dd:
            ds = dd.get('dateSubmitted')
            print(f'*** 提交成功 {aid} [{reason}] dateSubmitted={ds}', flush=True)
            append_ledger(aid, d.get('regular', {}).get('code', ''), S, b.get('fitness'),
                          b.get('turnover'), b.get('returns'), b.get('drawdown'),
                          ds, d.get('settings', {}).get('decay'), d.get('settings', {}).get('neutralization'),
                          f'0914-{BATCH}-{d.get("_cid")}')
            okc += 1
        else:
            print(f'  -> 提交未落地: {msg}', flush=True)
    print(f'=== {BATCH} 提交完成，本轮成功 {okc} ===', flush=True)

if __name__ == '__main__':
    main()
