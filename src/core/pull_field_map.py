# -*- coding: utf-8 -*-
"""pull_field_map.py —— 拉平台权威「字段 → 数据集」全量映射，落本地缓存。

## 为什么建这个（11-16 实测）

`src/core/atom.py:_load_field_map()` 只读 `data/alpha_quality_analysis/all_fields_*.json`
（26333 条），但这些缓存是**按当时拉的区域/期限**抓的，覆盖不全：
`beta_prediction_dispersion` / `forward_beta_risk` 等字段查不到归属 ⇒
`dataset_of()` 返回 None ⇒ `judge()` 判"无法判定数据集归属" ⇒ **ATOM 门误杀**。

另一个坑：`_grid/_field_ds_map.json`（13613 条）值是**数据集名不是 id**，
且 `beta_prediction_dispersion` 竟映射到 `forward_beta_risk`（明显错位一行）⇒ 不可用。

**唯一权威 = 平台 `GET /data-fields`**（每条带 `dataset.id`）。
本脚本按 region 全量拉，合并成 `{字段名: dataset_id}`，落：
    data/alpha_quality_analysis/field_ds_map.json   （新，权威）
并写一个 **region 分桶版**（修跨市场串味）：同一字段名在不同 region 可能属不同数据集，
合并表会取第一个命中 → 串味。故同时落：
    data/alpha_quality_analysis/field_ds_map_by_region.json
        {region: {字段名: dataset_id}}

用法：
    python src/core/pull_field_map.py --region USA --universe TOP3000
    python src/core/pull_field_map.py --region GLB --universe TOP3000
"""
import os as _os, io, sys, json, time, argparse, glob
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import requests

ap = argparse.ArgumentParser()
ap.add_argument('--region', default='USA')
ap.add_argument('--universe', default='TOP3000')
ap.add_argument('--delay', type=int, default=1)
ap.add_argument('--out', default=str(ROOT / 'data/alpha_quality_analysis/field_ds_map_by_region.json'))
ap.add_argument('--merge-out', default=str(ROOT / 'data/alpha_quality_analysis/field_ds_map.json'))
args = ap.parse_args()

CRED = tuple(json.load(io.open(ROOT / 'brain_credentials.txt')))


def sess():
    s = requests.Session()
    s.trust_env = False
    s.proxies = {'http': None, 'https': None}
    s.auth = CRED
    for _ in range(8):
        try:
            if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                return s
        except Exception:
            pass
        time.sleep(4)
    return None


def pull(s, region, universe, delay=1):
    tmpl = ('https://api.worldquantbrain.com/data-fields?'
            '&instrumentType=EQUITY&region=%s&delay=%d&universe=%s&limit=50&offset=%d')
    out = {}
    cnt = None
    off = 0
    # ★ 增量落盘：每 500 条写一次（11-16 实测：全量拉 USA 需 >8 分钟，
    #   进程被 timeout 切掉就一条不剩 ⇒ 改成边拉边存，中断也有产出）。
    part_p = ROOT / 'data/alpha_quality_analysis' / ('_fieldmap_partial_%s.json' % region)
    if part_p.exists():
        try:
            out = json.load(io.open(part_p, encoding='utf-8')) or {}
            print('  断点续拉：已有 %d 条' % len(out))
        except Exception:
            out = {}
    while True:
        url = tmpl % (region, delay, universe, off)
        data = None
        for att in range(5):
            try:
                r = s.get(url, timeout=90)
                j = r.json()
                if 'results' in j:
                    data = j
                    break
                msg = str(j.get('message', ''))
                if 'rate limit' in msg.lower():
                    time.sleep(10 * (att + 1))
                    continue
                time.sleep(3)
            except Exception:
                time.sleep(3)
        if data is None:
            print('  [warn] offset=%d 取数失败，跳过' % off)
            off += 50
            if cnt is not None and off >= cnt:
                break
            if off > 40000:
                break
            continue
        if cnt is None:
            cnt = data.get('count', 0)
            print('  平台报告总数 =', cnt, flush=True)
        res = data.get('results') or []
        for f in res:
            fid = f.get('id')
            ds = ((f.get('dataset') or {}) or {}).get('id')
            if fid and ds:
                out[fid.lower()] = ds
        off += 50
        if off % 500 == 0:
            io.open(part_p, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False))
            print('  已拉 %d/%s（入库 %d，已增量落盘）' % (off, cnt, len(out)), flush=True)
        if cnt and off >= cnt:
            break
        if off > 40000:
            break
    return out, cnt


def main():
    s = sess()
    if not s:
        print('认证失败，退出')
        sys.exit(1)
    print('拉取 region=%s universe=%s delay=%d ...' % (args.region, args.universe, args.delay))
    m, cnt = pull(s, args.region, args.universe, args.delay)
    print('完成：%s 共 %d 条（平台 count=%s）' % (args.region, len(m), cnt))

    # 合并进 by_region 文件
    p = Path(args.out)
    allm = {}
    if p.exists():
        try:
            allm = json.load(io.open(p, encoding='utf-8'))
        except Exception:
            allm = {}
    allm[args.region] = m
    io.open(p, 'w', encoding='utf-8').write(json.dumps(allm, ensure_ascii=False))
    print('写入 %s（区域数 %d）' % (p, len(allm)))

    # 合并版（后拉的区域不覆盖先拉的，仅补缺）
    pm = Path(args.merge_out)
    merged = {}
    if pm.exists():
        try:
            merged = json.load(io.open(pm, encoding='utf-8'))
        except Exception:
            merged = {}
    added = 0
    for k, v in m.items():
        if k not in merged:
            merged[k] = v
            added += 1
    io.open(pm, 'w', encoding='utf-8').write(json.dumps(merged, ensure_ascii=False))
    print('写入 %s：新增 %d 条，合计 %d 条' % (pm, added, len(merged)))


if __name__ == '__main__':
    main()
