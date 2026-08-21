# -*- coding: utf-8 -*-
"""构建 YOLO 数据集: 50 张 4K 高速图片, 85/15 固定随机划分 train/val."""
import os
import shutil
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # 8_19
IMG_SRC = ROOT / "images"
LBL_SRC = ROOT / "labels"
DST = ROOT / "yolo_dataset"

def clean_dst():
    if DST.exists():
        shutil.rmtree(DST)
    for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
        (DST / sub).mkdir(parents=True, exist_ok=True)

def copy_split(names, split_name):
    for n in names:
        img = IMG_SRC / (n + ".png")
        if not img.exists():
            img = IMG_SRC / (n + ".jpg")
        lbl = LBL_SRC / (n + ".txt")
        shutil.copy(img, DST / "images" / split_name / img.name)
        shutil.copy(lbl, DST / "labels" / split_name / (n + ".txt"))

def main():
    random.seed(42)
    bases = sorted(p.stem for p in LBL_SRC.glob("*.txt"))
    # 保证每个类别至少 1 个框进入训练集: 直接全量随机 85/15
    random.shuffle(bases)
    n_val = max(1, round(len(bases) * 0.15))
    val = set(bases[:n_val])
    train = [b for b in bases if b not in val]
    val = sorted(val)
    print(f"total={len(bases)} train={len(train)} val={len(val)}")
    clean_dst()
    copy_split(train, "train")
    copy_split(val, "val")
    # data.yaml
    names = [l.strip() for l in (ROOT / "classes.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    yaml = (f"path: {str(DST).replace(os.sep, '/')}\n"
            f"train: images/train\nval: images/val\n"
            f"nc: {len(names)}\n"
            f"names:\n" + "".join(f"  {i}: {n}\n" for i, n in enumerate(names)))
    (ROOT / "data.yaml").write_text(yaml, encoding="utf-8")
    print("data.yaml written:", len(names), "classes")
    (ROOT / "train_split.txt").write_text("\n".join(sorted(train)), encoding="utf-8")
    (ROOT / "val_split.txt").write_text("\n".join(val), encoding="utf-8")

if __name__ == "__main__":
    main()
