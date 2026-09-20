import os, json
os.chdir(r"D:\Python\worldquant")
for aid in ["LLNXEe7L", "zq8jl99K", "qMxzlLYK"]:
    f = f"data/alpha_quality_analysis/pnl/{aid}.json"
    if os.path.exists(f):
        d = json.load(open(f, encoding="utf-8"))
        print(aid, "OK", len(d), "days")
    else:
        print(aid, "MISSING")
