import json, os, csv
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/lows_map.out", "w", encoding="utf-8")
ps = json.load(open("data/alpha_quality_analysis/pool_s.json", encoding="utf-8"))
led = {}
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r.get("id"):
            led[r["id"]] = r.get("expr", "")
rows = sorted([(a, s) for a, s in ps.items() if s], key=lambda t: t[1])
OUT.write("=== 池子低 Sharpe 成员（豁免线 1.1× 最低的区域）===\n")
for aid, s in rows[:24]:
    OUT.write(f"S={s:.2f} {aid}: {led.get(aid,'')[:150]}\n\n")
OUT.close()
print("ok")
