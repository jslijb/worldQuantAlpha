import json, glob, os
os.chdir(r"D:\Python\worldquant")
out = open("_autologs/w213_status.out", "w", encoding="utf-8")
def P(*a):
    print(*a, file=out)
fs = sorted(glob.glob("data/alpha_quality_analysis/mined/w213leg_*.json")) + \
     sorted(glob.glob("data/alpha_quality_analysis/mined/w213b_*.json"))
P("w213 legs produced:", len(fs))
for p in fs:
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        P("  BAD", p); continue
    iss = j.get("is") or {}
    s, f = iss.get("sharpe"), iss.get("fitness")
    ts = (j.get("test") or {}).get("sharpe")
    checks = iss.get("checks") or []
    fails = [c.get("name") for c in checks if isinstance(c, dict) and c.get("result") == "FAIL"]
    st = j.get("status")
    P(f"  {os.path.basename(p)[:-5]} id={j.get('id')} status={st} S={s} F={f} tS={ts} FAIL={fails}")
out.close()
