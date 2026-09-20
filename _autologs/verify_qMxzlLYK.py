import json, requests, os, csv
os.chdir(r"D:\Python\worldquant")
s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
for aid in ["qMxzlLYK"]:
    d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
    print(aid, "status:", d.get("status"), "| stage:", d.get("stage"), "| dateSubmitted:", d.get("dateSubmitted"))
    iss = d.get("is") or {}
    print("  S:", iss.get("sharpe"), "F:", iss.get("fitness"))
# ledger tail
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rows = [r for r in csv.reader(f) if r]
ids = [r[0].strip() for r in rows[1:] if r[0].strip()]
print("LEDGER rows:", len(rows)-1, "unique:", len(set(ids)), "| qMxzlLYK in ledger:", "qMxzlLYK" in set(ids))
