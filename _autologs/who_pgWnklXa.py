import json, os, requests
os.chdir(r"D:\Python\worldquant")
s = requests.Session()
s.auth = tuple(json.load(open("brain_credentials.txt")))
assert s.post("https://api.worldquantbrain.com/authentication").status_code == 201
d = s.get("https://api.worldquantbrain.com/alphas/pgWnklXa").json()
print("status:", d.get("status"), "| dateSubmitted:", d.get("dateSubmitted"))
iss = d.get("is") or {}
print("S:", iss.get("sharpe"), "F:", iss.get("fitness"))
print("expr:", (d.get("regular") or {}).get("code"))
st = d.get("settings") or {}
print("neut:", st.get("neutralization"), "decay:", st.get("decay"))
