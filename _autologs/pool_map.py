import json, os, csv
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/pool_map.out", "w", encoding="utf-8")

ps = json.load(open("data/alpha_quality_analysis/pool_s.json", encoding="utf-8"))
expr = {}
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.DictReader(f)
    for r in rd:
        if r.get("id"):
            expr[r["id"]] = r.get("expr", "")

rows = [(aid, s) for aid, s in ps.items() if s]
rows.sort(key=lambda t: -t[1])
OUT.write("=== 池子 Sharpe TOP 15（对手地图）===\n")
for aid, s in rows[:15]:
    e = expr.get(aid, "")
    OUT.write(f"S={s:.2f} {aid}: {e[:190]}\n\n")

OUT.write(f"\n=== Sharpe 分布 ===\n")
import statistics as st
vals = [s for _, s in rows]
OUT.write(f"n={len(vals)} max={max(vals):.2f} min={min(vals):.2f} median={st.median(vals):.2f}\n")
OUT.write(f">=3.0: {sum(1 for v in vals if v>=3.0)} 条; 2.5~3.0: {sum(1 for v in vals if 2.5<=v<3.0)}; 2.0~2.5: {sum(1 for v in vals if 2.0<=v<2.5)}; <2.0: {sum(1 for v in vals if v<2.0)}\n")
OUT.close()
print("ok")
