import json, os, requests, time, csv

os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/probe3.out", "w", encoding="utf-8")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

OUT.write("=== N1ajLwA7 状态跟踪 ===\n")
for i in range(4):
    d = s.get("https://api.worldquantbrain.com/alphas/N1ajLwA7").json()
    iss = d.get("is") or {}
    sc = [c for c in (iss.get("checks") or []) if isinstance(c, dict) and c.get("name") == "SELF_CORRELATION"]
    OUT.write(f"  t+{i*12}s status={d.get('status')} dateSubmitted={d.get('dateSubmitted')} selfCorrCheck={json.dumps(sc, ensure_ascii=False)[:400]}\n")
    time.sleep(12)

OUT.write("\n=== 历史判决库：corr 0.68~0.92 的候选（Sharpe 提升概率带）===\n")
with open("data/alpha_quality_analysis/SUBMIT_VERDICTS.csv", encoding="utf-8-sig") as f:
    rd = csv.DictReader(f)
    rows = [r for r in rd]
band = [r for r in rows if r.get("selfCorr") and 0.68 <= float(r["selfCorr"]) <= 0.92 and r.get("verdict") == "REJECTED"]
OUT.write(f"总 {len(rows)} 行，概率带内 {len(band)} 条\n")
# 拉这些 alpha 的平台 S
OUT.write("\n=== 概率带候选的平台指标 ===\n")
res = []
for r in band:
    aid = r["alpha_id"]
    try:
        d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
        iss = d.get("is") or {}
        res.append((aid, r["cid"], float(r["selfCorr"]), iss.get("sharpe"), iss.get("fitness"), d.get("status")))
        time.sleep(0.15)
    except Exception as e:
        res.append((aid, r["cid"], float(r["selfCorr"]), None, None, f"ERR {e}"))
res.sort(key=lambda t: t[2])
for aid, cid, corr, sh, fi, st in res:
    OUT.write(f"  {aid} {cid} corr={corr} S={sh} F={fi} status={st}\n")
OUT.close()
print("done")
