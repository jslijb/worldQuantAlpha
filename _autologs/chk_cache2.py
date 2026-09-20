import os, json
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/chk_cache.out", "w", encoding="utf-8")
for aid in ["LLNXEe7L", "zq8jl99K", "qMxzlLYK"]:
    f = f"data/alpha_quality_analysis/pnl/{aid}.json"
    if os.path.exists(f):
        d = json.load(open(f, encoding="utf-8"))
        OUT.write(f"{aid} OK {len(d)} days\n")
    else:
        OUT.write(f"{aid} MISSING\n")
# 台账唯一 id 数（池成员）
import csv
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    ids = [r[0].strip() for r in rd if r and r[0].strip()]
OUT.write(f"ledger rows={len(ids)} unique={len(set(ids))}\n")
missing = [i for i in set(ids) if not os.path.exists(f"data/alpha_quality_analysis/pnl/{i}.json")]
OUT.write(f"pnl missing for {len(missing)}: {missing[:10]}\n")
OUT.close()
print("ok")
