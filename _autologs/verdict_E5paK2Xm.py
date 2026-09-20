import json, os, sys
os.chdir(r"D:\Python\worldquant")
aid = sys.argv[1] if len(sys.argv) > 1 else "E5paK2Xm"
with open("brain_credentials.txt") as f:
    cred = tuple(json.load(f))
import requests
s = requests.Session(); s.auth = cred
r = s.post("https://api.worldquantbrain.com/authentication")
assert r.status_code == 201, r.status_code
d = s.get(f"https://api.worldquantbrain.com/alphas/{aid}").json()
recs = ((d.get("is") or {}).get("selfCorrelated") or {}).get("records") or []
print("status:", d.get("status"), "| dateSubmitted:", d.get("dateSubmitted"))
for rec in recs[:8]:
    print("  opponent:", rec.get("id"), "corr=", rec.get("correlation"), "alphasS=", rec.get("alphaSharpe"))
# also fetch zq8jl99K pnl availability probe
r2 = s.get("https://api.worldquantbrain.com/alphas/zq8jl99K/recordsets/pnl")
print("zq8jl99K pnl probe:", r2.status_code, "| Retry-After:", r2.headers.get("Retry-After"), "| len:", len(r2.content))
