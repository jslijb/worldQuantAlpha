import subprocess
for i in range(3):
    r = subprocess.run(["git", "rev-list", "--count", "origin/main..main"], cwd=r"D:\Python\worldquant", capture_output=True, text=True)
    n = r.stdout.strip()
    if n == "0":
        print("PUSH OK (ahead=0)")
        break
    p = subprocess.run(["D:/ProgramData/Miniforge3/envs/bigmodel/python.exe", "D:/Python/worldquant/src/ops/git_snapshot.py", "--push-only", "--allow-public"], cwd=r"D:\Python\worldquant", capture_output=True, text=True, timeout=180)
    print(f"attempt {i+1}: ahead={n}, push rc={p.returncode}")
else:
    print("STILL UNPUSHED after 3 retries")
