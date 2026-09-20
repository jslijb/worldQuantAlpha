import json, os, requests, time

os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/submit_probe.out", "w", encoding="utf-8")

s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

TARGET = "LLNXEe7L"  # w218_s5, S 2.30 vs kqoq0zed 2.02 (+13.9%), corr 0.7642
OUT.write(f"=== POST /alphas/{TARGET}/submit 实测（Sharpe +13.9% vs 对手）===\n")
r = s.post(f"https://api.worldquantbrain.com/alphas/{TARGET}/submit")
OUT.write(f"HTTP {r.status_code}\n")
OUT.write("HEADERS: " + json.dumps({k: v for k, v in r.headers.items() if k.lower().startswith(('retry', 'location', 'content-type'))}) + "\n")
try:
    body = r.json()
    OUT.write("BODY(完整):\n" + json.dumps(body, indent=1, ensure_ascii=False) + "\n")
except Exception:
    OUT.write("BODY(raw): " + r.text[:3000] + "\n")

time.sleep(6)
d = s.get(f"https://api.worldquantbrain.com/alphas/{TARGET}").json()
OUT.write(f"\n=== 6 秒后 GET ===\nstatus={d.get('status')} dateSubmitted={d.get('dateSubmitted')}\n")
iss = d.get("is") or {}
for c in (iss.get("checks") or []):
    if isinstance(c, dict) and c.get("name") == "SELF_CORRELATION":
        OUT.write("SELF_CORRELATION check: " + json.dumps(c, ensure_ascii=False) + "\n")
OUT.close()
print("done")
