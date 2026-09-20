import json, os, requests, time

os.chdir(r"D:\Python\worldquant")
s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201

targets = ["LLNXEe7L", "zq8jl99K", "qMxzlLYK"]
for aid in targets:
    f = f"data/alpha_quality_analysis/pnl/{aid}.json"
    if os.path.exists(f):
        print(aid, "cached")
        continue
    j = None
    for att in range(8):
        r = s.get(f"https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl")
        ra = r.headers.get("Retry-After")
        try:
            j = r.json()
            if j.get("records"):
                break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if not j or not j.get("records"):
        print(aid, "FAILED")
        continue
    d = {}
    prev = None
    for r in j["records"]:
        cum = float(r[1]); d[str(r[0])] = cum - (prev if prev is not None else cum); prev = cum
    json.dump(d, open(f, "w", encoding="utf-8"))
    print(aid, "saved", len(d), "days")
