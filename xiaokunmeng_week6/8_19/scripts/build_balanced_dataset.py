# -*- coding: utf-8 -*-
"""类别平衡子采样: 从子集映射的 484 张图中, 对大类别(toll_booth/lane_sign等)按框数 cap 抽样,
缓解收费站场景主导, 构建平衡数据集 yolo_dataset_bal (8_19 42 张 + 平衡子集图)."""
import shutil
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "yolo_dataset_full"
BAL = ROOT / "yolo_dataset_bal"

# 每类框数上限 (8_19 原始训练已有: toll 91? 实际原始42训练框: toll~78? 用 cap 控制子集部分)
CAP = {7: 250, 3: 250, 9: 250, 4: 250}   # toll_booth, lane_sign, warning_sign, led_screen
# 其余类不限制 (fire_box 108, anti_collision_bucket 101, roadside_plant 108, tunnel_entrance 11, bridge_bearing 2)

def main():
    if BAL.exists():
        shutil.rmtree(BAL)
    for sub in ["images/train", "images/val", "labels/train", "labels/val"]:
        (BAL / sub).mkdir(parents=True, exist_ok=True)

    # 复制 8_19 原始 42 训练图
    for p in sorted((FULL / "images" / "train").iterdir()):
        # 只复制原 42 张: 判断 labels 是否在原始集 -> 用 yolo_dataset 对照
        pass

    # 更直接: 从 yolo_dataset (42图) 复制
    for p in sorted((ROOT / "yolo_dataset" / "images" / "train").iterdir()):
        shutil.copy(p, BAL / "images" / "train" / p.name)
        shutil.copy(ROOT / "yolo_dataset" / "labels" / "train" / (p.stem + ".txt"),
                    BAL / "labels" / "train" / (p.stem + ".txt"))

    # 子集图: 统计每张图的类别框数, 贪心保留直到各类达 cap
    sub_imgs = sorted((FULL / "images" / "train").iterdir())
    kept, counts, n_img = [], Counter(), 0
    for p in sub_imgs:
        lbl = FULL / "labels" / "train" / (p.stem + ".txt")
        if not lbl.exists():
            continue
        img_cnt = Counter()
        for line in lbl.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if parts:
                img_cnt[int(parts[0])] += 1
        # 是否超 cap
        if any(counts[c] + n >= CAP.get(c, 10**9) for c, n in img_cnt.items()):
            continue
        shutil.copy(p, BAL / "images" / "train" / p.name)
        shutil.copy(lbl, BAL / "labels" / "train" / (p.stem + ".txt"))
        counts.update(img_cnt)
        n_img += 1

    # val 8 张
    for p in sorted((ROOT / "yolo_dataset" / "images" / "val").iterdir()):
        shutil.copy(p, BAL / "images" / "val" / p.name)
        shutil.copy(ROOT / "yolo_dataset" / "labels" / "val" / (p.stem + ".txt"),
                    BAL / "labels" / "val" / (p.stem + ".txt"))

    names = ["anti_collision_bucket","bridge_bearing","fire_box","lane_sign","led_screen",
             "parking","roadside_plant","toll_booth","tunnel_entrance","warning_sign"]
    total = 0
    print(f"新增子集图: {n_img}")
    for c in range(10):
        print(f"  {c} {names[c]:22s} {counts[c]}")
        total += counts[c]
    print(f"子集部分框总数: {total}")
    n_train = len(list((BAL / "images" / "train").iterdir()))
    print(f"平衡训练集总图数: {n_train}")

    # data_bal.yaml
    import os
    yaml = (f"path: {str(BAL).replace(os.sep, '/')}\n"
            f"train: images/train\nval: images/val\nnc: 10\nnames:\n"
            + "".join(f"  {i}: {n}\n" for i, n in enumerate(names)))
    (ROOT / "data_bal.yaml").write_text(yaml, encoding="utf-8")
    print("data_bal.yaml written")

if __name__ == "__main__":
    main()
