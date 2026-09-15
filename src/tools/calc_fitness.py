# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
"""反推 Fitness 精确公式"""
import sys, io, json, os, math
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 已知数据点 (Sharpe, Returns, Turnover, Drawdown, Fitness)
data = [
    # rank(close)
    {"S": 0.83, "R": 0.3481, "T": 0.0108, "D": 0.6577, "F": 1.39},
    # cf_ev_zscore decay=3
    {"S": 1.42, "R": 0.0795, "T": 0.187, "D": 0.0809, "F": 0.93},
    # cf_ev_zscore decay=4
    {"S": 1.37, "R": 0.0, "T": 0.157, "D": 0.0, "F": 1.00},
    # cf_ev_zscore decay=2
    {"S": 1.50, "R": 0.0, "T": 0.217, "D": 0.0, "F": 0.93},
    # liabilities/assets (from earlier)
    {"S": 1.57, "R": 0.0, "T": 0.016, "D": 0.0, "F": 1.45},
]

print("=== 已知数据点 ===")
for d in data:
    print(f"  S={d['S']:.2f} R={d['R']:.4f} T={d['T']:.4f} D={d['D']:.4f} -> F={d['F']:.2f}")

# 尝试各种公式
print("\n=== 尝试公式 ===")
formulas = [
    ("S * sqrt(R) / max(T, 0.125)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / max(d['T'], 0.125)),
    ("S * sqrt(R) * sqrt(1-D)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) * math.sqrt(1 - d['D'])),
    ("S * R / max(T, 0.125)", lambda d: d['S'] * d['R'] / max(d['T'], 0.125)),
    ("S * sqrt(R) / T", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / d['T']),
    ("S * R * (1-D) / T", lambda d: d['S'] * d['R'] * (1 - d['D']) / d['T']),
    ("S * sqrt(R * (1-D)) / max(T, 0.125)", lambda d: d['S'] * math.sqrt(max(d['R'] * (1 - d['D']), 0.001)) / max(d['T'], 0.125)),
    ("S * sqrt(R) / max(T, 0.01)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / max(d['T'], 0.01)),
    ("S * sqrt(R) / max(T, 0.05)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / max(d['T'], 0.05)),
    ("S * sqrt(R) / max(T, 0.1)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / max(d['T'], 0.1)),
    ("S * sqrt(R) / max(T, 0.15)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / max(d['T'], 0.15)),
    ("S * sqrt(R) / max(T, 0.2)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) / max(d['T'], 0.2)),
    ("S * R / max(T, 0.125) * sqrt(1-D)", lambda d: d['S'] * d['R'] / max(d['T'], 0.125) * math.sqrt(1 - d['D'])),
    ("S * sqrt(R) * (1-D) / max(T, 0.125)", lambda d: d['S'] * math.sqrt(max(d['R'], 0.001)) * (1 - d['D']) / max(d['T'], 0.125)),
]

for name, fn in formulas:
    errors = []
    for d in data:
        predicted = fn(d)
        actual = d['F']
        error = abs(predicted - actual)
        errors.append(error)
    avg_error = sum(errors) / len(errors)
    max_error = max(errors)
    fits = [fn(d) for d in data]
    print(f"\n  {name}:")
    predicted_str = ', '.join(['%.2f' % f for f in fits])
    actual_str = ', '.join(['%.2f' % d['F'] for d in data])
    print(f"    预测: [{predicted_str}]")
    print(f"    实际: [{actual_str}]")
    print(f"    平均误差: {avg_error:.4f}, 最大误差: {max_error:.4f}")
