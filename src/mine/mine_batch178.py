# -*- coding: utf-8 -*-
"""mine_batch178.py —— 结构层最后一杠杆：逐腿 group_rank → group_zscore / group_neutralize

背景（0917）：
  - 本地库存与数据集全部闭合（x175 0/34、x176 decay 证伪、x177 analyst4 二次开采 0 种子）。
  - 池子 79 条的腿全部是 group_rank(..., subindustry) 形状；专家 SOP「结构层：换算子」里
    「ts_rank↔ts_zscore」已测过，但**逐腿 group_rank→group_zscore**（保幅度的组内标准化）
    从未测过——它改变每条腿的截面分布形状，PnL 因此不同。
  - 注意：已判死的是「顶层 zscore/rank 包裹」（丢中性化好处），本批是逐腿替换，不是同一个东西。

变换（对 8 条擦线候选，corr 0.689~0.702）：
  _ZS  = 每条腿 group_rank(e, subindustry) → group_zscore(e, subindustry)
  _GN  = 每条腿 group_rank(e, subindustry) → group_neutralize(rank(e), subindustry)

产出 data/alpha_quality_analysis/mined/x178_{cid}_{tag}.json
"""
import os as _os, pathlib as _pl, sys, json, time, re
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3

PICKS = [  # (cid, base_corr) —— x175 判决 corr 0.689~0.702
    ('x175_m161_e79PvPpE_BIT', 0.6890),
    ('x175_x172_w166_02_OVN_BIT', 0.6895),
    ('x175_w114_m_I', 0.6903),
    ('x175_x172_w166_02_OVN_B', 0.6933),
    ('x175_w166_02_BIT', 0.6978),
    ('x175_m161_0mR2K6lr_BIT', 0.6982),
    ('x175_w166_02_B', 0.7007),
    ('x175_m161_e79PvPpE_B', 0.7017),
]


def balanced_paren(s, i):
    """s[i] == '(' → 返回与之配对的 ')' 下标"""
    depth = 0
    for j in range(i, len(s)):
        if s[j] == '(':
            depth += 1
        elif s[j] == ')':
            depth -= 1
            if depth == 0:
                return j
    raise ValueError('unbalanced paren at %d' % i)


def split_top_commas(inner):
    """按顶层逗号切分（括号深度为 0 的逗号）"""
    parts, depth, last = [], 0, 0
    for j, ch in enumerate(inner):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        elif ch == ',' and depth == 0:
            parts.append(inner[last:j]); last = j + 1
    parts.append(inner[last:])
    return parts


def convert(expr, mode):
    out, i = [], 0
    while True:
        k = expr.find('group_rank(', i)
        if k < 0:
            out.append(expr[i:]); break
        out.append(expr[i:k])
        close = balanced_paren(expr, k + len('group_rank'))
        inner = expr[k + len('group_rank('):close]
        parts = split_top_commas(inner)
        sig, grp = ','.join(parts[:-1]), parts[-1]
        if mode == 'ZS':
            out.append(f'group_zscore({sig}, {grp})')
        else:
            out.append(f'group_neutralize(rank({sig}), {grp})')
        i = close + 1
    return ''.join(out)


todo = []
for cid, bc in PICKS:
    src = f'{OUT}/{cid}.json'
    if not _os.path.exists(src):
        print(f'{cid} 源 json 缺失，跳过', flush=True); continue
    d = json.load(open(src, encoding='utf-8'))
    expr = (d.get('regular') or {}).get('code')
    neut = (d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'
    if not expr or 'group_rank(' not in expr:
        print(f'{cid} 无 group_rank 腿，跳过', flush=True); continue
    for mode in ('ZS', 'GN'):
        todo.append((f'x178_{cid}_{mode}'[:64], convert(expr, mode), neut, cid, bc))

print(f'结构变换变体 {len(todo)} 条', flush=True)
for t in todo:
    print(f'   {t[0]:48s} {t[2]:11s} base={t[4]:.4f}', flush=True)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def BASE(neut):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
            'neutralization': neut, 'truncation': 0.08, 'pasteurization': 'ON',
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
    cid, expr, neut, src_cid, bc = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(neut), 'regular': expr}, cid)
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
    d['_cid'] = cid; d['_neut'] = neut; d['_src'] = src_cid; d['_base_corr'] = bc
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' fail '
    print(f'{flag} {cid:48s} {neut:11s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} base={bc:.4f} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch178 done', flush=True)
