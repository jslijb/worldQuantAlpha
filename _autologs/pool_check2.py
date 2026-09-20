import csv, json, os, requests, time
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/pool_check2.out", "w", encoding="utf-8")

with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    rows = [r for r in rd if r and r[0].strip()]
ids = list(dict.fromkeys(r[0].strip() for r in rows))
OUT.write(f"台账 {len(rows)} 行 / 唯一 {len(ids)}\n")

# 今日提交（按 dateSubmitted 美东 09-20）
today = [r for r in rows if len(r) > 8 and r[8].startswith("2026-09-20")]
OUT.write(f"美东 09-20 提交 {len(today)} 条: {[r[0] for r in today]}\n")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
ps = json.load(open("data/alpha_quality_analysis/pool_s.json", encoding="utf-8"))

need_pnl = [i for i in ids if not os.path.exists(f"data/alpha_quality_analysis/pnl/{i}.json")]
need_s = [i for i in ids if not ps.get(i)]
OUT.write(f"PnL 缺失 {len(need_pnl)}: {need_pnl[:8]}\n")
OUT.write(f"S 缺失 {len(need_s)}: {need_s[:8]}\n")

for aid in need_pnl:
    j = None
    for att in range(6):
        r = s.get(f"https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl")
        ra = r.headers.get("Retry-After")
        try:
            j = r.json()
            if j.get("records"):
                break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if j and j.get("records"):
        d = {}; prev = None
        for rec in j["records"]:
            cum = float(rec[1]); d[str(rec[0])] = cum - (prev if prev is not None else cum); prev = cum
        json.dump(d, open(f"data/alpha_quality_analysis/pnl/{aid}.json", "w", encoding="utf-8"))
        OUT.write(f"  补 PnL {aid} OK\n")
    else:
        OUT.write(f"  补 PnL {aid} FAILED\n")

for aid in need_s:
    d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
    ps[aid] = (d.get("is") or {}).get("sharpe")
    time.sleep(0.2)
    OUT.write(f"  补 S {aid} = {ps[aid]}\n")
json.dump(ps, open("data/alpha_quality_analysis/pool_s.json", "w", encoding="utf-8"), indent=1)
OUT.write(f"最终：S 覆盖 {sum(1 for i in ids if ps.get(i))}/{len(ids)}\n")
OUT.close()
print("ok")
