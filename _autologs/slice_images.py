# -*- coding: utf-8 -*-
from PIL import Image
import os
src_dir = r"C:\Users\jslij\.workbuddy\clipboard-images"
out_dir = r"D:\Python\worldquant\_autologs\insight_slices"
os.makedirs(out_dir, exist_ok=True)
files = ["clipboard-2026-09-19T15-33-48-338Z-500ffc4f.png",
         "clipboard-2026-09-19T15-33-48-341Z-acf68b41.jpg"]
for fn in files:
    p = os.path.join(src_dir, fn)
    im = Image.open(p)
    w, h = im.size
    tag = "img2" if "500ffc4f" in fn else "img3"
    # slice into chunks of 1600px height with 100px overlap, upscale x2 if narrow
    chunk = 1600
    i = 0
    y = 0
    while y < h:
        box = (0, y, w, min(y + chunk, h))
        crop = im.crop(box)
        if w < 900:
            crop = crop.resize((w * 2, crop.size[1] * 2), Image.LANCZOS)
        op = os.path.join(out_dir, f"{tag}_{i:02d}.png")
        crop.save(op)
        i += 1
        y += chunk - 100
    print(tag, w, h, "slices:", i)
print("done")
