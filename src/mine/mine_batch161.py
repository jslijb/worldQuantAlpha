# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch161 = 【中性化轴扩产】把台账里 SF≥4.5 的表达式全部换 MARKET 中性化重跑
#
# 依据（batch160 实测，一手数据）：
#   - 已提交 73 条的中性化分布 = SUBINDUSTRY 48 / INDUSTRY 26 / MARKET 0 / SECTOR 0 / NONE 0。
#     → MARKET 是池子里完全不存在的 PnL 几何。
#   - d5b5voEJ（SUBINDUSTRY，corr 0.7467 卡死）换 MARKET 后 → SF 4.71 / tS 1.50 / corr 0.6067
#     提交后平台实测 selfCorr **0.6015**，ACCEPTED。**降 0.14，一条从"过不去"变"直通"。**
#   - NONE 全线崩（SF 2.15~2.20 + LOW_SHARPE）→ 已排除，本批不跑。
#   - SECTOR 降 corr 力度弱（e7bkoYRJ 0.7552 / omL8Mazn 0.6996 仍卡）→ 本批不跑。
#
# 假设：表达式本身质量已达标（SF≥4.5），它贴池子是因为"外层 SUBINDUSTRY 去均值"这个维度与池子相同。
#   换 MARKET 后，同一信号在"全市场"维度上重新投影 → 与池子里所有 SUBINDUSTRY 版天然错开。
#   对照：这也解释了为什么"换字段/换锚"无效——那些都没动投影维度。
#
# 判据：SF≥4.0 + tS≥1.25 + 无 FAIL + 本地 corr ≤0.685 → 提交。不达标照实记，不粉饰。
import requests, json, time, os, csv
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'


def BASE(decay, neut):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1,
            'decay': decay, 'neutralization': neut, 'truncation': 0.08,
            'pasteurization': 'ON', 'unitHandling': 'VERIFY', 'nanHandling': 'ON',
            'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


# 从台账取 SF≥4.5 的表达式（保留原 decay，只把中性化换成 MARKET）
best = {}
for r in list(csv.reader(open(LED, encoding='utf-8-sig')))[1:]:
    try:
        sf = float(r[2]) + float(r[3])
    except Exception:
        continue
    if r[0] not in best or sf > best[r[0]][0]:
        best[r[0]] = (sf, r[1], int(float(r[9])) if r[9] else 10)

POOL = sorted([(v[0], k, v[1], v[2]) for k, v in best.items() if v[0] >= 4.5], reverse=True)

C = []
for sf, aid, expr, decay in POOL:
    cid = f'm161_{aid}'
    if os.path.exists(f'{OUT}/{cid}.json'):
        continue
    C.append((cid, aid, expr, BASE(decay, 'MARKET')))

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def post_retry(payload, cid):
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None


def run_one(item):
    cid, src, expr, st = item
    of = f'{OUT}/{cid}.json'
    r = post_retry({'type': 'REGULAR', 'settings': st, 'regular': expr}, cid)
    if not r:
        return
    loc = r.headers.get('Location')
    jj = None
    for _ in range(90):
        try:
            p = sess.get(loc)
        except Exception:
            time.sleep(10); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 10)); continue
        try: jj = p.json()
        except Exception: time.sleep(5); continue
        break
    if not jj:
        print(f'{cid} TIMEOUT', flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    d['_neut'] = 'MARKET'
    d['_src'] = src
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' '
    print(f"{flag} {cid} {aid} src={src} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get('turnover')} "
          f"tS={te.get('sharpe')} FAIL={fa}", flush=True)


if __name__ == '__main__':
    print(f'台账 SF≥4.5 表达式 {len(POOL)} 条，待跑 {len(C)} 条（MARKET 中性化）', flush=True)
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch161 done', flush=True)
