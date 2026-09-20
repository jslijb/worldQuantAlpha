import json, glob, os
os.chdir(r"D:\Python\worldquant")
out = open("_autologs/w210_passers_expr.txt", "w", encoding="utf-8")
for cid in ("w210_00", "w210_06", "w210_08", "w210_12"):
    p = f"data/alpha_quality_analysis/mined/{cid}.json"
    j = json.load(open(p, encoding="utf-8"))
    iss = j.get("is") or {}
    print(cid, j.get("id"), "S", iss.get("sharpe"), "F", iss.get("fitness"), "tS", (j.get("test") or {}).get("sharpe"), file=out)
    print("  ", (j.get("regular") or {}).get("code", ""), file=out)
    print(file=out)
out.close()
print("done")
