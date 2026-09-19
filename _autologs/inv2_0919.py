import csv, json, glob, os
os.chdir(r"D:\Python\worldquant")
rows=[]
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    header = next(rd)
    for r in rd:
        if r: rows.append(r)
print("HEADER:", header)
ids=[r[0].strip() for r in rows]
from collections import Counter
dup = {k:v for k,v in Counter(ids).items() if v>1}
print("ROWS:", len(rows), "UNIQUE:", len(set(ids)), "DUP:", dup)
blank = [i for i,x in enumerate(ids) if not x]
print("BLANK_IDS:", blank)

def walk(j, pref=""):
    out=[]
    if isinstance(j, dict):
        for k,v in j.items():
            if isinstance(v,(int,float,str)) and not isinstance(v,bool):
                out.append(pref+k)
            elif isinstance(v,dict):
                out += walk(v, pref+k+".")
    return out

sample = json.load(open("data/alpha_quality_analysis/mined/z8_d4_xo_mix.json", encoding="utf-8"))
print("NUMERIC_KEYS:", [k for k in walk(sample) if "sharpe" in k or "fitness" in k or "turnover" in k])
print("HAS_IS_CHECKS:", "checks" in sample.get("is",{}))
