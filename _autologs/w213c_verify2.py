import json, os, time
import requests
os.chdir(r"D:\Python\worldquant")
out = open("_autologs/w213c_verify2.out", "w", encoding="utf-8")
ids = ["LLNXPaea", "N1a6YGLq", "3qX6MQRO", "9qj6z66o", "YPbmRAgJ", "w213c_00"]
s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
for a in ["LLNXPaea", "N1a6YGLq", "3qX6MQRO", "9qj6z66o"]:
    d = {}
    for _ in range(6):
        try:
            r = s.get(f"https://api.worldquantbrain.com/alphas/{a}")
            if r.headers.get("Retry-After"):
                time.sleep(float(r.headers["Retry-After"])); continue
            d = r.json(); break
        except Exception:
            time.sleep(4)
    print(f"{a}: status={d.get('status')} stage={d.get('stage')} dateSubmitted={d.get('dateSubmitted')}", file=out)
    # 若 403 回执相关，查 selfCorrelated 是否 PENDING
    isc = ((d.get("is") or {}).get("selfCorrelated"))
    if isinstance(isc, dict):
        print(f"   selfCorrelated.status={isc.get('status')}", file=out)
out.close()
print("done")
