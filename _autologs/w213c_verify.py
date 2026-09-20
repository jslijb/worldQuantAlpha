import csv, json, os, time
import requests
os.chdir(r"D:\Python\worldquant")
out = open("_autologs/w213c_verify.out", "w", encoding="utf-8")

ids = ["zq8jl99K", "LLNXPaea", "N1a6YGLq", "3qX6MQRO", "9qj6z66o"]
with open("data/alpha_quality_analysis/SUBMITTED_LEDGER.csv", newline="", encoding="utf-8-sig") as f:
    rd = csv.reader(f)
    header = next(rd)
    rows = [r for r in rd if r]
led_ids = set(r[0].strip() for r in rows if r and r[0].strip())
print("LEDGER rows:", len(rows), "unique:", len(led_ids), file=out)
for a in ids:
    in_led = a in led_ids
    print(f"  {a}: in_ledger={in_led}", file=out)

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
print("=== 平台实况 ===", file=out)
for a in ids:
    for _ in range(5):
        try:
            r = s.get(f"https://api.worldquantbrain.com/alphas/{a}")
            if r.headers.get("Retry-After"):
                time.sleep(float(r.headers["Retry-After"])); continue
            d = r.json()
            break
        except Exception:
            time.sleep(4); continue
    st = d.get("status"); stg = d.get("stage")
    ds = d.get("dateSubmitted")
    print(f"  {a}: status={st} stage={stg} dateSubmitted={ds}", file=out)
out.close()
print("done")
