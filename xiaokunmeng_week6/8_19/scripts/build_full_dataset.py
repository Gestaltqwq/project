# -*- coding: utf-8 -*-
"""子集人工标注(0基33类) 映射到 8_19 的 10 类, 合并构建扩充训练集.
- 子集: 运营高速公路子集 (571图/569标注, ~6672框)
- 映射: 只保留属于 8_19 10类的框, 其余类别框丢弃
- 只保留至少含 1 个映射框的图片
- 与 8_19 的 val 8 张做 md5 去重, 防止数据泄漏
- 输出: 8_19/yolo_dataset_full/ (images|labels / train|val), data_full.yaml
"""
import hashlib
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # 8_19
SUB = Path(r"C:\Users\LENOVO\Downloads\运营高速公路子集")

# 8_19 的 10 类 (0基)
CLS10 = ["anti_collision_bucket","bridge_bearing","fire_box","lane_sign","led_screen",
         "parking","roadside_plant","toll_booth","tunnel_entrance","warning_sign"]
# 子集 33 类 (0基, data.yaml) -> 8_19 10类 id
MAP = {0:7, 5:3, 6:0, 10:2, 13:4, 16:8, 23:6, 26:9, 30:5, 31:1}

DST = ROOT / "yolo_dataset_full"

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    if DST.exists():
        shutil.rmtree(DST)
    for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
        (DST / sub).mkdir(parents=True, exist_ok=True)

    # 1) 8_19 原 train/val 全部图片 md5 (防重复/防泄漏)
    all_md5 = set()
    for sub in ["train", "val"]:
        for p in (ROOT / "yolo_dataset" / "images" / sub).iterdir():
            all_md5.add(md5(p))
    # 8_19 原 train 42 张直接复制
    n_orig = 0
    for p in sorted((ROOT / "yolo_dataset" / "images" / "train").iterdir()):
        shutil.copy(p, DST / "images" / "train" / p.name)
        shutil.copy(ROOT / "yolo_dataset" / "labels" / "train" / (p.stem + ".txt"),
                    DST / "labels" / "train" / (p.stem + ".txt"))
        n_orig += 1

    # 2) 子集映射
    n_img, n_box, n_skip_val, n_empty = 0, 0, 0, 0
    for lbl in sorted((SUB / "labels").iterdir()):
        img_png = SUB / "images" / (lbl.stem + ".png")
        img_jpg = SUB / "images" / (lbl.stem + ".jpg")
        img = img_png if img_png.exists() else img_jpg
        if not img.exists():
            continue
        if md5(img) in all_md5:
            n_skip_val += 1
            continue
        boxes = []
        for line in lbl.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) < 5:
                continue
            c = int(parts[0])
            if c in MAP:
                boxes.append(f"{MAP[c]} {' '.join(parts[1:5])}")
        if not boxes:
            n_empty += 1
            continue
        shutil.copy(img, DST / "images" / "train" / img.name)
        (DST / "labels" / "train" / (lbl.stem + ".txt")).write_text(
            "\n".join(boxes) + "\n", encoding="utf-8")
        n_img += 1
        n_box += len(boxes)

    # 3) val 8 张复制
    for p in sorted((ROOT / "yolo_dataset" / "images" / "val").iterdir()):
        shutil.copy(p, DST / "images" / "val" / p.name)
        shutil.copy(ROOT / "yolo_dataset" / "labels" / "val" / (p.stem + ".txt"),
                    DST / "labels" / "val" / (p.stem + ".txt"))

    # 4) data_full.yaml
    yaml = (f"path: {str(DST).replace(os.sep, '/')}\n"
            f"train: images/train\nval: images/val\n"
            f"nc: {len(CLS10)}\n"
            f"names:\n" + "".join(f"  {i}: {n}\n" for i, n in enumerate(CLS10)))
    (ROOT / "data_full.yaml").write_text(yaml, encoding="utf-8")

    train_n = len(list((DST / "images" / "train").iterdir()))
    val_n = len(list((DST / "images" / "val").iterdir()))
    print(f"8_19 原始训练图: {n_orig}")
    print(f"子集映射图: {n_img} (框 {n_box}, 与val重复跳过 {n_skip_val}, 无映射框丢弃 {n_empty})")
    print(f"新训练集: {train_n} 图, 验证集: {val_n} 图")
    print("data_full.yaml written")

if __name__ == "__main__":
    main()
