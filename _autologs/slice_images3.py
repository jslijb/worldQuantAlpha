# -*- coding: utf-8 -*-
from PIL import Image
import os
src_dir = r"C:\Users\jslij\.workbuddy\clipboard-images"
out_dir = r"D:\Python\worldquant\_autologs\insight_slices"
os.makedirs(out_dir, exist_ok=True)
fn = "clipboard-2026-09-19T15-33-48-341Z-acf68b41.jpg"
im = Image.open(os.path.join(src_dir, fn)).convert("RGB")
w, h = im.size
print("orig", w, h)
scale = 4
im2 = im.resize((w * scale, h * scale), Image.LANCZOS)
W, H = im2.size
chunk = 2200
i = 0
y = 0
while y < H:
    crop = im2.crop((0, y, W, min(y + chunk, H)))
    op = os.path.join(out_dir, f"z_{i:02d}.png")
    crop.save(op)
    i += 1
    y += chunk - 150
print("slices:", i, "size", W, H)
