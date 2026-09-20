import json, os, requests, time, glob, re

os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/lift_scan.out", "w", encoding="utf-8")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

# 对手 S（平台实测）
RIV = {'kqoq0zed': 2.02, 'qMxzlLYK': 2.28, 'e79PvPpE': 3.13, '6Xr2eQaJ': 2.27,
       'zq8jl99K': 2.68, 'XgWnklXa': None, 'pgWnklXa': None, 'y5Z85Je9': None}
for k in list(RIV):
    if RIV[k] is None:
        d = s.get(f"https://api.worldquantbrain.com/alphas/{k}").json()
        iss = d.get("is") or {}
        RIV[k] = iss.get("sharpe")
        time.sleep(0.2)

OUT.write("=== 对手 Sharpe（平台）===\n")
for k, v in RIV.items():
    OUT.write(f"  {k} S={v}\n")

# 历史判决：候选 -> (撞到的对手, corr)
JUDGED = {
    'w215_d1': ('kqoq0zed', 0.7153), 'w215_w54x': ('XgWnklXa', 0.7271), 'w215_w54y': ('pgWnklXa', 0.6978),
    'w215_h1': ('kqoq0zed', 0.93), 'w215_h2': ('kqoq0zed', 0.93),
    'w216_d3': ('qMxzlLYK', 0.8266),
    'w217_z4': ('qMxzlLYK', 0.7377), 'w217_z5': ('qMxzlLYK', 0.7591),
    'w218_s2': ('kqoq0zed', 0.7135), 'w218_s3': ('e79PvPpE', 0.7057), 'w218_s': ('kqoq0zed', 0.7117),
    'w218_u1': ('kqoq0zed', 0.7130), 'w218_p': ('6Xr2eQaJ', 0.7374),
    'w218_m': ('qMxzlLYK', 0.7622), 'w218_f': ('kqoq0zed', None), 'w218_f2': ('kqoq0zed', None),
}
OUT.write("\n=== 被 corr 挡掉的候选：Sharpe 提升重算 ===\n")
rows = []
for cid, (rival, corr) in JUDGED.items():
    p = f"data/alpha_quality_analysis/mined/{cid}.json"
    if not os.path.exists(p):
        OUT.write(f"  {cid} 缺 json\n")
        continue
    j = json.load(open(p, encoding="utf-8"))
    aid = j.get("id")
    iss = j.get("is") or {}
    s_mine = iss.get("sharpe")
    rs = RIV.get(rival)
    if s_mine is None or rs is None:
        rows.append((cid, aid, s_mine, rival, rs, None, corr))
        continue
    lift = (s_mine / rs - 1) * 100
    rows.append((cid, aid, s_mine, rival, rs, lift, corr))
rows.sort(key=lambda t: -(t[5] if t[5] is not None else -999))
for cid, aid, s_mine, rival, rs, lift, corr in rows:
    if lift is None:
        OUT.write(f"  {cid} {aid} S={s_mine} vs {rival}={rs} corr={corr} → 数据缺\n")
    else:
        flag = "★可试(≥10%)" if lift >= 10 else ("接近(5~10%)" if lift >= 5 else "不够")
        OUT.write(f"  {cid} {aid} S={s_mine} vs {rival}={rs} +{lift:.1f}% corr={corr} → {flag}\n")
OUT.close()
print("done")
