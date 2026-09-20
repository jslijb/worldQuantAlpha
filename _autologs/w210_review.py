import json, glob, os
os.chdir(r"D:\Python\worldquant")
for pat in ("w210_*", "w211_*"):
    print("===", pat, "===")
    rows = []
    for p in sorted(glob.glob(f"data/alpha_quality_analysis/mined/{pat}.json")):
        try:
            j = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        if not j.get("id"):
            continue  # legs are w210leg_*
        iss = j.get("is") or {}
        s, f = iss.get("sharpe"), iss.get("fitness")
        if s is None or f is None:
            continue
        ts = (j.get("test") or {}).get("sharpe")
        checks = iss.get("checks") or []
        fails = [c.get("name") for c in checks if isinstance(c, dict) and c.get("result") == "FAIL"]
        sf = round(float(s) + float(f), 2)
        rows.append((os.path.basename(p)[:-5], j["id"], sf, round(float(s),2), round(float(f),2), round(float(ts),2) if ts is not None else None, fails, ((j.get("regular") or {}).get("code",""))[:110]))
    rows.sort(key=lambda r: -r[2])
    for r in rows:
        print(f"  {r[0]} {r[1]} SF={r[2]} (S{r[3]}/F{r[4]}) tS={r[5]} FAIL={r[6]}")
        print(f"      {r[7]}")
