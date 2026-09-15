# BRAIN 零基础学量化第四课：Decay、Vector Data 与 Alpha Do's & Don'ts

> 来源：量化研究小组结课会议逐字稿（腾讯会议元宝整理） + PPT 截图  
> 会议时间：2025-03-17  
> 主讲人：导师  
> 更新时间：2026-09-06

---

## TL;DR 考试速查卡

- **Decay** 是在 neutralization 之后对仓位权重做**时间加权平均**，降低 turnover。
- Decay 公式：今天权重×N + 昨天×(N-1) + … + 最早×1，除以 N(N+1)/2。
- Alpha 表达式最大参数通常 5 天，decay 设 10/20 天经济学上无意义。
- **Vector Data** 是三维（股票×日期×entry 条数），长度不一，必须先通过 vector operator 降维成 matrix。
- 好 Alpha 四特征：**Robustness / Uniqueness / Value-add / Consistency**。
- **Don't**：过拟合参数（如 2.124、0.618）硬凑提交；为降相关性添加无意义噪音。
- **Do**：保持开放心态，复现后往前走一两步（换 dataset / group / operator）。

![好 Alpha 的 Do's](docs/images/good_practice_dos.png)

![Alpha 的 Don'ts](docs/images/alpha_donts_overfitting_noise.png)

---

## 一、开场与上节课作业讲评

### 1. 找不到 Alpha / Operator 权限问题

- 合集里有 100 多篇文章，找不到 Alpha 说明读得不够多，要继续训练。
- 没有某个 operator 权限是正常的，平台会逼你去 operator 列表里找**类似**的替代品。
- 上一节课讲了模板，要学会找**类似**，而不是只会用那一个 operator。
- 不能死读书，要会**换、会抽象**。

### 2. 抽象成模板的方法

- 先看原 Alpha 在哪个 dataset、用了什么 data set，把 data 全放进来。
- 在 BRAIN platform 的 **Learn 界面**可以搜 operator 形式，不懂可以借助工具查询。
- Operator 列表是平台语法的智慧结晶，量化没用的不会放进来，必须反复搞懂每一个 operator。

### 3. 搜索空间过大导致效率低

- 搜索空间到十万级会非常慢，说明定位不够精准。
- 举例：group neutralize / rank / normalize / scale 别全换，先拿一两个试，效果不好就删掉，再调整搜索空间。

### 4. 作业批改与 Genius Program

- 每个作业都会看，搜到十万级空间会慢；担心抄作业会放慢批改。
- Genius program 仔细阅读，以后成为 consultant 会再介绍收入组成。

---

## 二、顾问入职问卷与合规（重点）

### 填写规范

- 收到问卷后，去中文论坛带钻石的帖子按申请流程说明一步一步走。
- 名字填拼音或拼音+中文，但问卷里要求英文的写英文（print name 用打印体/标准体，跟护照身份证一致）。
- 没护照填 `NA`，不要填 `N/A` 或其他变体，保持一致。
- 身份证上传要 **PDF**，正反面都要，别拖照片进去。
- 背景调查签名中英文好好签，first/middle name 照实填。
- 选是否问公司完全尊重个人意愿。

### 提交与审核流程

- 社会人士没收到合同可回邮件或问群友要。
- 签字别签错位置：独立顾问下边是自己签，上面总经理处别帮签。
- 点 **submit task**，作业要求 task 里看到空空的即可。
- 交完收到"五天后处理"邮件：五天没打回 = 进入背调；背调约一个月（春节会更长）。
- 背调由**官方指定的第三方背景调查机构**执行，只走官方流程、保护隐私；任何非官方联系都不要信。

### 银行卡与姓名一致性（反洗钱）

- 问卷填的姓名必须和以后绑定的银行卡姓名一致，否则账号立即关掉。
- 现用名/曾用名开卡容易踩坑，千万别用家人卡代收钱。

### 没收到邀请的排查

- 已提交、超三天（不含当天）、没收到邮件、没邀请：发官方邮件附截图问"为何没邀请"。

---

## 三、本节课核心：Decay 与 Vector Data

### 1. Decay（时间加权平均）

**作用时机**：在 **neutralization 之后**，对交易信号（仓位权重）做时间加权平滑。

**公式**：

设 decay = N，则今天的最终权重为：

```
weight_today = (w_0 × N + w_1 × (N-1) + ... + w_{N-1} × 1) / (N × (N + 1) / 2)
```

其中 w_0 是今天权重，w_1 是昨天权重，依次类推。

**例子（N = 3）**：

A 股票今天 -0.038，昨天 -0.03，前天 +0.03：

```
weight = (-0.038 × 3 + (-0.03) × 2 + 0.03 × 1) / 6
       = (-0.114 - 0.060 + 0.030) / 6
       = -0.144 / 6
       = -0.024
```

**作用与注意事项**：

- **降低 turnover**（减少交易成本）。
- 但是 **N 别乱设**。
- Alpha 表达式中的最大参数通常是 **5 天**；decay 设 10/20 天在经济学上无意义，信号会不纯。

**考试速记**：

| Decay | 含义 | 注意 |
|---|---|---|
| 对仓位做时间加权平均 | 降低 turnover | Alpha 参数通常最大 5 天，decay 过大信号失真 |

### 2. Vector Data（向量数据）

**定义**：

- 数据类型除了 matrix / group 之外，还有 **vector data**。
- 它是**三维**：股票 × 日期 × entry 条数。
- 同一只股票在不同日期可能有不同数量的 entries，长度不一。

**例子**：

新闻数据中，Google 一天 3 条、Facebook 4 条、Apple 2 条，长度不同。

**使用规则**：

- Vector data **不能直接参与 Alpha 表达式**。
- 必须先接 **vector operator** 降维成 matrix：
  - `vector_avg` / `vector_average`（向量平均）
  - `vector_sum`（向量求和）
  - `vector_count`（向量计数）
- 新闻条数多可能代表关注度高，信息丰富，但必须先降维。

**重要提醒**：

> BRAIN 里的 vector/matrix 不是数学意义上的向量/矩阵，只是命名。

**考试速记**：

| Vector Data | 特点 | 使用方法 |
|---|---|---|
| 三维：股票×日期×entry | 长度不一 | 必须用 vector_avg / vector_sum / vector_count 降维成 matrix |

---

## 四、好 Alpha 的标准与 Do's / Don'ts

### 1. In-sample / Out-sample

- 平台能看到的是 **in-sample**（如到 2022 年 5 月），之后是 **out-sample**，故意不让用户调参。
- 只调 in-sample 容易 **overfitting**，out-sample 表现会掉。

### 2. 好 Alpha 的四个特征

| 特征 | 含义 |
|---|---|
| **Robustness**（稳健性） | 改 sub industry → industry、decay 5 → 10 表现不崩 |
| **Uniqueness**（独特性） | 能过相关性测试，尝试跨市场（如 China 研报思路挪到 USA 跑） |
| **Value-add**（增值性） | 对个人组合和 BRAIN 整体都有用，别总重复同动作 |
| **Consistency**（一致性） | 稳定最重要，稳定亏钱也比暴涨暴跌强；基金经理更敢投稳定曲线 |

### 3. Do's and Don'ts

#### ❌ Don'ts（反面教材）

1. **Overfitting（过拟合）**  
   为擦边满足 alpha 提交要求，硬塞无解释参数。  
   例子：`ts_rank(mdf_vol^2.124 * mdf_deq^2 + mdf_sq5^2, 600)`  
   其中 `2.124` 就是无意义硬凑参数。

2. **Adding Noise（添加噪音）**  
   为降低 self-correlation 而故意加入无逻辑表达式。  
   例子：把原 alpha `rank(close - ts_sum(close,5)/5)` 改成 `-rank(close - ts_sum(close,5)/5)*0.65 + rank(dividend/close)`  
   其中 `0.65` 是无意义缩放，out-sample 必差。

**导师总结**：

> Listen to your intuition; when you feel it is not good, then it may not be good.

#### ✅ Do's（好实践）

- **多尝试**：datasets / region / parameters / sub-universe。
- **读官方学习材料**：BRAIN 平台 Learn 栏目。
- **调用已有知识**：把读过的东西和市场认知测试出来。
- **保持开放心态**：测试前不要排除任何想法；同一想法在不同 region/market 表现可能不同。
- **复现后往前走一两步**：换 dataset、换 group、换 operator 组合，就是新的 alpha。

---

## 五、代码框架升级：Pending DB + Worker

### 上节课代码缺点

- 只管发 simulate 请求，不拿 alpha ID，不存 performance，容易出现**幸存者偏差**。

### 新框架

1. 建 `pending_database.csv`：存 alpha 表达式 + settings。
2. 写 `worker` 脚本：
   - 从 CSV 读待跑 alpha，并发发请求（consult 10 个 / user 3 个）。
   - 轮询进度，谁先完把 alpha ID + sharp/turnover 等写回 `complete_database.csv`。
   - 马上从 pending 补一个新 alpha 上去，保持队列满。
3. 好处：随时插队、随时复盘失败 alpha、可用代码筛"可提交"。

### 代码获取

- 中文论坛帖子 **《alpha simulator》**，核心是一个 simulator class：管理登录 / 发请求 / check_simulation_progress / get alpha ID。

---

## 六、结课叮嘱

- 自由作业：用云电脑挂程序、读《阿尔法灵感启示录》积累模板。
- 收到顾问邀请后五天盯邮箱，打回赶紧改，年前处理完。
- Consultant 课按大部队背调进度开，城市场（如武汉）会排。

---

## 七、Q&A 精华

| 问题 | 回答 |
|---|---|
| CSV 判断能否提交有代码吗？ | 论坛看，无现成；核心技能自己写，算各年 sharp 方差等 |
| 跑出一堆可提交 Alpha 哪个最好？ | 稳定即好；定量算指标方差 |
| 提交时改 Alpha name 匿名？ | consult 有 API 可改，user 可 F12 找 |
| 代码日志运行十小时明天接着跑？ | pending list 会续跑 |
| 一阶二阶三阶啥意思？ | 主信号经过几步 operator 修饰 |
| 用得少的 data type 积分权重高？ | 不绝对，value factor 看稳定性 |
| 单 dataset 还是跨 dataset 好？ | 单 dataset 更好，跨 dataset 拼风险大 |
| 前两节链接没收到怕 consult 课也收不到？ | 按登录邮箱发，检查垃圾箱；论坛也有 survey monkey 邀请 |
| 比赛期间提交 Alpha 自动计入？ | 要满足 region/turnover 等比赛门槛才算 |

---

## 考试易错点

- ❌ 错误：Decay 是对 alpha 原始信号做平均。  
  ✅ 正确：Decay 是对 **neutralization 之后的仓位权重**做时间加权平均。
- ❌ 错误：Vector data 可以直接放进 Alpha 表达式。  
  ✅ 正确：必须先通过 `vector_avg` / `vector_sum` / `vector_count` 降维成 matrix。
- ❌ 错误：好 Alpha 就是 IS 夏普最高。  
  ✅ 正确：好 Alpha 四特征是 Robustness / Uniqueness / Value-add / Consistency，稳定比暴涨暴跌更重要。
- ❌ 错误：硬塞 2.124、0.618、0.65 等参数降相关性没问题。  
  ✅ 正确：这是 overfitting / adding noise，out-sample 会崩。
- ❌ 错误：Decay 越大越好。  
  ✅ 正确：Alpha 表达式参数通常最大 5 天，decay 过大（10/20）信号不纯。
