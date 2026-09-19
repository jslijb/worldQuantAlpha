# -*- coding: utf-8 -*-
import glob, json, os
os.chdir(r"D:\Python\worldquant")
fs = sorted(glob.glob("data/alpha_quality_analysis/mined/w210_[0-9]*.json"))
out = []
out.append(f"combos_done={len(fs)}")
for p in fs:
    d = json.load(open(p, encoding="utf-8"))
    iss = d.get("is") or {}
    te = d.get("test") or {}
    s = iss.get("sharpe") or 0; f = iss.get("fitness") or 0
    ts = te.get("sharpe") or 0
    fa = [c.get("name") for c in (iss.get("checks") or []) if c.get("result") == "FAIL"]
    ok = "PASS" if (s + f >= 4.0 and ts >= 1.25 and not fa) else "fail"
    out.append(f"{os.path.basename(p)[:-5]} {d.get('_cid','')} id={d.get('id')} SF={s+f:.2f} tS={ts} FAIL={fa} [{ok}]")
open(r"_autologs\w210_status.out", "w", encoding="utf-8").write("\n".join(out))
print("done")
