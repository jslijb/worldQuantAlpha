# -*- coding: utf-8 -*-
from PIL import Image
import os
src = r"D:\Python\worldquant\_autologs\insight_slices"
# rebuild 4x full image
src_dir = r"C:\Users\jslij\.workbuddy\clipboard-images"
im = Image.open(os.path.join(src_dir, "clipboard-2026-09-19T15-33-48-341Z-acf68b41.jpg")).convert("RGB")
w, h = im.size
im2 = im.resize((w * 4, h * 4), Image.LANCZOS)
W, H = im2.size
# targeted bands (4x coords)
bands = [(0, 0, 500), (500, 400, 1200), (1200, 1100, 1800), (1800, 1700, 2250),
         (2250, 2150, 2900), (2900, 2800, 3500), (3500, 3400, 4100), (4100, 4000, 4700),
         (4700, 4600, 5300), (5300, 5200, 5900), (5900, 5800, 6500), (6500, 6400, 7100),
         (7100, 7000, 7700), (7700, 7600, 8400)]
for a, y0, y1 in bands:
    y0c = max(0, min(y0, H)); y1c = max(0, min(y1, H))
    if y1c <= y0c:
        continue
    crop = im2.crop((0, y0c, W, y1c))
    op = os.path.join(src, f"b_{a:02d}.png")
    crop.save(op)
print("W,H", W, H, "bands saved")
