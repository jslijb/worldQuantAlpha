raw = open(r"D:\Python\worldquant\_autologs\w213b_mix.log", "rb").read()
for enc in ("utf-16", "utf-8-sig", "utf-8", "gbk"):
    try:
        txt = raw.decode(enc)
        break
    except Exception:
        continue
open(r"D:\Python\worldquant\_autologs\w213b_mix.utf8.txt", "w", encoding="utf-8").write(txt)
print("decoded with", enc, "chars:", len(txt))
