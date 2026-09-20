import csv, os
os.chdir(r"D:\Python\worldquant")
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    hdr = next(rd)
    for r in rd:
        if any("pgwnklxa" in c.lower() for c in r):
            print("FOUND row:")
            for h, v in zip(hdr, r):
                print(f"  {h} = {v[:160]}")
            break
    else:
        print("not found in ledger rows")
