# -*- coding: utf-8 -*-
"""前 30 名实测数据 -> 目标前 10 的差距量化 + 评分列可解释性检验"""
import io, json, time
import numpy as np
import requests

OUT = io.open(r'D:\Python\worldquant\_autologs\_top10_gap.txt', 'w', encoding='utf-8')
def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s); OUT.write(s + '\n'); OUT.flush()

# 截图转录：rank, user, Total, Days, IS, Uniq
ROWS = [
 (1,'CS35156',0.86,39,17229,0.66),
 (2,'YX42680',0.85,34,13077,0.54),
 (3,'Ke Wang',0.82,32,19467,0.63),
 (4,'FL70603',0.81,48,13616,0.83),
 (5,'CH42645',0.79,35,10298,0.58),
 (6,'MG76588',0.79,32,15417,0.72),
 (7,'HG77739',0.77,32,12076,0.72),
 (8,'JW49109',0.77,48,12617,0.85),
 (9,'CW16048',0.74,48,10943,0.85),
 (10,'HL19556',0.73,48,11509,0.86),
 (11,'Leslie Cheung',0.71,45,8077,0.51),
 (12,'YW70391',0.71,26,9601,0.49),
 (13,'HL14389',0.71,50,11886,0.88),
 (14,'BH65499',0.70,17,10495,0.49),
 (15,'WL77079',0.69,48,11730,0.88),
 (16,'SJ63724',0.69,22,16170,0.78),
 (17,'XP53031',0.69,20,12868,0.74),
 (18,'YL36885',0.69,19,12687,0.72),
 (19,'YY54474',0.69,48,10356,0.86),
 (20,'PF72535',0.69,19,10880,0.65),
 (21,'Shao Fei',0.69,8,21385,0.51),
 (22,'WW60183',0.68,12,10606,0.38),
 (23,'LY76923',0.68,12,15103,0.63),
 (24,'QJ87786',0.68,9,11387,0.44),
 (25,'XW31386',0.68,11,12011,0.58),
 (26,'BX12838',0.67,50,10099,0.87),
 (27,'XW95492',0.67,6,14036,0.51),
 (28,'TT70501',0.66,7,12604,0.53),
 (29,'YZ41300',0.66,9,11771,0.57),
 (30,'CY21614',0.66,41,9718,0.84),
]
US = (130,'我们(当前)',0.58,25,8636,0.69)

say('='*78)
say('一、前 30 名实测（含 IS/天 折算）')
say('='*78)
say('%-5s %-14s %6s %5s %8s %6s %9s' % ('#','user','Total','Days','IS','Uniq','IS/day'))
for r in ROWS:
    say('%-5d %-14s %6.2f %5d %8d %6.2f %9.0f' % (r[0], r[1], r[2], r[3], r[4], r[5], r[4]/r[3]))
say('%-5s %-14s %6.2f %5d %8d %6.2f %9.0f' % ('130','我们(当前)',US[2],US[3],US[4],US[5],US[4]/US[3]))

say('')
say('='*78)
say('二、前 10 名 / 11-30 名的实测区间')
say('='*78)
for label, sub in [('前10', ROWS[:10]), ('11-30', ROWS[10:])]:
    for idx, name in [(2,'Total'),(3,'Days'),(4,'IS'),(5,'Uniq')]:
        v = [r[idx] for r in sub]
        say('%-6s %-6s min %8.2f  中位 %8.2f  max %8.2f' % (label, name, min(v), float(np.median(v)), max(v)))
    say('-')

say('')
say('='*78)
say('三、三列能不能解释 Total？（最小二乘拟合 + 反例检验）')
say('='*78)
A = np.array([[r[3], r[4], r[5]] for r in ROWS], float)
y = np.array([r[2] for r in ROWS], float)
X = np.column_stack([np.ones(len(y)), A, np.log(A[:,1])])
coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
pred = X @ coef
ss = ((y-pred)**2).sum(); st = ((y-y.mean())**2).sum()
say('Total ≈ %.4f + %.6f*Days + %.3e*IS + %.4f*Uniq + %.5f*ln(IS)' % tuple(coef))
say('   R2 = %.4f   残差std = %.4f   最大残差 = %.4f  (Total 2位小数 => 噪声 0.005)'
    % (1 - ss / st, (y - pred).std(), np.abs(y - pred).max()))
say('   用该式预测我们(25, 8636, 0.69) = %.3f   （实际 0.58）'
    % (coef[0]+coef[1]*25+coef[2]*8636+coef[3]*0.69+coef[4]*np.log(8636)))

# 反例：总分更高，但三个维度全面更差
viol = []
for i in range(len(ROWS)):
    for j in range(len(ROWS)):
        a, b = ROWS[i], ROWS[j]
        if a[2] > b[2] + 1e-9:
            if a[3] <= b[3] and a[4] <= b[4] and a[5] <= b[5] and (a[3] < b[3] or a[4] < b[4] or a[5] < b[5]):
                viol.append((a, b))
say('')
say('★ 反例对（对方三个维度全面不低于我，总分却更低）= %d 对' % len(viol))
for a, b in viol[:8]:
    say('   #%d %s Total%.2f vs #%d %s Total%.2f   (%d,%d,%.2f) vs (%d,%d,%.2f)'
        % (a[0], a[1], a[2], b[0], b[1], b[2], a[3], a[4], a[5], b[3], b[4], b[5]))

# 秩相关
def rank(v):
    v = np.asarray(v, float); order = v.argsort(); rk = np.empty(len(v)); rk[order] = np.arange(len(v))
    return rk
say('')
say('Spearman(列, Total)  %s' % '  '.join(
    '%s=%.3f' % (n, np.corrcoef(rank([r[i] for r in ROWS]), rank([r[2] for r in ROWS]))[0,1])
    for i, n in [(3,'Days'),(4,'IS'),(5,'Uniq')]))

say('')
say('='*78)
say('四、平台侧口径探测')
say('='*78)
try:
    creds = json.load(io.open(r'D:\Python\worldquant\brain_credentials.txt', encoding='utf-8'))
except Exception:
    creds = None
s = requests.Session()
if creds:
    s.auth = tuple(creds)
    ok = False
    for _ in range(6):
        try:
            if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                ok = True; break
        except Exception:
            pass
        time.sleep(3)
    say('认证:', 'OK' if ok else 'FAIL')
    if ok:
        urls = [
            ('competition', 'https://api.worldquantbrain.com/competitions/challenge'),
            ('lb?limit=30', 'https://api.worldquantbrain.com/competitions/challenge/leaderboard?limit=30&offset=0'),
            ('lb?limit=5',  'https://api.worldquantbrain.com/competitions/challenge/leaderboard?limit=5'),
            ('leaderboards','https://api.worldquantbrain.com/competitions/challenge/leaderboards?limit=30'),
            ('ranking',     'https://api.worldquantbrain.com/competitions/challenge/ranking?limit=30'),
            ('users',       'https://api.worldquantbrain.com/competitions/challenge/users?limit=30'),
        ]
        for tag, u in urls:
            try:
                r = s.get(u, timeout=45)
                say('[%s] %d  %s' % (tag, r.status_code, str(r.text)[:400].replace('\n', ' ')))
                if r.status_code == 200:
                    try:
                        io.open(r'D:\Python\worldquant\_autologs\_lb_%s.json' % tag.replace('?', '_').replace('=', '').replace('&', '_'),
                                'w', encoding='utf-8').write(r.text)
                    except Exception:
                        pass
            except Exception as e:
                say('[%s] ERR %s' % (tag, e))
            time.sleep(1)

say('')
say('='*78)
say('五、IS 折算：走到前 10 还差多少')
say('='*78)
gap_is = min(r[4] for r in ROWS[:10]) - US[4]
say('前10 里 IS 最低 = %d (#5) ；我们 = %d ；硬差 = %d' % (min(r[4] for r in ROWS[:10]), US[4], gap_is))
say('前10 里 Days 最低 = %d ；我们 = %d ；硬差 = %d 天' % (min(r[3] for r in ROWS[:10]), US[3], min(r[3] for r in ROWS[:10])-US[3]))
say('前10 里 Uniq 最低 = %.2f ；我们 = %.2f ' % (min(r[5] for r in ROWS[:10]), US[5]))
say('')
say('近两日实测日分：09-20 = +288/天、09-21 = +288/天（IS 8636 未刷新）')
say('')
say('='*78)
say('六、IS = 日均分 x Days 验证 + 日均分横向对比')
say('='*78)
ours_rate = US[4]/US[3]
rates10 = [r[4]/r[3] for r in ROWS[:10]]
rates30 = [r[4]/r[3] for r in ROWS]
say('我们: %d / %d 天 = %.0f 分/天' % (US[4], US[3], ours_rate))
say('前10 日均分: %s  中位 %.0f' % (' '.join('%.0f' % x for x in rates10), float(np.median(rates10))))
say('全部30名 日均分 中位 %.0f  max %.0f' % (float(np.median(rates30)), max(rates30)))
say('=> IS 基本等于 日均分 x Days（rank10: 240x48=11520 vs 实际 11509；rank5: 294x35=10290 vs 10298）')
say('=> 我们的 345 分/天 已高于前10中位 %.0f —— 差距主要是天数，不是质量' % float(np.median(rates10)))

say('')
say('='*78)
say('七、前 10 门槛前沿线（IS vs Days）与 ETA')
say('='*78)
d = np.array([r[3] for r in ROWS[:10]], float)
i = np.array([r[4] for r in ROWS[:10]], float)
A2 = np.column_stack([np.ones(len(d)), d])
c2, _, _, _ = np.linalg.lstsq(A2, i, rcond=None)
pr = A2 @ c2
ss2 = ((i-pr)**2).sum(); st2 = ((i-i.mean())**2).sum()
say('前沿线: IS_req ≈ %.0f %+.1f x Days      R2=%.3f  残差std=%.0f'
    % (c2[0], c2[1], 1-ss2/st2, (i-pr).std()))
step = -c2[1]
say('含义: Days 每多 1 天，进前10 所需的 IS 少 %.0f 分（因为对手也在攒天数）' % step)
say('')
say('  Days   该档所需IS   288/天    345/天    450/天')
import datetime as _dt
for dd in [28, 30, 32, 35, 38, 41, 45, 48]:
    need = c2[0] + c2[1]*dd
    t = dd - US[3]
    say('  %4d  %9.0f   %9.0f %9.0f %9.0f' % (dd, need, US[4]+288*t, US[4]+345*t, US[4]+450*t))
say('')
for rate in [288, 345, 400, 450, 500, 600]:
    tt = (c2[0] + c2[1]*US[3] - US[4]) / (rate + step)
    dd = US[3] + tt; ii = US[4] + rate*tt
    dt = _dt.date(2026, 9, 21) + _dt.timedelta(days=int(round(tt)))
    say('  日均分 %3d：还需 %4.1f 天 -> Days=%.0f / IS=%.0f -> 预计 %s 触到前10边界'
        % (rate, tt, dd, ii, dt.strftime('%m-%d')))
say('')
say('注意：前沿线只用前10的10个点拟合、且存在 25 对反例（三列不能完全解释 Total），')
say('     所以 ETA 只当量级参考，不作为承诺。')

say('')
say('='*78)
say('八、线性模型（31 个点：前30 + 我们自己）-> 超越时间')
say('='*78)
D = np.array([r[3] for r in ROWS] + [US[3]], float)
I = np.array([r[4] for r in ROWS] + [US[4]], float)
U = np.array([r[5] for r in ROWS] + [US[5]], float)
T = np.array([r[2] for r in ROWS] + [US[2]], float)
X3 = np.column_stack([np.ones(len(T)), D, I, U])
c3, _, _, _ = np.linalg.lstsq(X3, T, rcond=None)
p3 = X3 @ c3
R2 = 1 - ((T-p3)**2).sum() / ((T-T.mean())**2).sum()
say('Total ≈ %.4f + %.6f*Days + %.3e*IS + %.4f*Uniq' % (c3[0], c3[1], c3[2], c3[3]))
say('   R2 = %.4f   残差std = %.4f' % (R2, (T-p3).std()))
say('   预测我们(0.58 / 25 / 8636 / 0.69) = %.3f' % (c3[0]+c3[1]*25+c3[2]*8636+c3[3]*0.69))
say('   边际收益: +1 天 -> Total %+.4f ; +1000 IS -> %+.4f ; +0.10 Uniq -> %+.4f'
    % (c3[1], c3[2]*1000, c3[3]*0.1))
say('')
say('   若要单靠一个维度从 0.58 到 0.73：')
for nm, per in [('Days (+1/天)', c3[1]), ('IS (+1000)', c3[2]*1000), ('Uniq (+0.10)', c3[3]*0.1)]:
    if per > 0:
        need = 0.15/per
        say('     %-14s 需要 %8.1f 个单位' % (nm, need))
    else:
        say('     %-14s 系数为负/零，单独推不动' % nm)
say('')
say('   沿我们的轨迹（Days 25+t，Uniq 0.69 不变）达到 Total 0.73 的时间：')
for rate in [245, 288, 345, 400, 450, 600]:
    t = 0.0
    while t < 400:
        if (c3[0]+c3[1]*(25+t)+c3[2]*(8636+rate*t)+c3[3]*0.69) >= 0.73:
            break
        t += 0.25
    dt = _dt.date(2026, 9, 21) + _dt.timedelta(days=int(round(t)))
    say('     日均分 %3d -> %4.1f 天后  (Days=%.0f / IS=%.0f)  预计 %s'
        % (rate, t, 25+t, 8636+rate*t, dt.strftime('%m-%d')))
say('')
say('   ★ 期间对手也在涨：这只给了我们"进入前10 边界"的时间，守住前10 需要持续同样节奏。')

say('')
say('='*78)
say('九、历史收敛速度法（最简单、最不依赖模型）')
say('='*78)
say('   09-05 快照：我们 Total 0.38（IS 4708 / Days 9）；当时前10 门槛约 0.80')
say('   09-21 实测：我们 Total 0.58（IS 8636 / Days 25）；前10 门槛 0.73')
say('   16 天里：我们 +0.20，门槛 -0.07 => 净收敛 +0.27 => %.4f/天' % (0.27/16))
gap = 0.73 - 0.58
say('   当前缺口 %.2f => 还需 %.1f 天 => 预计 %s'
    % (gap, gap/(0.27/16),
       (_dt.date(2026, 9, 21) + _dt.timedelta(days=int(round(gap/(0.27/16))))).strftime('%m-%d')))
say('')
say('   实测日均分（最近 16 天）= (8636-4708)/16 = %.0f 分/天（低于 25 天均值 345）' % ((8636-4708)/16))
say('   => 想把 ETA 提前，唯一的抓手是把日分从 %.0f 拉回 345 以上' % ((8636-4708)/16))
say('')
say('   ★ 三法交叉：线性模型 %s / 前沿线 %s / 收敛速度 %s  => 中位约 10-01，区间 09-30~10-06'
    % ('10-01', '10-06', (_dt.date(2026, 9, 21) + _dt.timedelta(days=int(round(gap/(0.27/16))))).strftime('%m-%d')))
OUT.close()
