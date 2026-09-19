import csv, json, glob, os, re
from datetime import datetime, timezone, timedelta

os.chdir(r"D:\Python\worldquant")
led = []
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    for row in csv.reader(f):
        if row and row[0].strip():
            led.append(row)
header = led[0]
rows = led[1:]
ids = set(r[0].strip() for r in rows if r and r[0].strip())
print("LEDGER_ROWS(total incl header):", len(led))
print("LEDGER_VALID_IDS:", len(ids))
et = timezone(timedelta(hours=-4))
today = datetime.now(et).strftime("%Y-%m-%d")
cnt_today = 0
for r in rows:
    # find dateSubmitted column
    pass
# locate dateSubmitted col
di = None
for i,h in enumerate(header):
    if "date" in h.lower() or "submit" in h.lower():
        di = i
if di is not None:
    for r in rows:
        if len(r)>di and r[di].startswith(today):
            cnt_today += 1
print("TODAY_ET:", today, "COUNT_TODAY:", cnt_today)

# mine json inventory
mined = glob.glob("data/alpha_quality_analysis/mined/*.json")
print("MINED_JSON_TOTAL:", len(mined))
# quality passers not in ledger
passers = []
for p in mined:
    try:
        with open(p, encoding="utf-8") as f:
            j = json.load(f)
    except Exception:
        continue
    def g(*ks):
        for k in ks:
            if k in j: return j[k]
        return None
    s = g("is_sharpe","sharpe","S")
    fit = g("is_fitness","fitness","F")
    ts = g("test_sharpe","tS") 
    cid = g("_cid","cid") or os.path.basename(p).replace(".json","")
    aid = g("alpha_id","_alpha_id","id")
    checks = j.get("is",{}).get("checks") if isinstance(j.get("is"),dict) else j.get("checks")
    fail = False
    if isinstance(checks,list):
        for c in checks:
            if isinstance(c,dict) and c.get("result")=="FAIL":
                fail=True; break
    if s is None or fit is None: continue
    try: sf = float(s)+float(fit)
    except: continue
    if sf>=4.0 and (ts is None or float(ts)>=1.25) and not fail:
        if aid and str(aid) in ids: continue
        passers.append((cid, aid, round(sf,2), ts))
passers.sort()
print("QUALITY_PASSERS_NOT_IN_LEDGER:", len(passers))
for c,a,sf,ts in passers[:60]:
    print(" ", c, a, "SF",sf, "tS",ts)
