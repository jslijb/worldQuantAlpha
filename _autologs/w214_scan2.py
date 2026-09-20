import csv, json, glob, os
os.chdir(r"D:\Python\worldquant")
base = "data/alpha_quality_analysis"

verd = {}
with open(os.path.join(base, "SUBMIT_VERDICTS.csv"), encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if len(r) < 5 or not r[2].strip(): continue
        cid = r[2].strip()
        try: corr = float(r[4])
        except: corr = None
        verdict = r[3].strip()
        # keep best (lowest corr) per cid
        if cid not in verd or (corr is not None and (verd[cid][1] is None or corr < verd[cid][1])):
            verd[cid] = (verdict, corr)

with open(os.path.join(base, "SUBMITTED_LEDGER.csv"), encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    led_ids = set(r[0].strip() for r in rd if r and r[0].strip())

out = []
for p in glob.glob(os.path.join(base, "mined", "*.json")):
    cid = os.path.basename(p)[:-5]
    try: j = json.load(open(p, encoding="utf-8"))
    except Exception: continue
    iss = j.get("is") or {}
    s, fit = iss.get("sharpe"), iss.get("fitness")
    if s is None or fit is None: continue
    try: sf = float(s) + float(fit)
    except: continue
    ts = (j.get("test") or {}).get("sharpe")
    checks = iss.get("checks") or []
    fail = any(isinstance(c, dict) and c.get("result") == "FAIL" for c in checks)
    aid = j.get("id")
    if sf >= 4.0 and ts is not None and float(ts) >= 1.25 and not fail and aid not in led_ids:
        verdict, corr = verd.get(cid, ("", None))
        out.append((corr if corr is not None else 9.9, cid, aid, round(sf,2), round(float(ts),2), verdict))

with_corr = sorted([o for o in out if o[0] != 9.9])
unknown = sorted([o for o in out if o[0] == 9.9], key=lambda t: -t[3])
print(f"TOTAL_QP={len(out)} WITH_CORR={len(with_corr)} UNKNOWN={len(unknown)}")
print("\n--- REAL corr <= 0.76, excluding argmin family (w210/w211/w213) ---")
n = 0
for c, cid, aid, sf, ts, vd in with_corr:
    fam = cid.split("_")[0]
    if fam in ("w210", "w211", "w213", "x212", "w209"): continue
    if c <= 0.76:
        print(f"  corr={c:.4f} {cid} id={aid} SF={sf} tS={ts} verdict={vd}")
        n += 1
print(f"  ({n} rows)")
print("\n--- argmin family for reference (frozen today) ---")
for c, cid, aid, sf, ts, vd in with_corr[:8]:
    print(f"  corr={c:.4f} {cid} id={aid} SF={sf} tS={ts} verdict={vd}")
