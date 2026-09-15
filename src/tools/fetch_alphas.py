# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
"""登录 WQ Brain，批量拉取 31 个已提交 Alpha 的真实原始 JSON 落盘。"""
import requests, json, time, os, sys

OUT = r"D:\Python\worldquant\data/alpha_quality_analysis\raw"
os.makedirs(OUT, exist_ok=True)

IDS = [
    "58p2XdxX","wpjoxbbd","rKj7w0Z1","RR79x16n","9qX8Nr6r","vRjG1Jzw","QP7z069Q","1YwKML56",
    "1YwRK1wW","9qX3M2mq","kqjpepz8","N1QxNQK7","e79kPeEM","qMW92Az2","E5v15JPJ","le8ddYbe",
    "akLqqmm6","A10MYm3d","QP3XalpK","wpYgReRx","MP1mQRro","om6ea8j6","RRVLeabj","58QVJA9M",
    "6XrbGx1L","58Q7kl1z","A10a7pdY","883OXpJl","j23nOrVW","LL9n2Jp1","E5vkQ76G"
]

with open('brain_credentials.txt') as f:
    user, pw = json.load(f)

s = requests.Session()
s.auth = (user, pw)
s.headers.update({'Accept': 'application/json;version=2.0'})

r = s.post('https://api.worldquantbrain.com/authentication')
print("AUTH:", r.status_code, r.text[:120])
if r.status_code not in (200, 201):
    print("AUTH FAILED"); sys.exit(1)

def fetch(aid, tries=3):
    for t in range(tries):
        try:
            rr = s.get(f'https://api.worldquantbrain.com/alphas/{aid}', timeout=30)
            if rr.status_code == 200:
                return rr.json()
            if rr.status_code == 429:
                print(f"  {aid} rate-limited, wait 20s"); time.sleep(20); continue
            print(f"  {aid} HTTP {rr.status_code}: {rr.text[:120]}")
        except Exception as e:
            print(f"  {aid} err {e}, retry"); time.sleep(5)
    return None

ok = 0
for i, aid in enumerate(IDS, 1):
    d = fetch(aid)
    if d:
        with open(os.path.join(OUT, f"{aid}.json"), "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
        isd = d.get("is", {})
        print(f"[{i:2d}/31] {aid} status={d.get('status')} S={isd.get('sharpe')} F={isd.get('fitness')} T={isd.get('turnover')} DD={isd.get('drawdown')} R={isd.get('returns')}")
        ok += 1
    else:
        print(f"[{i:2d}/31] {aid} FAILED")
    time.sleep(1.2)

print(f"\nDone. {ok}/31 fetched -> {OUT}")
