import json, os, requests, time, csv, glob

os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/probe2_scan3.out", "w", encoding="utf-8")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

# 1) 实测 s2（同骨架兄弟，S +13.4% vs kqoq0zed）
OUT.write("=== POST N1ajLwA7 (w218_s2, S2.29 vs kqoq0zed 2.02 = +13.4%) ===\n")
r = s.post("https://api.worldquantbrain.com/alphas/N1ajLwA7/submit")
OUT.write(f"HTTP {r.status_code}\n")
try:
    OUT.write("BODY:\n" + json.dumps(r.json(), indent=1, ensure_ascii=False)[:2500] + "\n")
except Exception:
    OUT.write("BODY(raw): " + r.text[:1500] + "\n")
time.sleep(6)
d = s.get("https://api.worldquantbrain.com/alphas/N1ajLwA7").json()
OUT.write(f"6s后: status={d.get('status')} dateSubmitted={d.get('dateSubmitted')}\n")
for c in ((d.get('is') or {}).get('checks') or []):
    if isinstance(c, dict) and c.get('name') == 'SELF_CORRELATION':
        OUT.write("SELF_CORRELATION: " + json.dumps(c, ensure_ascii=False)[:800] + "\n")

# 2) 扫历史判决库：corr 0.68~0.9 且质量达标的候选（概率带）
OUT.write("\n=== 历史判决库扫描（SUBMIT_VERDICTS）===\n")
vfs = glob.glob("data/alpha_quality_analysis/SUBMIT_VERDICTS*.csv")
OUT.write("verdict files: " + str(vfs) + "\n")
pool = []
for vf in vfs:
    with open(vf, encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        try:
            header = next(rd)
        except StopIteration:
            continue
        OUT.write(f"  {os.path.basename(vf)} header={header}\n")
        for row in rd:
            if not row:
                continue
            pool.append((os.path.basename(vf), row))
OUT.write(f"总判决行数: {len(pool)}\n")
for vf, row in pool[:5]:
    OUT.write(f"  sample: {row[:8]}\n")
OUT.close()
print("done")
