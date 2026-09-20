import csv, json, glob, os, re
os.chdir(r"D:\Python\worldquant")
base = "data/alpha_quality_analysis"

# 1) load verdicts: cid -> (corr, verdict)
verd = {}
vp = os.path.join(base, "SUBMIT_VERDICTS.csv")
with open(vp, encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    hdr = next(rd)
    for r in rd:
        if not r: continue
        # find cid col and corr col heuristically
        cid = r[0].strip()
        corr = None
        for cell in r:
            m = re.fullmatch(r"0?\.\d{3,4}", cell.strip())
            if m:
                v = float(m.group())
                if 0 < v < 1:
                    corr = v
        verd.setdefault(cid, []).append((r, corr))
print("VERDICT_HEADER:", hdr)
print("VERDICT_ROWS:", sum(len(v) for v in verd.values()))

# 2) ledger ids
with open(os.path.join(base, "SUBMITTED_LEDGER.csv"), encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    led_ids = set(r[0].strip() for r in rd if r and r[0].strip())

# 3) scan mined jsons for quality passers not in ledger
out = []
for p in glob.glob(os.path.join(base, "mined", "*.json")):
    cid = os.path.basename(p)[:-5]
    try:
        j = json.load(open(p, encoding="utf-8"))
    except Exception:
        continue
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
        vv = verd.get(cid, [])
        corr = None
        for _, c in vv:
            if c is not None:
                corr = c if corr is None else min(corr, c)
        out.append((corr if corr is not None else 9.9, cid, aid, round(sf, 2), round(float(ts), 2)))

out.sort()
no_corr = [o for o in out if o[0] == 9.9]
with_corr = [o for o in out if o[0] != 9.9]
print(f"\nQUALITY PASSERS (not in ledger): with_corr={len(with_corr)} unknown_corr={len(no_corr)}")
print("\n--- corr <= 0.78 (rescue candidates) ---")
for c, cid, aid, sf, ts in with_corr:
    if c <= 0.78:
        print(f"  corr={c:.4f} {cid} id={aid} SF={sf} tS={ts}")
print("\n--- corr unknown (first 25, by SF desc) ---")
no_corr.sort(key=lambda t: -t[3])
for c, cid, aid, sf, ts in no_corr[:25]:
    print(f"  {cid} id={aid} SF={sf} tS={ts}")
