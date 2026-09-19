# -*- coding: utf-8 -*-
import csv, os
os.chdir(r"D:\Python\worldquant")
LEDGER = "data/alpha_quality_analysis/SUBMITTED_LEDGER.csv"

note = ("group_rank(fnd6_mfma2_revt/assets, subindustry) + group_rank(-ts_mean(abs(returns)/volume, 20), subindustry) + rank(-ts_delta(close, 2))")
row = ["YP57jVzo", note, "2.14", "1.91", "0.1363", "0.109", "0.0645", "0.6804",
       "2026-09-09T03:27:30-04:00", "8", "SUBINDUSTRY",
       "2026-09-19-correction: 本行是更正行。原台账把 YP57jVzo 记了两行(一行有selfCorr缺dateSubmitted,一行有dateSubmitted缺selfCorr);经平台核实 GET /alphas/YP57jVzo = ACTIVE/OS, 仅提交过一次(2026-09-09T03:27:30-04:00), 属重复记账非重复提交。本行把两行缺失字段合并补全。台账计数口径改为按唯一 id 计, 有效提交 = 86, Super Alpha 差 = 14。"]

with open(LEDGER, "a", encoding="utf-8", newline="") as f:
    csv.writer(f).writerow(row)

# verify
with open(LEDGER, encoding="utf-8-sig") as f:
    rd = csv.reader(f); next(rd)
    rows = [r for r in rd if r]
same = [r for r in rows if r and r[0].strip() == "YP57jVzo"]
ids = set(r[0].strip() for r in rows if r)
with open(r"D:\Python\worldquant\_autologs\corr_append_0919.out", "w", encoding="utf-8") as f:
    f.write(f"total_rows={len(rows)} unique_ids={len(ids)} yp57_rows={len(same)}\n")
    f.write(f"last_batch_field={rows[-1][11][:80]}\n")
print("done")
