# -*- coding: utf-8 -*-
"""mine_batch171.py —— analyst4 字段发现：预期分歧度 / 覆盖变化（池子里零条）

背景（0916 晚二轮）：池子 76 条已把「fnd6 锚 + /cap|/assets + 现有价量腿几何」吃干
（x162 12/12、w166 2/2 撞墙，corr 0.686~0.877）。四个外部数据集已判死
（option8 / news12 / model16 / socialmedia12，见 f165+f166）。

analyst4 有 **1105 个 MATRIX 字段**（不需要 vec_avg），而我们池子里只用了 4 个评级字段。
本批按「预期修正」这条明确的市场行为做 0 阶单腿发现：
  ① 预期分歧度 (high - low)/|mean| —— 分析师意见越一致，未来收益越好（经典结论）
  ② 预期修正率 ts_av_diff(mean, 45) —— 用记忆里验证过的最强窗口 45
  ③ 覆盖机构数变化 ts_av_diff(number, 45) —— 关注度漂移
  ④ 预期水平 /close —— 类估值轴
包装统一用我们验证过最强的那一种：group_rank(ts_backfill(<core>,120), subindustry)。

达标线：SF >= 3.0 记为「可入腿库候选」，<=1.0 或带 FAIL 记该轴关闭。
产出 data/alpha_quality_analysis/mined/f171_{cid}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2

NP_H = 'anl4_fs_detail_estimate_1qf_v4_nd_netprofit_high'
NP_L = 'anl4_fs_detail_estimate_1qf_v4_nd_netprofit_low'
NP_M = 'anl4_fs_detail_estimate_1qf_v4_nd_netprofit_mean'
NP_N = 'anl4_fs_detail_estimate_1qf_v4_nd_netprofit_number'
PT_H = 'anl4_fs_detail_estimate_1qf_v4_nd_ptp_high'
PT_L = 'anl4_fs_detail_estimate_1qf_v4_nd_ptp_low'
PT_M = 'anl4_fs_detail_estimate_1qf_v4_nd_ptp_mean'
PT_N = 'anl4_fs_detail_estimate_1qf_v4_nd_ptp_number'
EB_H = 'anl4_fs_detail_estimate_1qf_v4_nd_ebit_high'
EB_L = 'anl4_fs_detail_estimate_1qf_v4_nd_ebit_low'
EB_M = 'anl4_fs_detail_estimate_1qf_v4_nd_ebit_mean'
EB_N = 'anl4_fs_detail_estimate_1qf_v4_nd_ebit_number'
EP_M = 'anl4_fs_detail_estimate_1qf_v4_nd_epsr_mean'
EP_N = 'anl4_fs_detail_estimate_1qf_v4_nd_epsr_number'
GC_MAX = 'anl4_fs_guidances_advanced_qf_nd_capex_maxguidance'
GC_MIN = 'anl4_fs_guidances_advanced_qf_nd_capex_minguidance'

CORES = [
    ('disp_np', f'-({NP_H} - {NP_L})/abs({NP_M})'),
    ('disp_ptp', f'-({PT_H} - {PT_L})/abs({PT_M})'),
    ('disp_ebit', f'-({EB_H} - {EB_L})/abs({EB_M})'),
    ('rev_np', f'ts_av_diff({NP_M}, 45)'),
    ('rev_ptp', f'ts_av_diff({PT_M}, 45)'),
    ('rev_ebit', f'ts_av_diff({EB_M}, 45)'),
    ('cov_np', f'ts_av_diff({NP_N}, 45)'),
    ('cov_ep', f'ts_av_diff({EP_N}, 45)'),
    ('cov_ptp', f'ts_av_diff({PT_N}, 45)'),
    ('est_np', f'{NP_M}/close'),
    ('est_ebit', f'{EB_M}/close'),
    ('numrank_np', f'ts_rank({NP_N}, 252)'),
    ('guid_spread', f'-({GC_MAX} - {GC_MIN})/abs(close)'),
]
TODO = [(f'f171_{n}', f'group_rank(ts_backfill({core}, 120), subindustry)', n) for n, core in CORES]
print(f'analyst4 单腿 {len(TODO)} 条待测', flush=True)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def BASE():
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
            'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON',
            'unitHandling': 'VERIFY', 'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


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
    cid, expr, tag = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(), 'regular': expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try:
            p = sess.get(loc)
        except Exception as e:
            print(cid, 'NET-poll', e, flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(float(ra)); continue
        break
    try:
        jj = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_core'] = expr
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '***强' if S + F >= 3.0 else (' 中' if S + F >= 2.2 else '  弱')
    print(f"{flag} {tag:14s} {aid} S={S:6.2f} F={F:6.2f} SF={S+F:6.2f} T={b.get('turnover')} tS={te.get('sharpe')} FAIL={fa}", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, TODO))
print('batch171 done', flush=True)
