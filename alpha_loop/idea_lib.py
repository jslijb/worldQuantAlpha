from __future__ import annotations

from dataclasses import dataclass, field

from . import config


@dataclass
class Idea:
    idea_id: str
    mechanism: str
    market_scope: list[str]
    roles: list[dict]
    shapes: list[str] = field(default_factory=lambda: list("ABCDEFGHI"))
    kind: str = "other"


def _r(role: str, typ: str, semantic: str) -> dict:
    return {"role": role, "type": typ, "semantic": semantic}


IDEAS: list[Idea] = [
    Idea("anl_revision_vs_dispersion", "分析师上修强度相对预期分歧越高，后续定价越可能追上修", ["GLB", "EUR", "USA"],
         [_r("a", "revision", "estimate revision change upward"), _r("b", "dispersion", "estimate dispersion standard deviation")], kind="analyst"),
    Idea("anl_target_gap", "目标价与现价的差距越大，估值错配修复空间越大", ["GLB", "EUR", "JPN"],
         [_r("a", "level", "target price mean"), _r("b", "level", "close price level")], kind="analyst"),
    Idea("anl_eps_revision_momentum", "EPS 上修相对价格反应不足时存在漂移", ["GLB", "EUR", "USA"],
         [_r("a", "revision", "eps estimate revision change"), _r("b", "level", "price level")], kind="analyst"),
    Idea("anl_coverage_attention", "覆盖人数变化代表关注度迁移，关注度上升伴随预期修正", ["GLB", "EUR"],
         [_r("a", "level", "number of analysts coverage count"), _r("b", "revision", "consensus estimate revision")], kind="analyst"),
    Idea("anl_dispersion_shift", "预期分歧度变化比分歧度水平更能预示重定价", ["GLB", "EUR", "USA"],
         [_r("a", "dispersion", "estimate dispersion deviation"), _r("b", "level", "price level")], kind="analyst"),
    Idea("fnd_cashflow_yield", "经营现金流相对企业价值越高，现金创造能力被低估", ["GLB", "EUR", "USA"],
         [_r("a", "level", "cash flow from operations"), _r("b", "level", "enterprise value")], kind="fundamental"),
    Idea("fnd_gross_margin_quality", "毛利相对总资产体现资产盈利效率", ["GLB", "EUR", "JPN"],
         [_r("a", "level", "gross profit"), _r("b", "level", "total assets")], kind="fundamental"),
    Idea("fnd_inventory_build", "存货相对营收抬升预示需求转弱", ["GLB", "USA"],
         [_r("a", "level", "inventory total"), _r("b", "level", "revenue sales")], kind="fundamental"),
    Idea("fnd_receivable_quality", "应收账款相对营收扩张预示收入质量下降", ["GLB", "EUR"],
         [_r("a", "level", "accounts receivable"), _r("b", "level", "revenue sales")], kind="fundamental"),
    Idea("fnd_leverage_risk", "净负债相对 EBITDA 越高，利率敏感度越强", ["GLB", "EUR", "USA"],
         [_r("a", "level", "total debt net debt"), _r("b", "level", "ebitda earnings")], kind="fundamental"),
    Idea("fnd_capex_intensity", "资本开支相对折旧越高，扩张周期强度越大", ["GLB", "JPN"],
         [_r("a", "level", "capital expenditure"), _r("b", "level", "depreciation amortization")], kind="fundamental"),
    Idea("fnd_book_yield", "账面价值相对市值越高，价值折价越明显", ["GLB", "EUR", "JPN"],
         [_r("a", "level", "book value equity"), _r("b", "level", "market capitalization")], kind="fundamental"),
    Idea("opt_iv_rv_premium", "隐含波动高于已实现波动时，波动率风险溢价被高估", ["USA", "GLB", "EUR"],
         [_r("a", "volatility", "implied volatility"), _r("b", "volatility", "realized volatility")], kind="option"),
    Idea("opt_skew_put_call", "看跌看涨偏斜反映尾部风险定价", ["USA", "GLB"],
         [_r("a", "volatility", "put implied volatility skew"), _r("b", "volatility", "call implied volatility")], kind="option"),
    Idea("opt_volume_ratio", "期权成交量相对股票成交量放大预示知情交易", ["USA", "GLB"],
         [_r("a", "flow", "option volume"), _r("b", "flow", "stock volume turnover")], kind="option"),
    Idea("opt_term_slope", "波动率期限结构斜率变化反映事件预期", ["USA", "EUR"],
         [_r("a", "volatility", "implied volatility long maturity"), _r("b", "volatility", "implied volatility short maturity")], kind="option"),
    Idea("evt_news_tone_shift", "新闻语气改善相对价格滞后，存在情绪修复", ["GLB", "USA", "EUR"],
         [_r("a", "sentiment", "news sentiment score tone"), _r("b", "level", "price level")], kind="event"),
    Idea("evt_social_attention", "社交关注度上升而价格未动，后续波动加大", ["USA", "GLB"],
         [_r("a", "sentiment", "social media attention buzz"), _r("b", "flow", "volume turnover")], kind="event"),
    Idea("evt_earnings_drift", "盈利惊喜后的价格漂移未走完", ["GLB", "USA", "EUR"],
         [_r("a", "level", "earnings surprise actual estimate"), _r("b", "level", "price level")], kind="event"),
    Idea("pv_volume_price_div", "放量而价格不涨，筹码换手后价格压力显现", ["GLB", "ASI", "JPN"],
         [_r("a", "flow", "volume"), _r("b", "level", "close price")], kind="price_volume"),
    Idea("pv_range_pressure", "日内振幅相对收盘价抬升，波动压力积聚", ["GLB", "ASI"],
         [_r("a", "volatility", "high low range"), _r("b", "level", "close price")], kind="price_volume"),
    Idea("pv_illiquidity", "成交额相对收益变动越弱，流动性溢价越高", ["GLB", "ASI"],
         [_r("a", "flow", "turnover value amount"), _r("b", "volatility", "return volatility")], kind="price_volume"),
    Idea("pv_overnight_intraday", "隔夜与日内收益差反映资金结构差异", ["GLB", "USA"],
         [_r("a", "level", "open price"), _r("b", "level", "close price")], kind="price_volume"),
]

PV_LIMIT = 0.30


def by_id(idea_id: str) -> Idea | None:
    return next((i for i in IDEAS if i.idea_id == idea_id), None)


def candidates(market: str, used_datasets: set[str] | None = None) -> list[Idea]:
    used_datasets = used_datasets or set()
    out = [i for i in IDEAS if market in i.market_scope]
    if market == "USA" and config.USA_UNUSED_DATASET_ONLY:
        out = [i for i in out if i.kind != "price_volume"]
    return out


def pv_share(idea_ids: list[str]) -> float:
    if not idea_ids:
        return 0.0
    kinds = [(by_id(i).kind if by_id(i) else "other") for i in idea_ids]
    return sum(1 for k in kinds if k == "price_volume") / len(kinds)


if __name__ == "__main__":
    print("IDEAS", len(IDEAS))
    bad = [i.idea_id for i in IDEAS if not i.mechanism.strip()]
    print("EMPTY_MECHANISM", bad)
    print("PV_SHARE", round(pv_share([i.idea_id for i in IDEAS]), 3))