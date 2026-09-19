# -*- coding: utf-8 -*-
import subprocess, os
os.chdir(r"D:\Python\worldquant")
r1 = subprocess.run(["git", "log", "--oneline", "-2"], capture_output=True, text=True, encoding="utf-8", errors="replace")
r2 = subprocess.run(["git", "rev-list", "--count", "origin/main..main"], capture_output=True, text=True)
r3 = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8", errors="replace")
with open(r"_autologs\git_verify_0919.out", "w", encoding="utf-8") as f:
    f.write("LOG:\n" + (r1.stdout or r1.stderr) + "\n")
    f.write("UNPUSHED=" + (r2.stdout or "?").strip() + "\n")
    f.write("DIRTY=" + str(len((r3.stdout or "").strip().splitlines())) + "\n")
print("done")
