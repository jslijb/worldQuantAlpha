#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""抓取 BRAIN 平台 Learn 视频课程元数据（video-courses API）。

用途：定位 Learn 课程视频的 Vidyard UUID 与字幕轨，供备考归档使用。
只读取课程元数据，不触碰模拟/提交接口。
"""
import json
import os
import pathlib
import sys

import requests

# --- 向上定位项目根 ---
_p = pathlib.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / "brain_credentials.txt").exists():
        os.chdir(_d)
        break

BASE = "https://api.worldquantbrain.com"
OUT = pathlib.Path("_autologs/learn_video")


def login() -> requests.Session:
    user, pwd = json.loads(pathlib.Path("brain_credentials.txt").read_text(encoding="utf-8-sig"))
    s = requests.Session()
    s.auth = (user, pwd)
    r = s.post(f"{BASE}/authentication", timeout=30)
    r.raise_for_status()
    return s


def main() -> int:
    s = login()
    OUT.mkdir(parents=True, exist_ok=True)
    # ⚠️ 默认只返 10 条，必须显式带 limit，否则会漏掉后半程课程组
    r = s.get(f"{BASE}/video-courses", params={"limit": 100}, timeout=60)
    print("GET /video-courses ->", r.status_code, len(r.content), "bytes")
    if r.status_code != 200:
        print(r.text[:500])
        return 1
    data = r.json()
    (OUT / "video_courses.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # 打印结构概览
    if isinstance(data, dict):
        print("顶层键：", list(data.keys()))
    items = data.get("results", data) if isinstance(data, dict) else data
    n_v = sum(len(c.get("videos", [])) for c in items)
    n_t = sum(1 for c in items for v in c.get("videos", []) if v.get("transcript"))
    print(f"课程组：{len(items)}｜视频：{n_v}｜带字幕：{n_t}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
