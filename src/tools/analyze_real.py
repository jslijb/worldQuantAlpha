# -*- coding: utf-8 -*-
"""基于真实拉取的 31 个 Alpha JSON，做深度质量分析 + 出图。"""
import json, os, glob, statistics as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import Counter

RAW = r"D:\Python\worldquant\alpha_quality_analysis\raw"
OUT = r"D:\Python\worldquant\alpha_quality_analysis"

# CLAUDE.md 手工记录的 S/F（用于校验）
CLAUDE = {
 "58p2XdxX":(1.55,1.34),"wpjoxbbd":(1.37,1.00),"rKj7w0Z1":(1.60,1.24),"RR79x16n":(1.47,1.16),
 "9qX8Nr6r":(1.26,1.49),"vRjG1Jzw":(1.79,1.27),"QP7z069Q":(1.64,1.38),"1YwKML56":(2.21,1.75),
 "1YwRK1wW":(2.11,1.31),"9qX3M2mq":(2.49,1.45),"kqjpepz8":(2.74,1.42),"N1QxNQK7":(2.06,1.17),
 "e79kPeEM":(3.02,1.79),"qMW92Az2":(2.32,1.60),"E5v15JPJ":(1.67,1.14),"le8ddYbe":(2.41,1.87),
 "akLqqmm6":(1.71,1.23),"A10MYm3d":(1.90,1.46),"QP3XalpK":(1.27,1.07),"wpYgReRx":(1.54,1.41),
 "MP1mQRro":(1.91,1.74),"om6ea8j6":(2.00,1.25),"RRVLeabj":(1.61,1.09),"58QVJA9M":(2.15,1.27),
 "6XrbGx1L":(2.26,1.75),"58Q7kl1z":(2.14,1.49),"A10a7pdY":(2.32,1.54),"883OXpJl":(2.48,1.78),
 "j23nOrVW":(1.92,1.51),"LL9n2Jp1":(2.22,1.57),"E5vkQ76G":(2.39,1.72)
}

rows = []
for fp in sorted(glob.glob(os.path.join(RAW, "*.json"))):
    d = json.load(open(fp, encoding="utf-8"))
    isd = d.get("is", {})
    chk = {c["name"]: (c.get("result"), c.get("value"), c.get("limit")) for c in isd.get("checks", [])}
    rows.append({
        "id": d.get("id"),
        "status": d.get("status"),
        "dateSubmitted": d.get("dateSubmitted"),
        "stage": d.get("stage"),
        "S": isd.get("sharpe"),
        "F": isd.get("fitness"),
        "T": isd.get("turnover"),
        "R": isd.get("returns"),
        "DD": isd.get("drawdown"),
        "margin": isd.get("margin"),
        "pnl": isd.get("pnl"),
        "selfCorr": isd.get("selfCorrelation"),
        "prodCorr": isd.get("prodCorrelation"),
        "checks": chk,
        "train": d.get("train"),
        "test": d.get("test"),
        "prod": d.get("prod"),
    })

print("=== Exploratory ===")
print("n =", len(rows))
print("selfCorrelation values:", [round(r["selfCorr"],3) for r in rows])
print("\nsample train/test/prod (first alpha):")
print("  train:", json.dumps(rows[0]["train"], ensure_ascii=False)[:300])
print("  test :", json.dumps(rows[0]["test"], ensure_ascii=False)[:300])
print("  prod :", json.dumps(rows[0]["prod"], ensure_ascii=False)[:300])

# ---- 校验 CLAUDE vs API ----
diffs = []
for r in rows:
    c = CLAUDE.get(r["id"])
    if c:
        diffs.append((r["id"], c[0]-r["S"], c[1]-r["F"]))
maxS = max(abs(x[1]) for x in diffs); maxF = max(abs(x[2]) for x in diffs)
print(f"\n=== Verify CLAUDE.md vs API ===\nmax |ΔS|={maxS:.2f}  max |ΔF|={maxF:.2f}  (n={len(diffs)})")

# ---- Fitness 拆解归因 ----
# F = S * sqrt(|R| / max(T, 0.125))
def fit(S, R, T):
    return S * (abs(R)/max(T,0.125))**0.5

for r in rows:
    r["F_T125"] = fit(r["S"], r["R"], 0.125)   # 把 turnover 压到平台下限
    r["F_T030"] = fit(r["S"], r["R"], 0.30)
    r["T_drag"] = r["F_T125"] - r["F"]          # 高 T 造成的 F 损失

# ---- 分层 ----
def tier(s,f):
    t=s+f
    return "A(>=4.0)" if t>=4.0 else "B(3.4-3.99)" if t>=3.4 else "C(3.0-3.39)" if t>=3.0 else "D(<3.0)"
for r in rows:
    r["tier"]=tier(r["S"],r["F"])
    r["SF"]=round(r["S"]+r["F"],2)

print("\n=== Real IS Summary ===")
for k in ("S","F","T","R","DD"):
    v=[r[k] for r in rows]
    print(f"{k}: mean={st.mean(v):.3f} median={st.median(v):.3f} min={min(v):.3f} max={max(v):.3f}")
tc=Counter(r["tier"] for r in rows)
print("tier:",dict(tc))
print(f"S+F>=4.0: {sum(1 for r in rows if r['SF']>=4.0)} | 3.4-3.99: {sum(1 for r in rows if 3.4<=r['SF']<4.0)} | <3.4: {sum(1 for r in rows if r['SF']<3.4)}")

# ---- 风险排序 ----
print("\n=== Top Turnover (>=0.4, 拖累 F) ===")
for r in sorted(rows,key=lambda x:-x["T"])[:6]:
    print(f"  {r['id']} T={r['T']:.3f} S={r['S']} F={r['F']} F_if_T125={r['F_T125']:.2f} drag={r['T_drag']:.2f}")
print("\n=== Top Drawdown (>0.10) ===")
for r in sorted(rows,key=lambda x:-x["DD"])[:6]:
    print(f"  {r['id']} DD={r['DD']:.3f} S={r['S']} F={r['F']}")

# ---- Checks 边界 ----
print("\n=== Check pass/fail counts ===")
allchecks=Counter()
for r in rows:
    for name,(res,val,lim) in r["checks"].items():
        allchecks[f"{name}:{res}"]+=1
for k,v in allchecks.items(): print(f"  {k}: {v}")
# 接近 limit 的边界
print("\n=== Near-limit checks (value within 15% of limit) ===")
for r in rows:
    for name,(res,val,lim) in r["checks"].items():
        if res in ("PASS","PENDING") and val is not None and lim is not None and lim!=0:
            if val/lim < 1.15:
                print(f"  {r['id']} {name} val={val} lim={lim} ratio={val/lim:.2f}")

# ---- 写 CSV ----
import csv
with open(os.path.join(OUT,"summary_real.csv"),"w",newline="",encoding="utf-8-sig") as fh:
    w=csv.writer(fh)
    w.writerow(["id","status","dateSubmitted","S","F","S+F","tier","T","R","DD","margin","pnl","selfCorr","F_if_T125","F_if_T030","T_drag"])
    for r in rows:
        w.writerow([r["id"],r["status"],r["dateSubmitted"],r["S"],r["F"],r["SF"],r["tier"],r["T"],r["R"],r["DD"],r["margin"],r["pnl"],r["selfCorr"],round(r["F_T125"],2),round(r["F_T030"],2),round(r["T_drag"],2)])

# ---- 图1: S vs F 散点, 颜色=Turnover 档 ----
def tcolor(t):
    return "green" if t<0.15 else "orange" if t<0.4 else "red"
fig,ax=plt.subplots(figsize=(9,7))
for r in rows:
    ax.scatter(r["S"],r["F"],c=tcolor(r["T"]),s=60,edgecolor="k",zorder=3)
    ax.annotate(r["id"],(r["S"],r["F"]),fontsize=6,xytext=(2,2),textcoords="offset points")
ax.axhline(2.0,color="gray",ls=":",label="F=2.0 Excellent")
ax.axvline(2.5,color="gray",ls=":",label="S=2.5 Spectacular")
ax.plot([1,3.2],[3,1.2],"k--",label="S+F=4.0")
ax.set_xlabel("Sharpe (S)"); ax.set_ylabel("Fitness (F)")
ax.set_title("31 Alphas: Sharpe vs Fitness (real IS), color=Turnover")
ax.legend(fontsize=8)
from matplotlib.lines import Line2D
leg=[Line2D([0],[0],marker='o',color='w',markerfacecolor='green',markersize=8,label='T<0.15'),
     Line2D([0],[0],marker='o',color='w',markerfacecolor='orange',markersize=8,label='0.15<=T<0.4'),
     Line2D([0],[0],marker='o',color='w',markerfacecolor='red',markersize=8,label='T>=0.4')]
ax.add_artist(ax.legend(handles=leg,loc='upper left',fontsize=8,title='Turnover'))
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_real_scores.png"),dpi=110); plt.close(fig)

# ---- 图2: Turnover vs Fitness, 高 T 拖累标注 ----
fig,ax=plt.subplots(figsize=(9,6))
for r in rows:
    ax.scatter(r["T"],r["F"],c=tcolor(r["T"]),s=60,edgecolor="k",zorder=3)
    if r["T_drag"]>0.3:
        ax.annotate(r["id"],(r["T"],r["F"]),fontsize=7,xytext=(3,3),textcoords="offset points",color="red")
ax.set_xlabel("Turnover (T)"); ax.set_ylabel("Fitness (F)")
ax.set_title("Fitness vs Turnover: red labels = high-T drag (F would rise if T lower)")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_turnover.png"),dpi=110); plt.close(fig)

# ---- 图3: Drawdown 排序条形 ----
rs=sorted(rows,key=lambda x:x["DD"])
fig,ax=plt.subplots(figsize=(9,8))
cols=["red" if r["DD"]>0.10 else "steelblue" for r in rs]
ax.barh([r["id"] for r in rs],[r["DD"] for r in rs],color=cols)
ax.axvline(0.10,color="gray",ls="--",label="10% risk line")
ax.set_xlabel("Max Drawdown"); ax.set_title("Drawdown by Alpha (red = >10%)")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_drawdown.png"),dpi=110); plt.close(fig)

# ---- 图4: CLAUDE vs API 校验 ----
fig,axs=plt.subplots(1,2,figsize=(11,5))
xs=[r["S"] for r in rows]; ys=[CLAUDE[r["id"]][0] for r in rows]
axs[0].scatter(xs,ys,color="steelblue"); axs[0].plot([1,3.1],[1,3.1],"k--"); axs[0].set_xlabel("API S"); axs[0].set_ylabel("CLAUDE S"); axs[0].set_title("Sharpe: API vs CLAUDE.md")
xs=[r["F"] for r in rows]; ys=[CLAUDE[r["id"]][1] for r in rows]
axs[1].scatter(xs,ys,color="darkgreen"); axs[1].plot([1,2],[1,2],"k--"); axs[1].set_xlabel("API F"); axs[1].set_ylabel("CLAUDE F"); axs[1].set_title("Fitness: API vs CLAUDE.md")
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_verify.png"),dpi=110); plt.close(fig)

# ---- 图5: selfCorrelation 排序条形 (核心发现) ----
rs=sorted(rows,key=lambda x:-x["selfCorr"])
fig,ax=plt.subplots(figsize=(9,8))
cols=["red" if r["selfCorr"]>=0.7 else "steelblue" for r in rs]
ax.barh([r["id"] for r in rs],[r["selfCorr"] for r in rs],color=cols)
ax.axvline(0.7,color="gray",ls="--",label="0.7 rejection/dilution threshold")
ax.set_xlabel("Self-Correlation (max vs submitted set)")
ax.set_title("Self-Correlation by Alpha (red = >=0.7, redundant)")
ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT,"fig_selfcorr.png"),dpi=110); plt.close(fig)

n_ge_07=sum(1 for r in rows if r["selfCorr"]>=0.7)
print(f"\n=== Self-Correlation ===\nmean={st.mean([r['selfCorr'] for r in rows]):.3f}  #>=0.7: {n_ge_07}/31  #>=0.9: {sum(1 for r in rows if r['selfCorr']>=0.9)}/31")

print("\nDone. CSV + 5 figs in", OUT)
