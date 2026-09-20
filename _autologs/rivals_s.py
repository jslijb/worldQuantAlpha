import csv, os
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/rivals_s.out", "w", encoding="utf-8")
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    header = next(rd)
    OUT.write("HEADER: " + str(header) + "\n")
    rows = [r for r in rd if r and r[0].strip()]
ids = ('kqoq0zed', 'e79PvPpE', '6Xr2eQaJ', 'qMxzlLYK', 'zq8jl99K', 'XgWnklXa', 'pgWnklXa')
for r in rows:
    if r[0].strip() in ids:
        OUT.write(" | ".join(f"{h}={v}" for h, v in zip(header, r) if h.lower() in ('alpha', 'id', 'sharpe', 'fitness', 'turnover', 'tests', 'expr', 'batch', 'datesubmitted', 'submitted', 'corr', 'selfcorr', 'status')) + "\n\n")
# 今天 6 条过闸候选
cands = {
    'LLNXEe7L': ('w218_s5', 4.55, 2.30, 2.25, 0.7642, 'kqoq0zed'),
    '88j6G01o': ('w218_s3', 4.50, 2.30, 2.20, 0.7057, 'e79PvPpE'),
    'N1ajLwA7': ('w218_s2', 4.48, 2.29, 2.19, 0.7135, 'kqoq0zed'),
    'd5b79j6K': ('w218_s', 4.44, 2.27, 2.17, 0.7117, 'kqoq0zed'),
    'e7b2VgaO': ('w218_u1', 4.26, 2.18, 2.08, 0.7130, 'kqoq0zed'),
    'xA3zlPJw': ('w218_p', 4.13, 2.11, 2.02, 0.7374, '6Xr2eQaJ'),
}
OUT.write("=== 今日过闸候选 ===\n")
for aid, (tag, sf, s, f_, corr, rival) in cands.items():
    OUT.write(f"{aid} {tag} SF={sf} S={s} F={f_} corr={corr} rival={rival}\n")
OUT.close()
print("done")
