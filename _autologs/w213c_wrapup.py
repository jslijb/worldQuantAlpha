# -*- coding: utf-8 -*-
# 收尾：LLNXPaea 判决补档（只追加）+ 台账核对
import csv, json, os, datetime
os.chdir(r"D:\Python\worldquant")
out = open("_autologs/w213c_wrapup.out", "w", encoding="utf-8")

# 1) 裁决档案补 LLNXPaea（submit_v3 在 POST-403 分支提前退出，未落档）
row = [datetime.datetime.now().isoformat(timespec="seconds"), "LLNXPaea", "w213c_07",
       "REJECTED", 0.9143, "SELF_CORRELATION",
       "403判决书全文见_autologs/verdict_LLNXPaea.out;对手=zq8jl99K(同骨架A结构,17分钟前提交)"]
with open("data/alpha_quality_analysis/SUBMIT_VERDICTS.csv", "a", encoding="utf-8-sig", newline="") as f:
    csv.writer(f).writerow(row[:6])
print("verdict row appended for LLNXPaea", file=out)

# 2) 台账核对
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", newline="", encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    header = next(rd)
    rows = [r for r in rd if r]
ids = [r[0].strip() for r in rows]
uniq = set(ids)
zq = [r for r in rows if r[0].strip() == "zq8jl99K"]
print(f"LEDGER rows={len(rows)} unique={len(uniq)} zq8jl99K_rows={len(zq)}", file=out)
for r in zq:
    print("  zq8jl99K:", r[1][:80], "S=", r[2], "F=", r[3], "dateSubmitted=", r[7] if len(r) > 7 else "?", file=out)
out.close()
print("done")
