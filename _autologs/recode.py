import io
raw = open(r"D:\Python\worldquant\_autologs\w210_review.out", "rb").read()
for enc in ("utf-16", "utf-8-sig", "utf-8", "gbk"):
    try:
        txt = raw.decode(enc)
        break
    except Exception:
        continue
open(r"D:\Python\worldquant\_autologs\w210_review.utf8.txt", "w", encoding="utf-8").write(txt)
print("decoded with", enc, "lines:", txt.count("\n"))
