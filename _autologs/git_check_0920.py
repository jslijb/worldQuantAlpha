import subprocess, os
os.chdir(r"D:\Python\worldquant")
def run(*a):
    r = subprocess.run(a, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (r.stdout or "") + (r.stderr or "")
out = open("_autologs/git_verify_0920.out", "w", encoding="utf-8")
print("LOG:", open("_autologs/git_snap_0920.log", "rb").read().decode("utf-16", "replace")[-600:], file=out)
print("AHEAD:", run("git", "rev-list", "--count", "origin/main..main").strip(), file=out)
print(run("git", "log", "--oneline", "-3"), file=out)
out.close()
print("done")
