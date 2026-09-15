# -*- coding: utf-8 -*-
"""重组 31 个 Alpha 质量报告：Markdown + HTML（含降 Turnover 改写候选与下线清单）"""
import csv, os, statistics as st

OUT = os.path.dirname(os.path.abspath(__file__))
CSV = os.path.join(OUT, "summary_real.csv")

rows = []
with open(CSV, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        r["S"]=float(r["S"]); r["F"]=float(r["F"]); r["S+F"]=float(r["S+F"])
        r["T"]=float(r["T"]); r["R"]=float(r["R"]); r["DD"]=float(r["DD"])
        r["selfCorr"]=float(r["selfCorr"]); r["F_if_T125"]=float(r["F_if_T125"])
        rows.append(r)

# ---- 整体统计 ----
S=[r["S"] for r in rows]; F=[r["F"] for r in rows]; T=[r["T"] for r in rows]
R=[r["R"] for r in rows]; DD=[r["DD"] for r in rows]; SC=[r["selfCorr"] for r in rows]
def tier_of(v):
    if v>=4.0: return "A"
    if v>=3.4: return "B"
    if v>=3.0: return "C"
    return "D"
from collections import Counter
tc = Counter(tier_of(r["S+F"]) for r in rows)
n=len(rows)
ge4 = sum(1 for r in rows if r["S+F"]>=4.0)
lt34 = sum(1 for r in rows if r["S+F"]<3.4)
ge07 = sum(1 for x in SC if x>=0.7)
ge09 = sum(1 for x in SC if x>=0.9)

# ---- 优化方案数据 ----
# Tract A: 降 Turnover 改写候选（6 个高 T）
high_T = [
    ("e79kPeEM", "gr(liabcurr/assets)+gr(ts_av_diff(cf/ev,60))+gr(-ts_rank(close,5))", 0.57, 1.79, 3.82,
     "gr(liabcurr/assets)+gr(ts_av_diff(cf/ev,60))+gr(-ts_rank(close,20))"),
    ("kqjpepz8", "gr(liabcurr/assets)+gr(-ts_rank(close,5))", 0.663, 1.42, 3.28,
     "gr(liabcurr/assets)+gr(-ts_rank(close,20))"),
    ("N1QxNQK7", "gr(liabcurr/cap)+gr(-ts_rank(close,5))", 0.657, 1.17, 2.67,
     "gr(liabcurr/cap)+gr(-ts_rank(close,20))"),
    ("9qX3M2mq", "gr(liabcurr/assets)+gr(-ts_rank(close,10))", 0.528, 1.45, 2.97,
     "gr(liabcurr/assets)+gr(-ts_rank(close,20))"),
    ("qMW92Az2", "gr(liabcurr/cap)+gr(ts_av_diff(cf/ev,60))+gr(-ts_rank(close,10))", 0.464, 1.60, 3.08,
     "gr(liabcurr/cap)+gr(ts_av_diff(cf/ev,60))+gr(-ts_rank(close,20))"),
    ("1YwRK1wW", "gr(liabcurr/assets)+gr(-ts_rank(close,20))", 0.411, 1.31, 2.38,
     "gr(liabcurr/assets)+gr(-decay(ts_rank(close,20),5))  // 加 decay 平滑降低 T"),
]

# Tract B: 建议主动下线（最弱 + 冗余副本）
decom = [
    ("9qX8Nr6r", "D", 2.75, "S=1.26 全队最低(刚过1.25线) + DD=26.4% 全队最高，极脆弱"),
    ("QP3XalpK", "D", 2.34, "S+F 全队最低(2.34)，S=1.27 刚过线，无保留价值"),
    ("wpjoxbbd", "D", 2.37, "F=1.00 恰好踩线，S=1.37 弱"),
    ("RR79x16n", "D", 2.63, "liabcurr/assets 单因子弱版，被更强变体覆盖"),
    ("RRVLeabj", "D", 2.70, "rev/assets + -ts_rank(returns,20) 组合弱且高冗余"),
    ("akLqqmm6", "D", 2.94, "cash/assets+close,5+close-vol 组合弱且高冗余"),
    ("wpYgReRx", "D", 2.95, "rev/assets + -ts_av_diff(close,20) 弱组合"),
    ("E5v15JPJ", "D", 2.81, "liabcurr + -ts_corr(close,vol) 弱组合"),
    ("rKj7w0Z1", "C", 2.84, "cf/ev 家族副本(selfCorr=0.967 近重复)，C档仍建议下线"),
    ("vRjG1Jzw", "D", 3.06, "1YwKML56 的 delay=1 版(selfCorr=0.884 近重复)→ 留 1YwKML56"),
]

# 保留代表（去重后每簇最高 S+F）
keep = [
    ("e79kPeEM", "4.81", "liabcurr+close5 簇代表，且将出降T变体"),
    ("1YwKML56", "3.96", "cf/ev delay=0 代表(留，下线 vRjG1Jzw)"),
    ("le8ddYbe", "4.28", "三因子组合代表(留，下线 qMW/MP1 冗余)"),
    ("6XrbGx1L", "4.01", "returns,20 超级家族代表"),
    ("883OXpJl", "4.26", "fundamental6 组合代表"),
    ("E5vkQ76G", "4.11", "accrued_liab 组合代表"),
]

# ---- Markdown ----
def tier_badge(t): return {"A":"**A**","B":"B","C":"C","D":"D"}[t]

md = []
md.append("# WorldQuant Brain Alpha 质量体检报告（31 个 ACTIVE）\n")
md.append(f"> 数据来源：平台 `GET /alphas/{{id}}` 真实 IS 指标（非手工估算），拉取于 2026-09-08。\n")
md.append("> 关键约束：**已提交的 Alpha 无法原地修改**，表达式一旦 ACTIVE 即冻结。\n")
md.append("> 因此\"提升质量\"只有两条路：① 提交改进版**新变体**；② **主动下线(decommission)** 冗余/脆弱因子止损边际权重。\n")

md.append("## 一、指标说明（你问的 Return / Sharpe / IR / Fitness）\n")
md.append("| 指标 | 平台字段 | 是否在本报告 | 说明 |")
md.append("|---|---|---|---|")
md.append("| Return 年度化收益 | `is.returns` | ✅ 包含 | Fitness 公式中的 R |")
md.append("| Sharpe | `is.sharpe` | ✅ 包含 | 风险调整收益主线指标 |")
md.append("| Fitness | `is.fitness` | ✅ 包含 | F = S·√(\|R\|/max(T,0.125)) |")
md.append("| Turnover | `is.turnover` | ✅ 包含 | 换手率，Fitness 头号杀手 |")
md.append("| Drawdown | `is.drawdown` | ✅ 包含 | 最大回撤，脆弱度 |")
md.append("| selfCorrelation | `is.selfCorrelation` | ✅ 包含 | 与本集合最高相关 alpha 的相关度 |")
md.append("| **IR (Information Ratio)** | — | ❌ **平台不返回** | WQ Brain 用 Sharpe 代替，无独立 IR 字段；如需可派生近似 |")
md.append("\n**关于 `selfCorrelation >= 0.7`（你问的 \"red>=0.7\"）：**\n")
md.append("- 定义：该 alpha 与你**已提交的全部 ACTIVE alpha 中相关性最高的那个**的相关度。")
md.append("- `0.7` 是 WQ Alpha Streams 的**去冗余/权重稀释阈值**：两个 alpha 相关性过高→平台认为信号重复→**稀释权重**（少分资金）。`>=0.9` 基本是近似复制品。")
md.append(f"- 现状：**{ge07}/31 ≥0.7，{ge09}/31 ≥0.9**。这直接解释了\"堆了 31 个 Rank 仍卡 911\"——数量堆不出多样性，平台按相关性稀释 Weight。\n")

md.append("## 二、整体质量水位\n")
md.append(f"- 样本量：**{n}** 个 ACTIVE")
md.append(f"- Sharpe：min {min(S):.2f} / max {max(S):.2f} / 均值 **{st.mean(S):.2f}**")
md.append(f"- Fitness：min {min(F):.2f} / max {max(F):.2f} / 均值 **{st.mean(F):.2f}** —— **全员 <2.0**（最高 le8ddYbe 1.87），无 Excellent 档")
md.append(f"- Turnover：min {min(T):.3f} / max {max(T):.3f} / 均值 {st.mean(T):.3f}")
md.append(f"- Drawdown：min {min(DD):.3f} / max {max(DD):.3f} / 均值 {st.mean(DD):.3f}")
md.append(f"- selfCorr：min {min(SC):.3f} / max {max(SC):.3f} / 均值 **{st.mean(SC):.3f}**")
md.append(f"- 质量分层：**A(≥4.0) {tc['A']} 个 / B 10 个 / C 5 个 / D(<3.0) 10 个**")
md.append(f"- 达标率(S+F≥4.0)：**{ge4}/{n}**；低于 3.4：**{lt34}/{n}**（按你 9/7 红线这 {lt34} 个本不该提交）\n")

md.append("## 三、三个最硬伤\n")
md.append("1. **同质化（根因级）**：selfCorr 均值 0.673，14/31 ≥0.7。组合内部高度冗余→平台稀释权重→Rank 卡住。")
md.append("2. **Turnover 拖死 Fitness**：6 个 alpha T≥0.4 把 F 压在 1.2–1.8；把 T 压到 0.125 后 F 能翻到 2.4–3.8（见 Tract A）。")
md.append("3. **回撤与边界脆弱**：9qX8Nr6r DD=26%、S=1.26 全队最弱；N1QxNQK7 DD=18%；多个踩线（wpjoxbbd F=1.0、QP3XalpK S=1.27）。\n")

md.append("## 四、31 个 Alpha 质量总表（按 S+F 降序）\n")
md.append("| ID | S | F | S+F | 档 | T | R | DD | selfCorr | 标记 |")
md.append("|---|---|---|---|---|---|---|---|---|---|")
for r in sorted(rows, key=lambda x:-x["S+F"]):
    flags=[]
    if r["selfCorr"]>=0.7: flags.append("冗余≥0.7")
    if r["T"]>=0.4: flags.append("高T")
    if r["DD"]>=0.15: flags.append("高DD")
    if r["S+F"]<3.0: flags.append("D档")
    if r["S"]<1.3: flags.append("S临界")
    md.append(f"| {r['id']} | {r['S']:.2f} | {r['F']:.2f} | {r['S+F']:.2f} | {tier_badge(r['tier'][0])} | {r['T']:.3f} | {r['R']:.3f} | {r['DD']:.3f} | {r['selfCorr']:.3f} | {','.join(flags)} |")

md.append("\n## 五、优化方案\n")
md.append("### Tract A — 降 Turnover 改写（直接提 Fitness，提交新变体）\n")
md.append("机制：`ts_rank(close,N)` 窗口越短 T 越高→换长窗口(20)或加 decay 平滑。下表为**待模拟候选**（F_if_T125 是该 alpha 把 T 压到 0.125 的理论上限，现实目标取当前 F 与上限之间）。\n")
md.append("| alpha | 当前表达式 | T | F | F上限(T→0.125) | 候选降T改写 |")
md.append("|---|---|---|---|---|---|")
for aid,expr,t,f,ceil,cand in high_T:
    md.append(f"| {aid} | `{expr}` | {t:.3f} | {f:.2f} | {ceil:.2f} | `{cand}` |")

md.append("\n### Tract B — 主动下线清单（止损边际权重）\n")
md.append("原则：D 档弱因子 + 高 selfCorr 副本，每簇只留最高 S+F 代表（见 Tract C）。\n")
md.append("| alpha | 档 | S+F | 下线理由 |")
md.append("|---|---|---|---|")
for aid,t,sf,why in decom:
    md.append(f"| {aid} | {t} | {sf:.2f} | {why} |")

md.append("\n### Tract C — 去重后保留代表（每簇最高 S+F）\n")
md.append("| alpha | S+F | 角色 |")
md.append("|---|---|---|")
for aid,sf,role in keep:
    md.append(f"| {aid} | {sf} | {role} |")

md.append("\n### Tract D — 新信号族方向（必须换骨架，否则继续撞 0.7 墙）\n")
md.append("- 现有 31 个挤在 `liabcurr/assets`、`cf/ev`、`ts_rank(close/returns,N)`、`ts_corr(close,vol)` 几条骨架上。")
md.append("- 新挖应引入**未复用数据集/算子**：如 estimate/recommend/blockholder 数据集、ts_min_ts_max 区间类算子、`group_zscore` 替代 `group_rank`（降 T）、多区域数据集组合。")
md.append("- 提交前先本地算与现有集合的近似 selfCorr，避免再交高冗余副本。\n")

md.append("## 六、下一步（需你确认后执行）\n")
md.append("1. 批量**模拟** Tract A 的 6 个降T候选，看 IS 是否如预期（S 不降、T 降、F 涨）。")
md.append("2. 对模拟达标的候选**提交为新 alpha**（不覆盖原 alpha）。")
md.append("3. 在网页后台对 Tract B 清单**主动 decommission**。")
md.append("4. 按 Tract D 方向新挖 2–3 个低相关信号族 alpha。")
md.append("\n> 注：OS / train / test / prod 在 TUTORIAL 权限下均为 null/PENDING，平台 API 不返回样本外数值；跨 alpha 完整两两相关矩阵仅在网页 UI 暴露 Top5。OS 衰减补全需你网页后台人工核对或等权限提升。\n")

# ---- HTML ----
def esc(s): return str(s).replace("|","&#124;").replace("<","&lt;").replace(">","&gt;")
tier_color = {"A":"#1a7f37","B":"#3b82f6","C":"#d97706","D":"#dc2626"}
rows_sorted = sorted(rows, key=lambda x:-x["S+F"])
trs = ""
for r in rows_sorted:
    flags=[]
    if r["selfCorr"]>=0.7: flags.append('<span style="color:#dc2626">冗余≥0.7</span>')
    if r["T"]>=0.4: flags.append('<span style="color:#d97706">高T</span>')
    if r["DD"]>=0.15: flags.append('<span style="color:#dc2626">高DD</span>')
    if r["S+F"]<3.0: flags.append('<span style="color:#dc2626">D档</span>')
    if r["S"]<1.3: flags.append('<span style="color:#d97706">S临界</span>')
    trs += f"""<tr><td>{r['id']}</td><td>{r['S']:.2f}</td><td>{r['F']:.2f}</td>
    <td>{r['S+F']:.2f}</td><td style="color:{tier_color[r['tier'][0]]};font-weight:700">{r['tier'][0]}</td>
    <td>{r['T']:.3f}</td><td>{r['R']:.3f}</td><td>{r['DD']:.3f}</td><td>{r['selfCorr']:.3f}</td>
    <td>{' '.join(flags)}</td></tr>\n"""

tA = "".join(f"""<tr><td>{a}</td><td><code>{esc(e)}</code></td><td>{t:.3f}</td><td>{f:.2f}</td>
<td>{c:.2f}</td><td><code>{esc(k)}</code></td></tr>""" for a,e,t,f,c,k in high_T)
tB = "".join(f"<tr><td>{a}</td><td>{t}</td><td>{sf:.2f}</td><td>{esc(why)}</td></tr>" for a,t,sf,why in decom)
tC = "".join(f"<tr><td>{a}</td><td>{sf}</td><td>{esc(role)}</td></tr>" for a,sf,role in keep)

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Alpha 质量体检报告</title>
<style>
body{{font-family:-apple-system,'Microsoft YaHei',sans-serif;max-width:1080px;margin:24px auto;padding:0 16px;color:#1a1a1a;line-height:1.6}}
h1{{font-size:24px;border-bottom:3px solid #3b82f6;padding-bottom:8px}}
h2{{font-size:19px;margin-top:32px;color:#1f2937;border-left:4px solid #3b82f6;padding-left:10px}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}}
th,td{{border:1px solid #d1d5db;padding:6px 8px;text-align:center}}
th{{background:#f3f4f6;font-weight:700}}
tr:nth-child(even){{background:#fafafa}}
code{{background:#eef2ff;padding:1px 5px;border-radius:4px;font-size:12px;color:#3730a3}}
.note{{background:#fffbeb;border:1px solid #fde68a;padding:10px 14px;border-radius:8px;font-size:13px}}
.kpi{{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}}
.kpi div{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;flex:1;min-width:130px}}
.kpi b{{font-size:20px;color:#3b82f6;display:block}}
img{{max-width:100%;border:1px solid #e5e7eb;border-radius:8px;margin:8px 0}}
</style></head><body>
<h1>WorldQuant Brain Alpha 质量体检报告</h1>
<p class="note">数据来源：平台 <code>GET /alphas/{{id}}</code> 真实 IS 指标，拉取于 2026-09-08。
<b>关键约束：已提交 Alpha 无法原地修改</b>，只能提交改进版新变体或主动下线(decommission)。</p>

<h2>一、指标说明（Return / Sharpe / IR / Fitness）</h2>
<table><tr><th>指标</th><th>平台字段</th><th>本报告</th><th>说明</th></tr>
<tr><td>Return 年度化收益</td><td>is.returns</td><td>✅</td><td>Fitness 公式中的 R</td></tr>
<tr><td>Sharpe</td><td>is.sharpe</td><td>✅</td><td>风险调整收益主线</td></tr>
<tr><td>Fitness</td><td>is.fitness</td><td>✅</td><td>F=S·√(|R|/max(T,0.125))</td></tr>
<tr><td>Turnover</td><td>is.turnover</td><td>✅</td><td>Fitness 头号杀手</td></tr>
<tr><td>Drawdown</td><td>is.drawdown</td><td>✅</td><td>最大回撤</td></tr>
<tr><td>selfCorrelation</td><td>is.selfCorrelation</td><td>✅</td><td>与本集合最高相关 alpha 的相关度</td></tr>
<tr><td><b>IR</b></td><td>—</td><td>❌ 平台不返回</td><td>WQ 用 Sharpe 代替，无独立 IR</td></tr></table>
<p><b>selfCorrelation ≥ 0.7 是啥意思？</b> 该 alpha 与你已提交 ACTIVE alpha 中相关性最高的那个的相关度。
0.7 是 WQ 去冗余/权重稀释阈值：相关性过高→平台认为信号重复→稀释权重；≥0.9 基本是复制品。
现状 <b>{ge07}/31 ≥0.7，{ge09}/31 ≥0.9</b>——这就是堆了 31 个 Rank 仍卡 911 的根因。</p>

<h2>二、整体质量水位</h2>
<div class="kpi">
<div><b>{n}</b>ACTIVE 因子</div>
<div><b>{st.mean(S):.2f}</b>Sharpe 均值</div>
<div><b>{st.mean(F):.2f}</b>Fitness 均值(全员&lt;2.0)</div>
<div><b>{st.mean(SC):.3f}</b>selfCorr 均值</div>
<div><b>{ge4}/{n}</b>S+F≥4.0 达标</div>
<div><b>{lt34}/{n}</b>低于 3.4</div>
</div>

<h2>三、三个最硬伤</h2>
<ol>
<li><b>同质化（根因级）</b>：selfCorr 均值 0.673，14/31 ≥0.7，组合内部高度冗余→平台稀释权重→Rank 卡住。</li>
<li><b>Turnover 拖死 Fitness</b>：6 个 alpha T≥0.4 把 F 压在 1.2–1.8；T 压到 0.125 后 F 能翻到 2.4–3.8。</li>
<li><b>回撤与边界脆弱</b>：9qX8Nr6r DD=26%、S=1.26 全队最弱；N1QxNQK7 DD=18%；多个踩线。</li>
</ol>

<h2>四、可视化</h2>
<img src="fig_selfcorr.png" alt="selfCorr">
<img src="fig_real_scores.png" alt="scores">
<img src="fig_turnover.png" alt="turnover">
<img src="fig_drawdown.png" alt="drawdown">

<h2>五、31 个 Alpha 质量总表（按 S+F 降序）</h2>
<table><tr><th>ID</th><th>S</th><th>F</th><th>S+F</th><th>档</th><th>T</th><th>R</th><th>DD</th><th>selfCorr</th><th>标记</th></tr>
{trs}</table>

<h2>六、优化方案</h2>
<h3>Tract A — 降 Turnover 改写（提交新变体）</h3>
<table><tr><th>alpha</th><th>当前表达式</th><th>T</th><th>F</th><th>F上限(T→0.125)</th><th>候选降T改写</th></tr>
{tA}</table>
<h3>Tract B — 主动下线清单</h3>
<table><tr><th>alpha</th><th>档</th><th>S+F</th><th>下线理由</th></tr>
{tB}</table>
<h3>Tract C — 去重后保留代表</h3>
<table><tr><th>alpha</th><th>S+F</th><th>角色</th></tr>
{tC}</table>
<h3>Tract D — 新信号族方向</h3>
<p>现有 31 个挤在 liabcurr/assets、cf/ev、ts_rank(close/returns,N)、ts_corr(close,vol) 几条骨架。
新挖应引入未复用数据集/算子（estimate/recommend/blockholder、ts_min_ts_max 区间类、group_zscore 替代 group_rank 降T、多区域组合），提交前先本地估 selfCorr 避免再交高冗余副本。</p>

<h2>七、下一步（需确认后执行）</h2>
<ol>
<li>批量<b>模拟</b> Tract A 的 6 个降T候选，验证 S 不降、T 降、F 涨。</li>
<li>达标候选<b>提交为新 alpha</b>（不覆盖原 alpha）。</li>
<li>网页后台对 Tract B 清单<b>主动 decommission</b>。</li>
<li>按 Tract D 新挖 2–3 个低相关信号族 alpha。</li>
</ol>
<p class="note">注：OS/train/test/prod 在 TUTORIAL 权限下均为 null/PENDING，平台 API 不返回样本外数值；跨 alpha 完整两两相关矩阵仅在网页 UI 暴露 Top5。OS 衰减补全需网页后台人工核对或等权限提升。</p>
</body></html>"""

html_path = os.path.join(OUT, "QUALITY_REPORT.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("HTML written:", html_path)

md_path = os.path.join(OUT, "QUALITY_REPORT.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("\n".join(md))
print("MD written:", md_path)
