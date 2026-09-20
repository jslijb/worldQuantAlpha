import csv, json, os, requests, time

os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/s5_ledger.out", "w", encoding="utf-8")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

# 台账现有 id
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); header = next(rd)
    rows = [r for r in rd if r and r[0].strip()]
ids = [r[0].strip() for r in rows]
OUT.write(f"台账 {len(rows)} 行 / 唯一 {len(set(ids))}\n")
OUT.write(f"LLNXEe7L 在台账? {'LLNXEe7L' in ids}\n")

# 平台实况
d = s.get("https://api.worldquantbrain.com/alphas/LLNXEe7L").json()
iss = d.get("is") or {}
OUT.write(f"平台: status={d.get('status')} dateSubmitted={d.get('dateSubmitted')} S={iss.get('sharpe')} F={iss.get('fitness')} T={iss.get('turnover')} tS={(d.get('test') or {}).get('sharpe')}\n")
j = json.load(open("data/alpha_quality_analysis/mined/w218_s5.json", encoding="utf-8"))
expr = (j.get("regular") or {}).get("code") or ""
OUT.write(f"expr: {expr[:200]}\n")

if "LLNXEe7L" not in ids:
    row = ["LLNXEe7L", expr, iss.get("sharpe"), iss.get("fitness"), iss.get("turnover"), "",
           "", "0.6821", d.get("dateSubmitted"), j.get("settings", {}).get("decay", 10),
           j.get("settings", {}).get("neutralization", "SUBINDUSTRY"), "0916-v3-0920-w218-w218_s5"]
    with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow(row)
    OUT.write("已追加台账行\n")
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    rows2 = [r for r in rd if r and r[0].strip()]
ids2 = [r[0].strip() for r in rows2]
OUT.write(f"追加后：{len(rows2)} 行 / 唯一 {len(set(ids2))}\n")
OUT.close()
print("done")
