# -*- coding: utf-8 -*-
"""2026-09-19 代码清理第二步：删冗余脚本（李工已批准）。
回滚点：git 37317a4（删前快照）。台账/json/判死表一律不碰。"""
import pathlib

ROOT = pathlib.Path(r"D:\Python\worldquant")

# 1) batch 脚本：mine_batch120~180（缺 163/164/179，保留活跃的 181）
batch = [ROOT / "src" / "mine" / f"mine_batch{n}.py" for n in range(120, 181)
         if n not in (163, 164, 179)]
# 2) 旧提交件 6 个
submit_old = ["blind_submit.py", "corr_only.py", "corr_probe_sweep.py",
              "corr_sweep_once.py", "precheck_only.py", "probe_corr_service.py"]
# 3) 一次性 tools 15 个（保留 fetch_alphas / fetch_learn_docs / fetch_learn_video / merge_video_notes）
tools = ["analyze_expr.py", "analyze_real.py", "build_library.py", "build_report.py",
         "calc_fitness.py", "classify_scripts.py", "corr_watch.py", "extract_expr.py",
         "fix_paths.py", "gen_list.py", "migrate.py", "scan_project.py",
         "summarize_mined.py", "supplement_lib.py", "upgrade_analysis.py"]

targets = batch + [ROOT / "src" / "submit" / f for f in submit_old] \
          + [ROOT / "src" / "tools" / f for f in tools] \
          + [ROOT / "src" / "mine" / "__pycache__"]

deleted, missing = [], []
for t in targets:
    if t.is_dir():
        import shutil
        shutil.rmtree(t)
        deleted.append(str(t.relative_to(ROOT)) + "/")
    elif t.exists():
        t.unlink()
        deleted.append(str(t.relative_to(ROOT)))
    else:
        missing.append(str(t.relative_to(ROOT)))

print(f"plan={len(targets)} deleted={len(deleted)} missing={len(missing)}")
for m in missing:
    print("MISSING:", m)

# 删后余量核对
mine_left = sorted(p.name for p in (ROOT / "src" / "mine").glob("*.py"))
submit_left = sorted(p.name for p in (ROOT / "src" / "submit").glob("*.py"))
tools_left = sorted(p.name for p in (ROOT / "src" / "tools").glob("*.py"))
print("mine_left(%d): %s" % (len(mine_left), ", ".join(mine_left)))
print("submit_left(%d): %s" % (len(submit_left), ", ".join(submit_left)))
print("tools_left(%d): %s" % (len(tools_left), ", ".join(tools_left)))
