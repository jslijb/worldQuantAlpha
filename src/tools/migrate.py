# -*- coding: utf-8 -*-
"""迁移脚本：活跃脚本 -> src/，文档 -> docs/。不删除历史脚本（下一步单独做）。"""
import shutil, sys
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')

CHDIR_SNIPPET = """
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
"""

def insert_chdir(path: Path):
    s = path.read_text(encoding='utf-8')
    if 'brain_credentials.txt' in s and '_os.chdir' in s:
        return 'skip(already)'
    lines = s.split('\n')
    at = 0
    if lines and lines[0].startswith('#!'):
        at = 1
    if len(lines) > at and (lines[at].strip().startswith('# -*- coding') or lines[at].strip().startswith('# coding')):
        at += 1
    lines[at:at] = CHDIR_SNIPPET.split('\n')[1:-1]
    path.write_text('\n'.join(lines), encoding='utf-8')
    return 'ok'

# ---------- 1. 活跃脚本 & 工具 ----------
CODE_MOVES = {
    'utils.py': 'src/core/utils.py',
    'AlphaSimulator.py': 'src/core/AlphaSimulator.py',
    'submit_v2.py': 'src/submit/submit_v2.py',
    'probe_corr_service.py': 'src/submit/probe_corr_service.py',
    'precheck_only.py': 'src/submit/precheck_only.py',
    'mine_batch120.py': 'src/mine/mine_batch120.py',
    'mine_batch121.py': 'src/mine/mine_batch121.py',
    'auto_submit_loop.py': 'src/ops/auto_submit_loop.py',
    'calc_fitness.py': 'src/tools/calc_fitness.py',
    'summarize_mined.py': 'src/tools/summarize_mined.py',
    'fetch_alphas.py': 'src/tools/fetch_alphas.py',
    'corr_watch.py': 'src/tools/corr_watch.py',
}
(ROOT / 'src' / 'tools').mkdir(parents=True, exist_ok=True)
for src, dst in CODE_MOVES.items():
    s, d = ROOT / src, ROOT / dst
    if not s.exists():
        print('MISS', src); continue
    shutil.move(str(s), str(d))
    r = insert_chdir(d)
    print(f'moved {src:28} -> {dst:36} chdir={r}')

# auto_submit_loop 里对 submit_v2 的引用改路径
p = ROOT / 'src' / 'ops' / 'auto_submit_loop.py'
if p.exists():
    t = p.read_text(encoding='utf-8').replace("'submit_v2.py'", "'src/submit/submit_v2.py'").replace('"submit_v2.py"', '"src/submit/submit_v2.py"')
    p.write_text(t, encoding='utf-8')

# ---------- 2. 文档 ----------
DOC_MOVES = {
    # research
    'BRAIN_Research16_分析师短期交易思路_20260915.md': 'docs/research/Research16_分析师短期交易思路.md',
    'BRAIN_东吴证券_优加换手率UTR因子_20260914.md': 'docs/research/东吴证券_UTR因子_优加换手率.md',
    'data/alpha_quality_analysis/LESSONS_20260914_球队硬币与挖矿复盘.md': 'docs/research/球队硬币与挖矿复盘_20260914.md',
    'docs/idea_regret_factor.md': 'docs/research/idea_regret_factor_后悔因子.md',
    # exam（考试资料单独存放）
    'BRAIN_备考总纲_详细版.md': 'docs/exam/备考总纲_详细版.md',
    'BRAIN_备考待补充知识清单.md': 'docs/exam/备考待补充知识清单.md',
    'BRAIN_研究能力笔试面试学习指南.md': 'docs/exam/研究能力笔试面试学习指南.md',
    'BRAIN_快速表达式_IQC提示与Alpha示例题库.md': 'docs/exam/快速表达式_IQC提示与Alpha示例题库.md',
    'BRAIN_Alpha提交测试完整清单.md': 'docs/exam/Alpha提交测试完整清单.md',
    'BRAIN_IQC团队指南.md': 'docs/exam/IQC团队指南.md',
    'docs/worldQuant 考试笔记.txt': 'docs/exam/考试笔记.txt',
    # study
    'BRAIN_零基础学量化第一课_新手入门.md': 'docs/study/零基础学量化第一课_新手入门.md',
    'BRAIN_零基础学量化第二课_数据与算子.md': 'docs/study/零基础学量化第二课_数据与算子.md',
    'BRAIN_零基础学量化第三课_中性化与trade_when.md': 'docs/study/零基础学量化第三课_中性化与trade_when.md',
    'BRAIN_零基础学量化第四课_Decay_Vector_Do_Dont.md': 'docs/study/零基础学量化第四课_Decay_Vector_Do_Dont.md',
    'BRAIN_Alpha与回测原理完整教程.md': 'docs/study/Alpha与回测原理完整教程.md',
    'BRAIN_第一个Alpha回测与结果解读.md': 'docs/study/第一个Alpha回测与结果解读.md',
    'BRAIN_进阶指南_理解模拟结果与提升Alpha表现.md': 'docs/study/进阶指南_理解模拟结果与提升Alpha表现.md',
    'BRAIN_Alpha改进与顾问进阶指南.md': 'docs/study/Alpha改进与顾问进阶指南.md',
    # project（平台规则 / 工程文档 / 数据集参考）
    'BRAIN_WorldQuant背景与顾问指南.md': 'docs/project/WorldQuant背景与顾问指南.md',
    'BRAIN_平台行为准则与顾问边界.md': 'docs/project/平台行为准则与顾问边界.md',
    'BRAIN_顾问收入计算与提升指南.md': 'docs/project/顾问收入计算与提升指南.md',
    'BRAIN_顾问组队与权重共享.md': 'docs/project/顾问组队与权重共享.md',
    'BRAIN_WorldQuant_Challenge_挑战赛规则.md': 'docs/project/WorldQuant_Challenge_挑战赛规则.md',
    'BRAIN_核心数据集类别详解.md': 'docs/project/数据集_核心类别详解.md',
    'BRAIN_其他数据集与高级数据字段指南.md': 'docs/project/数据集_其他数据集与高级字段.md',
    'BRAIN_Option6数据集使用指南.md': 'docs/project/数据集_Option6使用指南.md',
    'BRAIN_回测结果指标与Alpha状态.md': 'docs/project/回测结果指标与Alpha状态.md',
    'BRAIN_回测设置(Simulation_Settings)完全指南.md': 'docs/project/回测设置完全指南.md',
    'BRAIN_FastExpression_官方操作符完整清单.md': 'docs/project/官方_FastExpression操作符清单.md',
    'WQ_BRAIN_API.md': 'docs/project/API_WQ_BRAIN_API.md',
    'WQ_RANKING_GOALS.md': 'docs/project/目标_排名目标.md',
    'docs/spec.md': 'docs/project/SDD_spec.md',
    'docs/design.md': 'docs/project/SDD_design.md',
    'docs/tasks.md': 'docs/project/SDD_tasks.md',
    'docs/pitfalls.md': 'docs/project/SDD_pitfalls.md',
    'docs/methodology.md': 'docs/project/SDD_methodology_48轮实测沉淀.md',
    'data/alpha_quality_analysis/MINING_REPORT.md': 'docs/project/报告_挖矿报告.md',
    'data/alpha_quality_analysis/QUALITY_REPORT.md': 'docs/project/报告_质量报告.md',
    'data/alpha_quality_analysis/SUBMIT_REPORT.md': 'docs/project/报告_提交报告.md',
    'data/alpha_quality_analysis/PLAYBOOK.md': 'docs/methodology/06_打法手册/PLAYBOOK.md',
    # archive
    'docs/README.md': 'docs/archive/README_旧版_0827.md',
}
(ROOT / 'docs' / 'methodology' / '06_打法手册').mkdir(parents=True, exist_ok=True)
ok = miss = 0
for src, dst in DOC_MOVES.items():
    s, d = ROOT / src, ROOT / dst
    if not s.exists():
        print('  MISS', src); miss += 1; continue
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(s), str(d)); ok += 1
print(f'文档移动: {ok} 成功 / {miss} 缺失')

# ---------- 3. 图片资源 ----------
imgdst = ROOT / 'docs' / 'exam' / 'images'
if (ROOT / 'docs' / 'images' / 'exam').exists():
    shutil.move(str(ROOT / 'docs' / 'images' / 'exam'), str(imgdst))
    print('考试截图 ->', imgdst.relative_to(ROOT))
# operators OCR 中间产物删除（原 PDF 保留）
opd = ROOT / 'docs' / 'images' / 'operators'
if opd.exists():
    shutil.rmtree(opd); print('删除 OCR 中间产物 docs/images/operators/')

print('DONE')
