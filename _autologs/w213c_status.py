import json, glob, os
os.chdir(r"D:\Python\worldquant")
out = open("_autologs/w213c_status.out", "w", encoding="utf-8")
rows = []
meta = json.load(open("_autologs/search_combos_w213c.json", encoding="utf-8"))
for p in sorted(glob.glob("data/alpha_quality_analysis/mined/w213c_*.json")):
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
    if not j.get("id"):
        continue
    cid = os.path.basename(p)[:-5]
    iss = j.get("is") or {}
    s, f = iss.get("sharpe"), iss.get("fitness")
    if s is None or f is None:
        continue
    ts = (j.get("test") or {}).get("sharpe")
    checks = iss.get("checks") or []
    fails = [c.get("name") for c in checks if isinstance(c, dict) and c.get("result") == "FAIL"]
    sf = round(float(s) + float(f), 2)
    m = meta.get(cid, {})
    to = (iss.get("turnover") or 0)
    rows.append((sf, cid, j["id"], sf, round(float(s),2), round(float(f),2), ts, fails, m.get("struct"), m.get("ev"), m.get("ew"), m.get("S"), m.get("maxcorr"), to))
rows.sort(key=lambda r: -r[0])
for r in rows:
    print(f"  {r[1]} {r[2]} SF={r[3]} (S{r[4]}/F{r[5]}) tS={r[6]} FAIL={r[7]} struct={r[8]} ev={r[9]}(w{r[10]}) offlineS={r[11]} pred={r[12]} TO={r[13]:.3f}" if r[13] is not None else f"  {r[1]} SF={r[3]}", file=out)
ok = [r for r in rows if r[3] >= 4.0 and r[6] is not None and float(r[6]) >= 1.25 and not r[7]]
print(f"\n质量闸门达标: {len(ok)} 条", file=out)
for r in ok:
    print(f"  >>> {r[1]} {r[2]} SF={r[3]} S={r[4]} F={r[5]} tS={r[6]} ev={r[9]}(w{r[10]})", file=out)
out.close()
print("done")
