# -*- coding: utf-8 -*-
import subprocess, os, time
os.chdir(r"D:\Python\worldquant")
out = []
r = subprocess.run(["git", "show", "--stat", "--oneline", "1e70a4e"], capture_output=True, text=True, encoding="utf-8", errors="replace")
out.append("SHOW 1e70a4e:\n" + (r.stdout or r.stderr))
for i in range(3):
    r = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ok = r.returncode == 0
    out.append(f"PUSH try{i+1}: rc={r.returncode} {(r.stdout or r.stderr).strip()[:200]}")
    if ok:
        break
    time.sleep(8)
r2 = subprocess.run(["git", "rev-list", "--count", "origin/main..main"], capture_output=True, text=True)
out.append("UNPUSHED=" + r2.stdout.strip())
with open(r"_autologs\git_push_retry_0919.out", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("done")
