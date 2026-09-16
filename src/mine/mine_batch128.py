# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch128 = 覆盖验证轮（batch127 定案：aC<30 完全无数据，tfvceq aC=87 有数据）
# 目标：对 aC 30~400 未用字段逐个单锚回测 group_rank(fld/assets, subindustry)，
#       产出"已验证有数据"的白名单 -> data/alpha_quality_analysis/COLD_FIELD_WHITELIST.csv
# 判据（batch127 同款）：longCount>0 且 shortCount>0 且 S!=0
import requests, json, time, os, csv
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WL  = 'data/alpha_quality_analysis/COLD_FIELD_WHITELIST.csv'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

# (字段, aC)  aC 30~400 全部未用；剔除 cptrank_gvkeymap(技术码，无经济含义)
FIELDS = [
 ('fnd6_newqv1300_spceepspq',122), ('fnd6_optdrq',182), ('fnd6_newa1v1300_cshi',249),
 ('fnd6_newa1v1300_aol2',251), ('fnd6_newa2v1300_spceeps',271), ('fnd6_newqv1300_spcedpq',279),
 ('fnd6_newa1v1300_ibcom',281), ('fnd6_optlifeq',282), ('fnd6_txtubtxtr',302),
 ('fnd6_newqv1300_invrmq',303), ('fnd6_newqv1300_aocipenq',307), ('fnd6_newqv1300_rdipdq',317),
 ('fnd6_newa1v1300_fca',321), ('fnd6_newqv1300_dpactq',322), ('fnd6_newqv1300_aqpl1q',328),
 ('fnd6_newa1v1300_aocidergl',334), ('fnd6_newqv1300_cshoq',338), ('fnd6_newa1v1300_dvt',346),
 ('fnd6_mfmq_mibtq',347), ('fnd6_newqv1300_ibcomq',352), ('fnd6_lqpl1',361),
 ('fnd6_newa1v1300_ibadj',361), ('fnd6_newqv1300_txdbaq',364), ('fnd6_pstkl',365),
 ('fnd6_lol2',368), ('fnd6_txs',370), ('fnd6_newqv1300_aociderglq',371),
 ('fnd6_txtubposinc',378), ('fnd6_txtubadjust',379), ('fnd6_pidom',382),
 ('fnd6_newqv1300_rectoq',384), ('fnd6_stkcpa',384), ('fnd6_newqv1300_aol2q',387),
 ('fnd6_newqv1300_chq',388), ('fnd6_newqv1300_invwipq',388), ('fnd6_newa1v1300_dpact',389),
 ('fnd6_newqv1300_citotalq',389), ('fnd6_newa2v1300_nopi',392), ('fnd6_invo',393),
 ('fnd6_txdba',393), ('fnd6_newa1v1300_ano',395), ('fnd6_newqv1300_ibadjq',397),
 ('fnd6_np',400),
]

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def post_retry(payload, cid):
    for att in range(8):
        try: r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201): return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None

def run_one(item):
    fld, aC = item
    cid = 'w128_' + fld.split('_', 2)[-1] if fld.count('_') >= 2 else 'w128_' + fld
    of = f'{OUT}/{cid}.json'
    if os.path.exists(of):
        print(f'{cid}已有产出，跳过', flush=True)
    else:
        expr = f'group_rank({fld}/assets, subindustry)'
        r = post_retry({'type':'REGULAR','settings':BASE(),'regular':expr}, cid)
        if r is None: return (fld, aC, None)
        loc = r.headers.get('Location'); p = None
        for _ in range(400):
            try: p = sess.get(loc)
            except Exception as e:
                print(cid,'NET-poll',e,flush=True); time.sleep(20); continue
            ra = p.headers.get('Retry-After')
            if ra: time.sleep(float(ra)); continue
            break
        try: j = p.json()
        except Exception:
            print(cid, 'POLL-BAD', p.text[:200], flush=True); return (fld, aC, None)
        aid = j.get('alpha')
        if not aid:
            print(f'{cid} SIM-FAIL {json.dumps(j)[:200]}', flush=True); return (fld, aC, None)
        d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
        d['_cid'] = cid
        json.dump(d, open(of, 'w'), ensure_ascii=False)
    d = json.load(open(of, encoding='utf-8'))
    b = d.get('is') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    lc = b.get('longCount') or 0; sc = b.get('shortCount') or 0
    has = 'Y' if (lc > 0 and sc > 0 and S != 0) else 'N'
    print(f'{d.get("_cid")} {d.get("id")} aC={aC} S={S:.3f} F={F:.3f} L={lc} Sh={sc} 数据={has}', flush=True)
    return (fld, aC, dict(aid=d.get('id'), S=round(S,3), F=round(F,3), lc=lc, sc=sc, has=has))

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        results = list(ex.map(run_one, FIELDS))
    n = sum(1 for _,_,r in results if r and r['has']=='Y')
    print(f'=== 覆盖验证完毕：{n}/{len(results)} 有数据 ===', flush=True)
    with open(WL, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['field','alphaCount','alpha_id','S','F','longCount','shortCount','hasData'])
        for fld, aC, r in results:
            if r: w.writerow([fld, aC, r['aid'], r['S'], r['F'], r['lc'], r['sc'], r['has']])
    print('白名单已写', WL, flush=True)
