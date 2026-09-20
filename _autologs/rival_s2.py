import json, os, requests, time

os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/rival_s2.out", "w", encoding="utf-8")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

rivals = ['kqoq0zed', 'e79PvPpE', '6Xr2eQaJ', 'qMxzlLYK', 'zq8jl99K']
OUT.write("=== 对手 IS 指标（平台实况）===\n")
rival_s = {}
for aid in rivals:
    d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
    iss = d.get("is") or {}
    tes = d.get("test") or {}
    rival_s[aid] = (iss.get("sharpe"), iss.get("fitness"), tes.get("sharpe"))
    OUT.write(f"{aid} S={iss.get('sharpe')} F={iss.get('fitness')} tS={tes.get('sharpe')} turnover={iss.get('turnover')}\n")
    time.sleep(0.3)

OUT.write("\n=== 我的候选 vs 撞到的对手 ===\n")
cands = [
    ('LLNXEe7L', 'w218_s5', 2.30, 0.7642, 'kqoq0zed'),
    ('88j6G01o', 'w218_s3', 2.30, 0.7057, 'e79PvPpE'),
    ('N1ajLwA7', 'w218_s2', 2.29, 0.7135, 'kqoq0zed'),
    ('d5b79j6K', 'w218_s', 2.27, 0.7117, 'kqoq0zed'),
    ('e7b2VgaO', 'w218_u1', 2.18, 0.7130, 'kqoq0zed'),
    ('xA3zlPJw', 'w218_p', 2.11, 0.7374, '6Xr2eQaJ'),
]
for aid, tag, s_mine, corr, rival in cands:
    rs = rival_s.get(rival, (None, None, None))[0]
    if rs:
        lift = (s_mine / rs - 1) * 100
        verdict = "Sharpe高10%+可试" if lift >= 10 else ("未达10%" if lift > 0 else "低于对手")
        OUT.write(f"{aid} {tag} 我的S={s_mine} 对手({rival})S={rs} 提升={lift:.1f}% corr={corr} → {verdict}\n")
    else:
        OUT.write(f"{aid} {tag} 对手S未知\n")
OUT.write("\n=== 我的候选 IS 指标（平台）===\n")
for aid, tag, *_ in cands:
    d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
    iss = d.get("is") or {}
    OUT.write(f"{aid} {tag} status={d.get('status')} S={iss.get('sharpe')} F={iss.get('fitness')} tS={(d.get('test') or {}).get('sharpe')}\n")
    time.sleep(0.3)
OUT.close()
print("done")
