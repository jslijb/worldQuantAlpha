import json, os, glob
os.chdir(r"D:\Python\worldquant")
OUT = open("_autologs/w206_expr.out", "w", encoding="utf-8")
for cid in ["w206_05", "w206_01", "w206_00", "w204_02"]:
    p = f"data/alpha_quality_analysis/mined/{cid}.json"
    if not os.path.exists(p):
        OUT.write(f"=== {cid} 缺文件 ===\n")
        continue
    j = json.load(open(p, encoding="utf-8"))
    OUT.write(f"=== {cid} id={j.get('id')} ===\n")
    OUT.write(((j.get("regular") or {}).get("code") or "") + "\n")
    st = j.get("settings") or {}
    OUT.write(f"settings: neut={st.get('neutralization')} decay={st.get('decay')} delay={st.get('delay')} univ={st.get('universe')} trunc={st.get('truncation')}\n")
    iss = j.get("is") or {}
    OUT.write(f"IS: S={iss.get('sharpe')} F={iss.get('fitness')} T={iss.get('turnover')} R={iss.get('returns')}\n\n")
OUT.write("=== 生成器文件 ===\n")
for f in glob.glob("src/mine/mine_w20*.py"):
    OUT.write(f + "\n")
OUT.close()
print("ok")
