# 平台 Learn 文档全文归档（官方 documentation 全部页面）

> 来源：`GET /tutorials`（目录树）+ `GET /tutorial-pages/{id}`（正文），需登录
> 抓取日期：2026-09-15 ｜ 脚本：`src/tools/fetch_learn_docs.py all`
> 合计 **7 个课程 / 29 页**，成功 **29** 页、失败 0 页
> 素材：图片 **88** 张 ｜ 示例表达式（含完整模拟设置）**24** 个 ｜ 公式 **12** 条 ｜ 表格 **6** 个
> 其中 5 页内嵌的视频**在课程库里有官方字幕**，可直接翻译
> 原文照录：文字 / 表格 / 图片 / 公式均按接口内容原样转换，未改写、未删节

---

## 目录结构

```
docs/study/learn/docs/
├── NN_<课程id>/              官方课程目录（NN = 官方 sequence）
│   └── MM_<页面id>.md        MM = 该课程内页序
├── images/<页面id>/          该页配图（md 中按 ../images/... 引用）
└── README_官方文档结构.md     本文件（逐页清单）
```

> 原始 JSON 证据留档在 `_autologs/learn_docs/{页面id}.json`（未加工的接口返回）。

---

## 逐页清单


### 01 `discover-brain` ｜ Getting Started ｜ 9 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `read-first-starter-pack` | *Read this First * - Starter Pack | PT19M | 11 | 2 | 2 | 0 | 21522 | ✅ `docs/01_discover-brain/01_read-first-starter-pack.md` |
| 02 | `10-steps-start-brain-platform` | 10 Steps to Start on BRAIN | PT1M | 0 | 0 | 0 | 0 | 2290 | ✅ `docs/01_discover-brain/02_10-steps-start-brain-platform.md` |
| 03 | `about-brain-platform` | Introduction to Alphas | PT6M | 2 | 0 | 0 | 1 | 7761 | ✅ `docs/01_discover-brain/03_about-brain-platform.md` |
| 04 | `intermediate-pack-part-1` | Intermediate Pack - Understand Results [1/2] | PT5M | 4 | 0 | 6 | 0 | 6221 | ✅ `docs/01_discover-brain/04_intermediate-pack-part-1.md` |
| 05 | `intermediate-pack-part-2` | Intermediate Pack - Improve your Alpha [2/2] | PT5M | 9 | 0 | 0 | 0 | 5242 | ✅ `docs/01_discover-brain/05_intermediate-pack-part-2.md` |
| 06 | `challenge-help` | WorldQuant Challenge | PT3M | 0 | 0 | 0 | 0 | 3540 | ✅ `docs/01_discover-brain/06_challenge-help.md` |
| 07 | `scoring-algorithm-challenge-users` | Scoring Algorithm for Challenge Users | - | 0 | 0 | 0 | 0 | 3524 | ✅ `docs/01_discover-brain/07_scoring-algorithm-challenge-users.md` |
| 08 | `brain-and-alphas` | BRAIN and Alphas | - | 1 | 0 | 0 | 0 | 14330 | ✅ `docs/01_discover-brain/08_brain-and-alphas.md` |
| 09 | `intermediate-pack-part-3` | Intermediate Pack - Conditional Operators [3/3] 🥉 | - | 6 | 3 | 0 | 0 | 8431 | ✅ `docs/01_discover-brain/09_intermediate-pack-part-3.md` |

### 02 `create-alphas` ｜ Getting Started ｜ 5 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `running-your-first-alpha` | Simulate your first Alpha | PT3M | 3 | 1 | 0 | 0 | 6773 | ✅ `docs/02_create-alphas/01_running-your-first-alpha.md` |
| 02 | `test-period` | Test Period | PT3M | 2 | 0 | 0 | 0 | 2808 | ✅ `docs/02_create-alphas/02_test-period.md` |
| 03 | `simulation-settings` | How to choose the Simulation Settings | PT6M | 3 | 3 | 1 | 0 | 8847 | ✅ `docs/02_create-alphas/03_simulation-settings.md` |
| 04 | `how-brain-platform-works` | ⭐ How BRAIN works | PT12M | 10 | 0 | 1 | 0 | 12430 | ✅ `docs/02_create-alphas/04_how-brain-platform-works.md` |
| 05 | `introduction-brain-expression-language` | Introduction to BRAIN Expression Language | PT3M | 3 | 0 | 0 | 0 | 2755 | ✅ `docs/02_create-alphas/05_introduction-brain-expression-language.md` |

### 03 `examples` ｜ Getting Started ｜ 3 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `19-alpha-examples` | ⭐ Alpha Examples for Beginners | PT4M | 0 | 5 | 0 | 0 | 5582 | ✅ `docs/03_examples/01_19-alpha-examples.md` |
| 02 | `sample-alpha-concepts` | ⭐ Alpha Examples for Bronze Users 🥉 | PT2M | 0 | 3 | 0 | 0 | 3570 | ✅ `docs/03_examples/02_sample-alpha-concepts.md` |
| 03 | `example-expression-alphas` | ⭐ Alpha Examples for Silver Users🥈 | PT3M | 0 | 6 | 0 | 0 | 7743 | ✅ `docs/03_examples/03_example-expression-alphas.md` |

### 04 `interpret-results` ｜ Interpreting Results ｜ 3 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `alpha-submission` | Clear these tests before submitting an Alpha | PT11M | 9 | 0 | 0 | 3 | 16709 | ✅ `docs/04_interpret-results/01_alpha-submission.md` |
| 02 | `parameters-simulation-results` | Parameters in the Simulation results | PT6M | 5 | 0 | 2 | 1 | 10750 | ✅ `docs/04_interpret-results/02_parameters-simulation-results.md` |
| 03 | `how-pass-sub-universe-test` | How to pass the Sub-universe test? 🥈 | - | 4 | 0 | 0 | 0 | 4097 | ✅ `docs/04_interpret-results/03_how-pass-sub-universe-test.md` |

### 05 `understanding-data` ｜ Data ｜ 5 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `data` | Understanding Data in BRAIN: Key Concepts and Tips | PT4M | 1 | 0 | 0 | 1 | 5677 | ✅ `docs/05_understanding-data/01_data.md` |
| 02 | `how-use-data-explorer` | How to use the Data Explorer | PT3M | 5 | 0 | 0 | 0 | 3230 | ✅ `docs/05_understanding-data/02_how-use-data-explorer.md` |
| 03 | `vector-datafields` | Vector Data Fields 🥉 | PT4M | 5 | 0 | 0 | 0 | 4851 | ✅ `docs/05_understanding-data/03_vector-datafields.md` |
| 04 | `group-data-fields` | Group Data Fields 🥈 | PT3M | 0 | 0 | 0 | 0 | 3381 | ✅ `docs/05_understanding-data/04_group-data-fields.md` |
| 05 | `getting-started-option6-implied-volatility-iv` | Option6 Implied volatility (IV) | PT2M | 0 | 0 | 0 | 0 | 7640 | ✅ `docs/05_understanding-data/05_getting-started-option6-implied-volatility-iv.md` |

### 06 `advanced-topics` ｜ Getting Started ｜ 3 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `list-must-read-posts-how-improve-your-alphas-are-submitted` | Must-read posts: How to improve your Alphas🥉 | PT2M | 0 | 0 | 0 | 0 | 2703 | ✅ `docs/06_advanced-topics/01_list-must-read-posts-how-improve-your-alphas-are-submitted.md` |
| 02 | `neut-cons` | Neutralization 🥉 | PT5M | 0 | 0 | 0 | 0 | 6932 | ✅ `docs/06_advanced-topics/02_neut-cons.md` |
| 03 | `getting-started-d0` | D0 | PT4M | 2 | 0 | 0 | 0 | 4473 | ✅ `docs/06_advanced-topics/03_getting-started-d0.md` |

### 07 `regions-and-universes` ｜ Regions and Universes ｜ 1 页

| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `china-region` | China Alphas: Understand the market 🥈 | - | 3 | 1 | 0 | 0 | 3826 | ✅ `docs/07_regions-and-universes/01_china-region.md` |
