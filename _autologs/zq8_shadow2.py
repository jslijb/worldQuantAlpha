import json, os
os.chdir(r"D:\Python\worldquant")
PC = "data/alpha_quality_analysis/pnl"
fix = ["E5paK2Xm", "Vk6AxE1b", "j23qYr8O", "QPbPVOn5", "blRJRxvl"]
for aid in fix:
    fp = os.path.join(PC, aid + ".json")
    d = json.load(open(fp, encoding="utf-8"))
    if isinstance(d, dict):
        print(aid, "already dict, skip"); continue
    out = {}
    prev = None
    for r in d:
        cum = float(r[1]); out[str(r[0])] = cum - (prev if prev is not None else cum); prev = cum
    json.dump(out, open(fp, "w", encoding="utf-8"))
    print(aid, "fixed -> dict daily,", len(out), "rows")

# recompute shadow
def load(aid):
    return {k: float(v) for k, v in json.load(open(os.path.join(PC, aid + ".json"), encoding="utf-8")).items()}

def corr(a, b):
    ks = sorted(set(a) & set(b))
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = sum(x)/len(x); my = sum(y)/len(y)
    sx = sum((v-mx)**2 for v in x) ** .5; sy = sum((v-my)**2 for v in y) ** .5
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(ks))) / (sx*sy)

zq8 = load("zq8jl99K")
targets = {"x214_w54c_SEC": "E5paK2Xm", "w125_c": "Vk6AxE1b", "w125_d": "j23qYr8O", "w131_h": "QPbPVOn5", "w54_c": "blRJRxvl"}
for cid, aid in targets.items():
    print(f"corr({cid}, zq8jl99K) = {corr(load(aid), zq8):.4f}")
ids = list(targets)
for i in range(len(ids)):
    for j in range(i+1, len(ids)):
        print(f"corr({targets[ids[i]]}, {targets[ids[j]]}) = {corr(load(targets[ids[i]]), load(targets[ids[j]])):.4f}")
