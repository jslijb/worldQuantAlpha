# -*- coding: utf-8 -*-
# 重取完整 403 判决书（POST /submit 的 body 全文，不截断）
import os, json, time, sys
import requests
os.chdir(r"D:\Python\worldquant")
aid = sys.argv[1]
out = open(f"_autologs/verdict_{aid}.out", "w", encoding="utf-8")
s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
print(f"{aid} status={d.get('status')} stage={d.get('stage')}", file=out)
r = s.post(f"https://api.worldquantbrain.com/alphas/{aid}/submit")
print(f"POST -> {r.status_code}", file=out)
print("BODY:", r.text, file=out)
# 若 200/201，走轮询
if r.status_code in (200, 201):
    loc = r.headers.get("Location") or f"https://api.worldquantbrain.com/alphas/{aid}/submit"
    for i in range(40):
        d2 = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
        if d2.get("status") == "ACTIVE" or d2.get("stage") == "OS":
            print(f"VERDICT: ACCEPTED dateSubmitted={d2.get('dateSubmitted')}", file=out)
            break
        p = s.get(loc)
        ra = p.headers.get("Retry-After")
        if ra:
            time.sleep(min(float(ra), 10)); continue
        try:
            j = p.json()
        except Exception:
            time.sleep(5); continue
        checks = (j.get("is") or {}).get("checks") or []
        fails = [c["name"] for c in checks if c.get("result") == "FAIL"]
        if fails:
            print("VERDICT: REJECTED fails=", fails, file=out)
            print("BODY:", json.dumps(j, ensure_ascii=False), file=out)
            break
        time.sleep(5)
    else:
        print("VERDICT: TIMEOUT", file=out)
out.close()
print("done")
