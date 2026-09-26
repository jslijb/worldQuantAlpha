# -*- coding: utf-8 -*-
"""对比 09-04 前10截图 与 09-21 前30截图：同一批用户的四列变化。"""
import io, os

OUT = io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '_rank_diff.txt'), 'w', encoding='utf-8')
def say(s=''):
    print(s)
    OUT.write(s + '\n')

# --- 09-04 截图（前 10，存档于 docs/project/目标_排名目标.md） ---
d04 = {
    'FL70603':  (1, 0.90, 52, 14868, 0.83),
    'CS35156':  (2, 0.90, 44, 17490, 0.71),
    'YX42680':  (3, 0.89, 40, 13081, 0.58),
    'ZH97118':  (4, 0.88, 47, 11988, 0.83),
    'CH42645':  (5, 0.84, 38, 10298, 0.47),
    'SJ63724':  (6, 0.84, 36, 16170, 0.74),
    'Ke Wang':  (7, 0.83, 31, 18736, 0.57),
    'JW49109':  (8, 0.83, 53, 12114, 0.90),
    'CW16048':  (9, 0.83, 53, 11010, 0.90),
    'WL77079':  (10, 0.80, 53, 11608, 0.91),
}

# --- 09-21 截图（前 30） ---
d21 = {
    'CS35156': (1, 0.86, 39, 17229, 0.66),
    'YX42680': (2, 0.85, 34, 13077, 0.54),
    'Ke Wang': (3, 0.82, 32, 19467, 0.63),
    'FL70603': (4, 0.81, 48, 13616, 0.83),
    'CH42645': (5, 0.79, 35, 10298, 0.58),
    'MG76588': (6, 0.79, 32, 15417, 0.72),
    'HG77739': (7, 0.77, 32, 12076, 0.72),
    'JW49109': (8, 0.77, 48, 12617, 0.85),
    'CW16048': (9, 0.74, 48, 10943, 0.85),
    'HL19556': (10, 0.73, 48, 11509, 0.86),
    'Leslie Cheung': (11, 0.71, 45, 8077, 0.51),
    'YW70391': (12, 0.71, 26, 9601, 0.49),
    'HL14389': (13, 0.71, 50, 11886, 0.88),
    'BH65499': (14, 0.70, 17, 10495, 0.49),
    'WL77079': (15, 0.69, 48, 11730, 0.88),
    'SJ63724': (16, 0.69, 22, 16170, 0.78),
    'XP53031': (17, 0.69, 20, 12868, 0.74),
    'YL36885': (18, 0.69, 19, 12687, 0.72),
    'YY54474': (19, 0.69, 48, 10356, 0.86),
    'PF72535': (20, 0.69, 19, 10880, 0.65),
    'Shao Fei': (21, 0.69, 8, 21385, 0.51),
    'WW60183': (22, 0.68, 12, 10606, 0.38),
    'LY76923': (23, 0.68, 12, 15103, 0.63),
    'QJ87786': (24, 0.68, 9, 11387, 0.44),
    'XW31386': (25, 0.68, 11, 12011, 0.58),
    'BX12838': (26, 0.67, 50, 10099, 0.87),
    'XW95492': (27, 0.67, 6, 14036, 0.51),
    'TT70501': (28, 0.66, 7, 12604, 0.53),
    'YZ41300': (29, 0.66, 9, 11771, 0.57),
    'CY21614': (30, 0.66, 41, 9718, 0.84),
}

say('=' * 96)
say('一、09-04 前 10 名 —— 16 天后（09-21）逐人变化')
say('=' * 96)
say('%-12s %-13s %-11s %-13s %-9s' % ('user', 'Total', 'Days', 'IS', 'Uniq'))
say('-' * 96)
rows = []
for u, (r4, t4, d4_, i4, q4) in sorted(d04.items(), key=lambda x: x[1][0]):
    if u not in d21:
        say('%-12s %.2f->缺失(Days%d/IS%d/U%.2f)  掉出前30' % (u, t4, d4_, i4, q4))
        rows.append((u, None, None, None, None))
        continue
    r2, t2, d2, i2, q2 = d21[u]
    dt, dd, di, dq = t2 - t4, d2 - d4_, i2 - i4, q2 - q4
    say('%-12s %.2f->%.2f(%+.2f)  %2d->%2d(%+3d)  %5d->%5d(%+6d)  %.2f->%.2f(%+.2f)   rank %d->%d'
        % (u, t4, t2, dt, d4_, d2, dd, i4, i2, di, q4, q2, dq, r4, r2))
    rows.append((u, dt, dd, di, dq))

say('')
say('-' * 96)
say('汇总（9 人可比，ZH97118 掉出前 30）')
say('  Total  下降 %d/9 人   平均 %+.3f' % (sum(1 for r in rows if r[1] is not None and r[1] < 0),
                                        sum(r[1] for r in rows if r[1] is not None) / 9))
say('  Days   下降 %d/9 人   平均 %+.1f   最小 %+d   最大 %+d'
    % (sum(1 for r in rows if r[2] is not None and r[2] < 0),
       sum(r[2] for r in rows if r[2] is not None) / 9,
       min(r[2] for r in rows if r[2] is not None),
       max(r[2] for r in rows if r[2] is not None)))
say('  IS     下降 %d/9 人   平均 %+.0f'
    % (sum(1 for r in rows if r[3] is not None and r[3] < 0),
       sum(r[3] for r in rows if r[3] is not None) / 9))
say('  Uniq   下降 %d/9 人   平均 %+.3f'
    % (sum(1 for r in rows if r[4] is not None and r[4] < 0),
       sum(r[4] for r in rows if r[4] is not None) / 9))

say('')
say('★ IS 一分未动的人（16 天零提交的实锤）：')
for u in d04:
    if u in d21 and d04[u][3] == d21[u][3]:
        say('   %-10s IS 恒为 %d   Days %d->%d (%+d)  Total %.2f->%.2f'
            % (u, d04[u][3], d04[u][2], d21[u][2], d21[u][2] - d04[u][2], d04[u][1], d21[u][1]))

say('')
say('★ Days 数值撞点统计（09-21）：')
from collections import Counter
c = Counter(v[2] for v in d21.values())
for k in sorted(c, reverse=True):
    if c[k] >= 2:
        say('   Days=%d  出现 %d 人' % (k, c[k]))

say('')
say('=' * 96)
say('二、门槛与天花板的变化')
say('=' * 96)
t04_top1 = max(v[1] for v in d04.values())
t04_top10 = min(v[1] for v in d04.values())
t21_top1 = max(v[1] for v in d21.values())
t21_top10 = d21['HL19556'][1]
say('  Total 第 1 名        %.2f  ->  %.2f   (%+.2f)' % (t04_top1, t21_top1, t21_top1 - t04_top1))
say('  Total 第 10 名门槛    %.2f  ->  %.2f   (%+.2f)' % (t04_top10, t21_top10, t21_top10 - t04_top10))
d04_days = [v[2] for v in d04.values()]
d21_top10_days = [d21[k][2] for k in ('CS35156','YX42680','Ke Wang','FL70603','CH42645','MG76588','HG77739','JW49109','CW16048','HL19556')]
say('  前10 Days 中位        %d  ->  %d' % (sorted(d04_days)[5], sorted(d21_top10_days)[5]))
say('  前10 IS  中位      %d  ->  %d' % (sorted(v[3] for v in d04.values())[5],
                                        sorted(d21[k][3] for k in ('CS35156','YX42680','Ke Wang','FL70603','CH42645','MG76588','HG77739','JW49109','CW16048','HL19556'))[5]))

say('')
say('★ 前 10 换人：')
gone = [u for u in d04 if u not in {k for k, v in d21.items() if v[0] <= 10}]
new = [k for k, v in d21.items() if v[0] <= 10 and k not in d04]
say('   09-04 在前 10、今天不在前 10：%s' % (', '.join(gone) if gone else '无'))
say('   今天进前 10 的新面孔：%s' % (', '.join(new) if new else '无'))
for k in new:
    r, t, d, i, q = d21[k]
    say('      %-10s #%-3d Total %.2f  Days %-3d IS %-6d Uniq %.2f   日均分 %d' % (k, r, t, d, i, q, i / d))

say('')
say('=' * 96)
say('三、关键对标：今天第 10 名 HL19556（慢速老号型）')
say('=' * 96)
r, t, d, i, q = d21['HL19556']
say('  HL19556: Days %d / IS %d / Uniq %.2f / Total %.2f / 日均分 %d' % (d, i, q, t, i / d))
say('  我们   : Days 25 / IS 8636 / Uniq 0.69 / Total 0.58 / 日均分 345')
say('  => 它日均分 %d「低于」我们的 345，靠的是天数多 %d 天。' % (i / d, d - 25))
for rate in (246, 288, 345, 400, 450):
    need_days = (i - 8636) / rate
    say('     若我们日均分 %3d：IS 追上 HL19556 需 %4.1f 天（届时 Days=%.0f、IS=%.0f）'
        % (rate, need_days, 25 + need_days, 8636 + rate * need_days))

OUT.close()
