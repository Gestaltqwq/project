# -*- coding: utf-8 -*-
"""统计: 子集图与 8_19 训练集重复情况 + 新全量数据集类别分布."""
import hashlib
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
SUB = Path(r"C:\Users\LENOVO\Downloads\运营高速公路子集")

def md5(p):
    h = hashlib.md5()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    train_md5 = {md5(p) for p in (ROOT / "yolo_dataset" / "images" / "train").iterdir()}
    sub_dup = 0
    for p in (SUB / "images").iterdir():
        if md5(p) in train_md5:
            sub_dup += 1
    print(f"子集图与 8_19 训练集(42) md5 重复: {sub_dup}")

    # 新数据集类别分布
    cnt = Counter()
    n_img = 0
    for lbl in (ROOT / "yolo_dataset_full" / "labels" / "train").iterdir():
        n_img += 1
        for line in lbl.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if parts:
                cnt[int(parts[0])] += 1
    names = ["anti_collision_bucket","bridge_bearing","fire_box","lane_sign","led_screen",
             "parking","roadside_plant","toll_booth","tunnel_entrance","warning_sign"]
    total = 0
    print(f"训练图: {n_img}")
    for c in range(10):
        print(f"  {c} {names[c]:22s} {cnt[c]}")
        total += cnt[c]
    print(f"总框数: {total}")

if __name__ == "__main__":
    main()
