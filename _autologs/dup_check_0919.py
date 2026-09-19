# -*- coding: utf-8 -*-
import csv, json, os, requests
os.chdir(r"D:\Python\worldquant")
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); header = next(rd)
    rows = [r for r in rd if r and r[0].strip() == "YP57jVzo"]
out = []
out.append("HEADER: " + ",".join(header))
for i, r in enumerate(rows):
    out.append(f"--- row {i+1} ---")
    for h, v in zip(header, r):
        out.append(f"  {h} = {v}")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
d = s.get("https://api.worldquantbrain.com/alphas/YP57jVzo").json()
out.append("=== platform ===")
out.append(f"status: {d.get('status')} | stage: {d.get('stage')} | grade: {d.get('grade')}")
out.append(f"dateSubmitted: {d.get('dateSubmitted')}")
iss = d.get("is") or {}
out.append(f"is.sharpe: {iss.get('sharpe')} | is.fitness: {iss.get('fitness')}")
out.append("expr: " + ((d.get("regular") or {}).get("code") or "")[:150])

with open(r"D:\Python\worldquant\_autologs\dup_check_0919.out", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")
