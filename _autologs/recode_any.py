import sys
src, dst = sys.argv[1], sys.argv[2]
raw = open(src, "rb").read()
txt = None
for enc in ("utf-16", "utf-8-sig", "utf-8", "gbk"):
    try:
        txt = raw.decode(enc)
        break
    except Exception:
        continue
open(dst, "w", encoding="utf-8").write(txt)
print("decoded", src, "with", enc)
