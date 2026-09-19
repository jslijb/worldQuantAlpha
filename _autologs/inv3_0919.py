import csv, json, glob, os
os.chdir(r"D:\Python\worldquant")
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    ids = set(r[0].strip() for r in rd if r)
# duplicate detail
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    duprows = [r for r in rd if r and r[0].strip()=="YP57jVzo"]
for r in duprows:
    print("DUPROW:", r[0], r[8], r[11], r[1][:60])

passers=[]; parse_fail=0
for p in glob.glob("data/alpha_quality_analysis/mined/*.json"):
    try:
        j=json.load(open(p,encoding="utf-8"))
    except Exception:
        parse_fail+=1; continue
    iss=j.get("is",{}) or {}
    s=iss.get("sharpe"); fit=iss.get("fitness")
    if s is None or fit is None: continue
    try: sf=float(s)+float(fit)
    except: continue
    ts=(j.get("test") or {}).get("sharpe")
    checks=iss.get("checks") or []
    fail=any(isinstance(c,dict) and c.get("result")=="FAIL" for c in checks)
    aid=j.get("id")
    if sf>=4.0 and ts is not None and float(ts)>=1.25 and not fail:
        if aid in ids: continue
        cid=os.path.basename(p)[:-5]
        passers.append((cid,aid,round(sf,2),round(float(ts),2),j.get("status")))
passers.sort()
print("PARSE_FAIL:", parse_fail)
print("QUALITY_PASSERS_NOT_IN_LEDGER:", len(passers))
for c,a,sf,ts,st in passers:
    print(" ",c,a,"SF",sf,"tS",ts,"status",st)
