# -*- coding: utf-8 -*-
"""跨场景泛化评估: 用各模型 best.pt 在子集未参与训练的新图上评估 (val 模式).
评估集: yolo_dataset_full 中未进入 yolo_dataset_bal 训练集的子集图.
"""
import os
import shutil
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "yolo_dataset_full"
BAL = ROOT / "yolo_dataset_bal"
EVAL = ROOT / "eval_holdout_set"

def main():
    if EVAL.exists():
        shutil.rmtree(EVAL)
    (EVAL / "images" / "val").mkdir(parents=True)
    (EVAL / "labels" / "val").mkdir(parents=True)
    bal_train = {p.name for p in (BAL / "images" / "train").iterdir()}
    n = 0
    for p in sorted((FULL / "images" / "train").iterdir()):
        if p.name in bal_train:
            continue
        shutil.copy(p, EVAL / "images" / "val" / p.name)
        lbl = FULL / "labels" / "train" / (p.stem + ".txt")
        if lbl.exists():
            shutil.copy(lbl, EVAL / "labels" / "val" / (p.stem + ".txt"))
        n += 1
    print(f"评估集: {n} 张子集新图")

    names = ["anti_collision_bucket","bridge_bearing","fire_box","lane_sign","led_screen",
             "parking","roadside_plant","toll_booth","tunnel_entrance","warning_sign"]
    yaml = (f"path: {str(EVAL).replace(os.sep, '/')}\ntrain: images/val\nval: images/val\nnc: 10\nnames:\n"
            + "".join(f"  {i}: {nm}\n" for i, nm in enumerate(names)))
    (ROOT / "data_holdout.yaml").write_text(yaml, encoding="utf-8")

    models = {
        "e6_data_x3(42图+增强)": ROOT / "runs" / "e6_data_x3" / "weights" / "best.pt",
        "e8_bal_subset(平衡217图)": ROOT / "runs" / "e8_bal_subset" / "weights" / "best.pt",
        "e10_bal_lrsmall(平衡+小lr)": ROOT / "runs" / "e10_bal_lrsmall" / "weights" / "best.pt",
    }
    for name, w in models.items():
        if not w.exists():
            print(f"[skip] {name}: weights missing")
            continue
        m = YOLO(str(w))
        r = m.val(data=str(ROOT / "data_holdout.yaml"), imgsz=640,
                  conf=0.001, iou=0.6, verbose=False, project=str(ROOT / "runs"),
                  name="eval_holdout", exist_ok=True, max_det=300)
        print(f"{name}: mAP50={r.box.map50:.4f} mAP50-95={r.box.map:.4f} "
              f"P={r.box.mp:.4f} R={r.box.mr:.4f}")

if __name__ == "__main__":
    main()
