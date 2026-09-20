import json, os, requests, time
os.chdir(r"D:\Python\worldquant")
PC = "data/alpha_quality_analysis/pnl"
aid = "qMxzlLYK"
fp = os.path.join(PC, aid + ".json")
if os.path.exists(fp):
    print("cached already"); raise SystemExit
s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
for att in range(20):
    r = s.get(f"https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl")
    ra = r.headers.get("Retry-After")
    if r.status_code == 200 and r.content:
        try:
            j = r.json()
            recs = j.get("records") or []
            if recs:
                d = {}
                prev = None
                for x in recs:
                    cum = float(x[1]); d[str(x[0])] = cum - (prev if prev is not None else cum); prev = cum
                json.dump(d, open(fp, "w", encoding="utf-8"))
                print("OK", len(d), "rows")
                raise SystemExit
        except SystemExit:
            raise
        except Exception:
            pass
    time.sleep(float(ra) if ra else 5)
print("FAILED after retries")
