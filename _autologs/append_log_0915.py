# -*- coding: utf-8 -*-
txt = '''

---

## 20:52-21:20 | 李工批复后执行：停定时任务 + 挖矿补任务

### 李工三项批复
1. 两个 ACTIVE 定时任务 -> 停止（已 PAUSED：a9b2c5cd 每4小时补提交、07ac2d4a 每日挖矿，均未删除可恢复）
2. 旧会话归档 -> 李工自己操作
3. 挖矿 simulation 是否越级 -> 不确定，但拍板"继续挖 Alpha 因子，今天补齐之前的任务"

### 挖矿结果
- batch123（w123_，fundamental2 极冷脚注锚，早前会话已跑）：8 条全灭（最高 w123_f SF=3.75）-> 纯冷脚注锚路线证伪。
- batch124（w124_，并发会话 16:18 跑的）：1 条达标 w124_e `6XrkW6R5` SF=4.28 tS=2.78（三锚 cicurrq/dxd5/aqi + 0.5 降权共享腿）。
- batch125（本轮新写 `src/mine/mine_batch125.py`）：6/8 达标——
  w125_h SF=4.78 tS=2.40（E3+xrent）/ w125_g SF=4.40 tS=2.56（纯极冷锚 spceepsp12+prcepsq+spcep12，T=0.314 偏高）/
  w125_c SF=4.33 tS=3.01（E3 换 VOLB 桶）/ w125_f 4.18 / w125_a 4.13 / w125_d 4.13。b(3.69)/e(3.64) 未达标。
- 今日新达标候选合计 7 条（w124_e + w125 6条），任务目标 5 已补齐。全部只挖不提交（不越级约束）。

### 新发现
- fnd6 极冷字段其实有效：w125_g 纯 aC=9~29 三锚 SF=4.40 达标 -> batch123 全灭的问题在 fundamental2 脚注字段（覆盖差），不在"冷"本身。极冷 fnd6 锚是可行的差异化方向。
- w124_e 三锚（aC 279~361）+ 0.5 降权是当前最稳配方骨架。

### 环境故障记录
- WorkBuddy bash shim PATH 崩（dirname/ls/head/wc/sleep 全找不到）+ PowerShell stdout 全吞（Write-Output 都不回显）-> 应对：bash 内建 cd + python 绝对路径 + 输出重定向到文件 + Read 工具读取。python 本身正常。
- git 快照已本地提交 `6c33618`（--no-push，远端仍欠 4+ 个待补推，github 443 仍不通）。
'''
with open('.workbuddy/memory/2026-09-15.md', 'a', encoding='utf-8') as f:
    f.write(txt)
print('appended', len(txt))
