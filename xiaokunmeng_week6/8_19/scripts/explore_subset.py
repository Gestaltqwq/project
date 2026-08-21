# -*- coding: utf-8 -*-
"""探查子集数据: 重复度(md5), 标注配对, 类别分布, 与8_19的10类映射; 并验证 backend COCO 模型预测效果."""
import hashlib
import sys
from pathlib import Path
from collections import Counter
from ultralytics import YOLO

SUB = Path(r"C:\Users\LENOVO\Downloads\运营高速公路子集")
IMG = SUB / "images"
LBL = SUB / "labels"
BACKEND_PT = Path(r"D:\label\my_yolo_backend\yolov8n.pt")

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    # 1) 重复度
    imgs = sorted(IMG.iterdir())
    hashes = {}
    dup = 0
    for p in imgs:
        h = md5(p)
        if h in hashes:
            dup += 1
        else:
            hashes[h] = p
    print(f"images={len(imgs)} 唯一(按md5)={len(hashes)} 重复={dup}")

    # 2) 配对
    lbls = {p.stem for p in LBL.iterdir()}
    stems = {p.stem for p in imgs}
    print(f"labels={len(lbls)} 无标注图片={len(stems - lbls)} 无图标注={len(lbls - stems)}")

    # 3) 类别分布(33类体系)
    cnt = Counter()
    for p in LBL.iterdir():
        for line in p.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if parts:
                cnt[int(parts[0])] += 1
    names33 = [l.strip() for l in (SUB / "classes.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    # classes.txt 是 "id name # 中文" 格式
    nm = {}
    for l in (SUB / "classes.txt").read_text(encoding="utf-8").splitlines():
        l = l.strip()
        if not l or l.startswith("YOLO") or l.startswith("格式") or l.startswith("==="):
            continue
        parts = l.replace("#", "").split()
        if len(parts) >= 2 and parts[0].isdigit():
            nm[int(parts[0])] = parts[1]
    print("--- 子集33类分布 ---")
    for c in sorted(cnt):
        print(f"  {c:2d} {nm.get(c, '?'):24s} {cnt[c]}")

    # 4) 映射到 8_19 的 10 类
    map_10 = {0:"toll_booth",5:"lane_sign",6:"anti_collision_bucket",10:"fire_box",13:"led_screen",
              16:"tunnel_entrance",23:"roadside_plant",26:"warning_sign",30:"parking",31:"bridge_bearing"}
    mapped = Counter()
    for c, n in cnt.items():
        if c in map_10:
            mapped[map_10[c]] += n
    print("--- 可映射到8_19 10类的框数 ---", sum(mapped.values()))
    for k, v in mapped.most_common():
        print(f"  {k:24s} {v}")

    # 5) COCO 模型在子集上的预测效果(前2张)
    print("--- backend COCO 模型预测效果 ---")
    m = YOLO(str(BACKEND_PT))
    for p in sorted(IMG.iterdir())[:2]:
        r = m.predict(str(p), conf=0.3, imgsz=640, verbose=False)[0]
        print(f"{p.name}: {len(r.boxes)} dets ->", 
              [f"{m.names[int(b.cls)]}:{float(b.conf):.2f}" for b in r.boxes][:8])

if __name__ == "__main__":
    main()
