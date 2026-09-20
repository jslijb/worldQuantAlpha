import json, os, glob, requests, time
os.chdir(r"D:\Python\worldquant")
PNLDIR = "data/alpha_quality_analysis/pnl"

def get_pnl(aid):
    fp = os.path.join(PNLDIR, aid + ".json")
    if os.path.exists(fp):
        try:
            d = json.load(open(fp))
            if d: return d
        except Exception: pass
    with open("brain_credentials.txt") as f:
        s = requests.Session(); s.auth = tuple(json.load(f))
    s.post("https://api.worldquantbrain.com/authentication")
    for _ in range(6):
        r = s.get(f"https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl")
        ra = r.headers.get("Retry-After")
        if r.status_code == 200 and r.content:
            try:
                d = r.json()
                rec = d.get("records") or []
                if rec:
                    json.dump(rec, open(fp, "w"))
                    return rec
            except Exception:
                pass
        if not ra: break
        time.sleep(float(ra) + 0.2)
    return None

def series(rec):
    # pnl records: [date, pnl] cumulative -> diff
    vals = [float(r[1]) for r in rec]
    return [vals[i] - vals[i-1] for i in range(1, len(vals))]

def corr(a, b):
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
    ma, mb = sum(a)/n, sum(b)/n
    num = sum((x-ma)*(y-mb) for x, y in zip(a, b))
    da = (sum((x-ma)**2 for x in a))**.5
    db = (sum((y-mb)**2 for y in b))**.5
    return num/(da*db+1e-12)

targets = {
    "x214_w54c_SEC": "E5paK2Xm",
    "w125_c": "Vk6AxE1b", "w125_d": "j23qYr8O", "w131_h": "QPbPVOn5", "w54_c": "blRJRxvl",
}
pnls = {}
for cid, aid in targets.items():
    rec = get_pnl(aid)
    if rec:
        pnls[cid] = series(rec)
        print(f"{cid}({aid}): pnl ok, {len(rec)} rows")
    else:
        print(f"{cid}({aid}): PNL UNAVAILABLE")

zrec = get_pnl("zq8jl99K")
zq8 = series(zrec) if zrec else None
print("zq8jl99K:", "ok" if zq8 else "UNAVAILABLE")
if zq8:
    for cid, ser in pnls.items():
        print(f"  corr({cid}, zq8jl99K) = {corr(ser, zq8):.4f}")
    ids = list(pnls)
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            print(f"  corr({ids[i]}, {ids[j]}) = {corr(pnls[ids[i]], pnls[ids[j]]):.4f}")
