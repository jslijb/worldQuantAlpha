import sys, os
os.chdir(r"D:\Python\worldquant")
src, dst = sys.argv[1], sys.argv[2]
raw = open(src, 'rb').read()
for enc in ('utf-8', 'utf-16', 'utf-16-le', 'gbk', 'cp936'):
    try:
        t = raw.decode(enc)
        if t.count('\x00') > len(t) * 0.05:
            continue
        open(dst, 'w', encoding='utf-8').write(t)
        print(f"decoded as {enc}, {len(t)} chars -> {dst}")
        break
    except Exception:
        continue
else:
    print("decode failed")
