# -*- coding: utf-8 -*-
"""lb_record.py —— 记录每日前 30 榜单 + 我们五数，算差距统计
用法：python lb_record.py "日期" <csv行：rank,user,total,days,is,uniq> ... --me rank,total,days,is,uniq
由会话内直接调用 record 函数更方便：见 0922 daily log。
"""
import io, csv, os, sys, statistics

OUT = r'D:\Python\worldquant\docs\project\leaderboard_top30_daily.csv'

def record(date, rows, me, src='screenshot'):
    """rows: [(rank,user,total,days,is,uniq,univ), ...] 前30；me: (rank,total,days,is,uniq)"""
    new = not os.path.exists(OUT)
    with io.open(OUT, 'a', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['date', 'src', 'scope', 'rank', 'user', 'total', 'days', 'is', 'uniq', 'univ'])
        for r in rows:
            w.writerow([date, src, 'top30', *r])
        w.writerow([date, src, 'me', '', 'LJ49886 (Me)', *me, 'not applicable'])
    # 统计
    tot = [r[2] for r in rows]; days = [r[3] for r in rows]; iss = [r[4] for r in rows]; unq = [r[5] for r in rows]
    lines = []
    lines.append('%s 前30统计（n=%d）' % (date, len(rows)))
    lines.append('  Total: max %.2f / #30 %.2f / 中位 %.2f | 我 %.2f（差 #30 %.2f）' % (max(tot), tot[-1], statistics.median(tot), me[1], me[1]-tot[-1]))
    lines.append('  Days : 中位 %.0f / 区间 %d~%d | 我 %d' % (statistics.median(days), min(days), max(days), me[2]))
    lines.append('  IS   : 中位 %d / 区间 %d~%d | 我 %d（差中位 %d）' % (statistics.median(iss), min(iss), max(iss), me[3], me[3]-statistics.median(iss)))
    lines.append('  Uniq : 中位 %.2f / 区间 %.2f~%.2f | 我 %.2f' % (statistics.median(unq), min(unq), max(unq), me[4]))
    # 前10 vs 11~30
    t10 = rows[:10]; t30 = rows[10:]
    lines.append('  前10 : Total 中位 %.2f / Days 中位 %.0f / IS 中位 %d / Uniq 中位 %.2f' % (
        statistics.median([r[2] for r in t10]), statistics.median([r[3] for r in t10]),
        statistics.median([r[4] for r in t10]), statistics.median([r[5] for r in t10])))
    lines.append('  11~30: Total 中位 %.2f / Days 中位 %.0f / IS 中位 %d / Uniq 中位 %.2f' % (
        statistics.median([r[2] for r in t30]), statistics.median([r[3] for r in t30]),
        statistics.median([r[4] for r in t30]), statistics.median([r[5] for r in t30])))
    return '\n'.join(lines)

if __name__ == '__main__':
    print(__doc__)
