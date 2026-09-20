import json, os, csv
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/highs_full.out", "w", encoding="utf-8")
targets = ['0mR2K6lr', 'pwRwWoJ3', 'j23Pl0e5', 'mLgd6nwX', 'e79kPeEM', 'kqjpepz8', '9qjqm3Q9']
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.DictReader(f)
    d = {r["id"]: r for r in rd if r.get("id")}
for aid in targets:
    r = d.get(aid)
    if not r:
        OUT.write(f"{aid} 不在台账\n")
        continue
    OUT.write(f"=== {aid} (S={r.get('S')}, F={r.get('F')}, neut={r.get('neutralization')}) ===\n")
    OUT.write((r.get("expr") or "") + "\n\n")
OUT.close()
print("ok")
