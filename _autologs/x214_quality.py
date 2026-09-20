import csv, json, glob, os, sys, time
os.chdir(r"D:\Python\worldquant")
import requests

base = "data/alpha_quality_analysis"
led_ids = set()
with open(os.path.join(base, "SUBMITTED_LEDGER.csv"), encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if r and r[0].strip(): led_ids.add(r[0].strip())

rows = []
for p in sorted(glob.glob(os.path.join(base, "mined", "x214_*.json"))):
    cid = os.path.basename(p)[:-5]
    try: j = json.load(open(p, encoding="utf-8"))
    except Exception: continue
    iss = j.get("is") or {}
    s, fit = iss.get("sharpe"), iss.get("fitness")
    ts = (j.get("test") or {}).get("sharpe")
    checks = iss.get("checks") or []
    fails = [c.get("name") for c in checks if isinstance(c, dict) and c.get("result") == "FAIL"]
    aid = j.get("id")
    st = j.get("status")
    if s is None or fit is None or aid is None:
        print(f"{cid}: incomplete (status={st})"); continue
    sf = float(s) + float(fit)
    ok = sf >= 4.0 and ts is not None and float(ts) >= 1.25 and not fails
    print(f"{cid}: id={aid} status={st} S={s} F={fit} SF={sf:.2f} tS={ts} FAIL={fails} GATE={'PASS' if ok else 'FAIL'}")
    if ok:
        rows.append((cid, aid, sf, float(ts)))

print(f"\nQUALITY PASS: {len(rows)}")
json.dump(rows, open("_autologs/x214_passers.json", "w"), indent=1)
