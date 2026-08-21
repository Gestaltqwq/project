# -*- coding: utf-8 -*-
"""实例测试: 用最优模型对未参与训练的图片(验证集 + 数据集中随机抽测)推理并保存可视化结果."""
import sys
import shutil
from pathlib import Path
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "runs" / "e10_bal_lrsmall" / "weights" / "best.pt"
if not WEIGHTS.exists():
    WEIGHTS = ROOT / "runs" / "e6_data_x3" / "weights" / "best.pt"

VAL_IMGS = ROOT / "yolo_dataset" / "images" / "val"
OUT = ROOT / "inference_test"
OUT.mkdir(exist_ok=True)

def main():
    print("using weights:", WEIGHTS)
    model = YOLO(str(WEIGHTS))
    # 1) 验证集 8 张全部推理 (真值可对比)
    imgs = sorted(VAL_IMGS.glob("*"))
    for i, p in enumerate(imgs):
        res = model.predict(str(p), conf=0.25, imgsz=1280, save=False, verbose=False)
        for r in res:
            r.save(str(OUT / f"val_{i:02d}_{p.name}"))
    print(f"val inference done: {len(imgs)} imgs -> {OUT}")
    # 2) 测试集预测明细打印(前2张)
    for p in imgs[:2]:
        res = model.predict(str(p), conf=0.25, imgsz=1280, verbose=False)[0]
        print(f"\n-- {p.name} ({res.speed})")
        for box in res.boxes:
            cls = res.names[int(box.cls)]
            conf = float(box.conf)
            xyxy = [round(float(v)) for v in box.xyxy[0]]
            print(f"   {cls:20s} conf={conf:.3f} xyxy={xyxy}")

if __name__ == "__main__":
    main()
