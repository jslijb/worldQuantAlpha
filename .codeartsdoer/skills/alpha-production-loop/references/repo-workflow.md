# 本仓库可执行流程

> 本文件是"路径相关"的部分，迁移到其他项目时只改这里。

## 环境

- Python 虚拟环境 `bigmodel`（已存在；**不要** `conda init`）
- 平台凭据：`brain_credentials.txt`

## 单条模拟（最常用）

```powershell
python -m alpha_loop.run_one --market <REGION> --expr "<表达式>" --universe <UNIVERSE> `
  --neut <NEUT> --decay <int> --trunc <float> --tag <label>
```

输出：`GATES {...}` / `ALPHA <id>` / `VERDICT S=.. F=.. TO=..` / `CHECKS {...}`

## 单条提交并取判决

```powershell
python -c "from alpha_loop.auth import Brain; from alpha_loop import submit; b=Brain(); b.login(); print(submit.submit(b,'<ALPHA_ID>'))"
```

然后查：`GET /alphas/<id>/submit`（403 才是判决；200 空 = 待出）。

## 超级 Alpha

```powershell
python -m alpha_loop.run_super --region USA --universe TOP3000 --decay 32 --limit 10 `
  --trunc 0.08 --neut SUBINDUSTRY --combo "1" --sel "(1-self_correlation)"
```

脚本内部流程：创建 → 轮询模拟 → PATCH 描述 → 提交 → 轮询判决。

## 字段缓存补齐

```powershell
python -m alpha_loop.pull_dataset_fields --region EUR --universe TOP2500 --dataset fundamental94 --dataset fundamental23
```

> 全量 `FieldDB().load(force=True)` 会被平台 10000 条上限截断，必须用上面这条按数据集补。

## 记账

- 每轮一行：`data/alpha_quality_analysis/IDEA_LOOP_LEDGER.csv`
- 入池一行：`data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`
- 判决原件：`alpha_loop/state/verdicts/<alpha_id>.json`

## 判据快照（自动维护）

```powershell
python .codeartsdoer/skills/alpha-production-loop/scripts/sync_evidence.py
```

只读事实源，重写 `references/evidence/criteria_snapshot.md`；内容无变化时不写盘。

## 测试

```powershell
pytest tools/tests -q
pytest alpha_loop/tests -q
```

## 配额节奏

- **配额窗口：北京时间 14:00**（用户实测确认；不要按"美东 0 点 ≈ 北京 13:00"推算，那个换算不成立）。
  配额未开时提交会返回 `Alpha submissions N reached quota of N`。
- 每日常规 4 条 + 超级 1 条。
- 模拟不占提交配额；可在配额未开时先攒候选，但**候选的主腿经济量必须互不相同**
  （同一经济量换字面字段仍会撞 SELF，实测 `sales`↔`revenue` = 0.9743）。