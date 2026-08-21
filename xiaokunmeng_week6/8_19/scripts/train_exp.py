# -*- coding: utf-8 -*-
"""YOLOv8 微调实验运行器: 记录 loss 变化, 汇总指标, 生成 loss 趋势图."""
import sys
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"
RUNS.mkdir(exist_ok=True)

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def plot_loss_trend(csv_path, out_png, title):
    df = pd.read_csv(csv_path)
    ep = df["epoch"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    axes[0].plot(ep, df["train/box_loss"], label="train/box_loss", color="#d62728")
    axes[0].plot(ep, df["train/cls_loss"], label="train/cls_loss", color="#1f77b4")
    axes[0].plot(ep, df["train/dfl_loss"], label="train/dfl_loss", color="#2ca02c")
    axes[0].set_title(title + " - Train Loss")
    axes[0].set_xlabel("epoch")
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    axes[1].plot(ep, df["val/box_loss"], label="val/box_loss", color="#d62728")
    axes[1].plot(ep, df["val/cls_loss"], label="val/cls_loss", color="#1f77b4")
    axes[1].plot(ep, df["val/dfl_loss"], label="val/dfl_loss", color="#2ca02c")
    axes[1].set_title(title + " - Val Loss")
    axes[1].set_xlabel("epoch")
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"[loss trend saved] {out_png}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True)
    ap.add_argument("--data", default="data.yaml")
    ap.add_argument("--lr0", type=float, default=0.01)
    ap.add_argument("--box", type=float, default=7.5)
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--model", default="yolov8n.pt")
    ap.add_argument("--optimizer", default="SGD")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    data_path = ROOT / args.data
    print(f"=== Experiment [{args.name}] data={data_path} lr0={args.lr0} box={args.box} "
          f"epochs={args.epochs} imgsz={args.imgsz} model={args.model} optimizer={args.optimizer} ===", flush=True)

    model = YOLO(args.model)
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        lr0=args.lr0,
        box=args.box,
        optimizer=args.optimizer,
        seed=args.seed,
        project=str(RUNS),
        name=args.name,
        exist_ok=True,
        cache=True,
        patience=20,
        plots=True,
        verbose=True,
    )

    exp_dir = RUNS / args.name
    csv_path = exp_dir / "results.csv"
    if csv_path.exists():
        plot_loss_trend(csv_path, exp_dir / "loss_trend.png", args.name)

    # 汇总
    df = pd.read_csv(csv_path)
    best = df.loc[df["metrics/mAP50-95(B)"].idxmax()]
    last = df.iloc[-1]
    print("\n===== SUMMARY =====", flush=True)
    print(f"best_epoch={int(best['epoch'])} mAP50={best['metrics/mAP50(B)']:.4f} "
          f"mAP50-95={best['metrics/mAP50-95(B)']:.4f} P={best['metrics/precision(B)']:.4f} "
          f"R={best['metrics/recall(B)']:.4f}", flush=True)
    print(f"last_epoch={int(last['epoch'])} train/box={last['train/box_loss']:.4f} "
          f"train/cls={last['train/cls_loss']:.4f} train/dfl={last['train/dfl_loss']:.4f}", flush=True)
    print(f"val_box={last['val/box_loss']:.4f} val_cls={last['val/cls_loss']:.4f} "
          f"val_dfl={last['val/dfl_loss']:.4f}", flush=True)
    with open(RUNS / f"{args.name}_summary.txt", "w", encoding="utf-8") as f:
        f.write(f"name={args.name}\nbest_epoch={int(best['epoch'])}\n"
                f"mAP50={best['metrics/mAP50(B)']:.4f}\nmAP50-95={best['metrics/mAP50-95(B)']:.4f}\n"
                f"P={best['metrics/precision(B)']:.4f}\nR={best['metrics/recall(B)']:.4f}\n"
                f"last_train_box={last['train/box_loss']:.4f}\nlast_train_cls={last['train/cls_loss']:.4f}\n"
                f"last_train_dfl={last['train/dfl_loss']:.4f}\n"
                f"last_val_box={last['val/box_loss']:.4f}\nlast_val_cls={last['val/cls_loss']:.4f}\n"
                f"last_val_dfl={last['val/dfl_loss']:.4f}\n")


if __name__ == "__main__":
    main()
