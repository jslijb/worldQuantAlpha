# -*- coding: utf-8 -*-
"""2026-09-19 账目实测：台账总数 / 美东每日计数 / 欠账（禁止凭印象）"""
import csv, datetime, pathlib
from collections import Counter

LEDGER = pathlib.Path(r"D:\Python\worldquant\data\alpha_quality_analysis\SUBMITTED_LEDGER.csv")
rows = list(csv.reader(LEDGER.open(encoding="utf-8-sig")))
header, data = rows[0], [r for r in rows[1:] if len(r) >= 9 and r[0].strip()]
print("header:", header)
print("total_rows:", len(data))
ids = [r[0] for r in data]
print("unique_ids:", len(set(ids)))

# dateSubmitted 是 row[8]，美东 -04:00
per_day = Counter()
for r in data:
    ds = r[8].strip()
    if not ds:
        continue
    day = ds[:10]
    per_day[day] += 1

print("\n== recent days (US Eastern) ==")
for day in sorted(per_day)[-8:]:
    print(day, per_day[day])

today = "2026-09-19"
today_n = per_day.get(today, 0)
print("\ntoday(09-19 ET):", today_n)

# 欠账：从 09-13 起按每日目标 5 累计缺口（下限口径，与自动化提醒一致）
START = "2026-09-13"
debt = 0
print("\n== debt since", START, "(target 5/day) ==")
d = datetime.date(2026, 9, 13)
end = datetime.date(2026, 9, 19)
while d <= end:
    k = d.isoformat()
    n = per_day.get(k, 0)
    gap = max(0, 5 - n)
    debt += gap
    print(k, "submitted", n, "gap", gap)
    d += datetime.timedelta(days=1)
print("total_debt:", debt, "| today target = 5 + prior debt =", 5 + debt - max(0, 5 - today_n))
