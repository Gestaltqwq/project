# -*- coding: utf-8 -*-
"""汇总所有实验: 指标表 + 对比图 (loss 趋势 / mAP 对比)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

EXPS = ["e1_base", "e2_lr_low", "e3_lr_high", "e4_box_low", "e5_box_high", "e6_data_x3", "e7_subset_full", "e8_bal_subset", "e9_bal_aug", "e10_bal_lrsmall"]
CONFIG = {
    "e1_base":    ("data.yaml",  0.01, 7.5),
    "e2_lr_low":  ("data.yaml",  0.003, 7.5),
    "e3_lr_high": ("data.yaml",  0.03, 7.5),
    "e4_box_low": ("data.yaml",  0.01, 5.0),
    "e5_box_high":("data.yaml",  0.01, 12.0),
    "e6_data_x3": ("data_x3.yaml", 0.01, 5.0),
    "e7_subset_full": ("data_full.yaml", 0.01, 5.0),
    "e8_bal_subset": ("data_bal.yaml", 0.01, 5.0),
    "e9_bal_aug": ("yolo_dataset_bal_x3.yaml", 0.01, 5.0),
    "e10_bal_lrsmall": ("data_bal.yaml", 0.005, 5.0),
}

def main():
    rows = []
    for e in EXPS:
        summary = RUNS / f"{e}_summary.txt"
        csvp = RUNS / e / "results.csv"
        if not (summary.exists() and csvp.exists()):
            print(f"[skip] {e} missing")
            continue
        kv = {}
        for line in summary.read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            kv[k] = v
        data, lr0, box = CONFIG[e]
        dname = {"data.yaml": "42图(全量)", "data_x3.yaml": "313图(增强3x)",
                 "data_full.yaml": "526图(子集映射)",
                 "data_bal.yaml": "217图(平衡子集)",
                 "yolo_dataset_bal_x3.yaml": "1500+图(平衡+增强)"}.get(data, data)
        rows.append({
            "实验编号": e,
            "数据集": dname,
            "lr0": lr0,
            "box": box,
            "best_epoch": int(kv["best_epoch"]),
            "loss(train/box)": round(float(kv["last_train_box"]), 4),
            "loss(train/cls)": round(float(kv["last_train_cls"]), 4),
            "loss(val/box)": round(float(kv["last_val_box"]), 4),
            "mAP50": round(float(kv["mAP50"]), 4),
            "mAP50-95": round(float(kv["mAP50-95"]), 4),
            "P": round(float(kv["P"]), 4),
            "R": round(float(kv["R"]), 4),
        })
    df = pd.DataFrame(rows)
    df.to_csv(RUNS / "experiment_summary.csv", index=False, encoding="utf-8-sig")
    print(df.to_string(index=False))

    # ---- 对比图1: 各实验 val/box_loss 趋势 ----
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    for e, c in zip(EXPS, colors):
        csvp = RUNS / e / "results.csv"
        if not csvp.exists():
            continue
        d = pd.read_csv(csvp)
        axes[0].plot(d["epoch"], d["train/box_loss"], color=c, label=e)
        axes[1].plot(d["epoch"], d["val/box_loss"], color=c, label=e)
    axes[0].set_title("Train box_loss 对比")
    axes[1].set_title("Val box_loss 对比")
    for ax in axes:
        ax.set_xlabel("epoch"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(RUNS / "compare_box_loss.png", dpi=150)
    plt.close()

    # ---- 对比图2: 各实验 val/cls_loss ----
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.5))
    for e, c in zip(EXPS, colors):
        csvp = RUNS / e / "results.csv"
        if not csvp.exists():
            continue
        d = pd.read_csv(csvp)
        axes[0].plot(d["epoch"], d["train/cls_loss"], color=c, label=e)
        axes[1].plot(d["epoch"], d["val/cls_loss"], color=c, label=e)
    axes[0].set_title("Train cls_loss 对比")
    axes[1].set_title("Val cls_loss 对比")
    for ax in axes:
        ax.set_xlabel("epoch"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(RUNS / "compare_cls_loss.png", dpi=150)
    plt.close()

    # ---- 对比图3: 指标柱状图 ----
    if len(df):
        fig, ax = plt.subplots(figsize=(10, 5))
        x = range(len(df))
        w = 0.18
        ax.bar([i - 1.5 * w for i in x], df["mAP50"], w, label="mAP50")
        ax.bar([i - 0.5 * w for i in x], df["mAP50-95"], w, label="mAP50-95")
        ax.bar([i + 0.5 * w for i in x], df["P"], w, label="P")
        ax.bar([i + 1.5 * w for i in x], df["R"], w, label="R")
        ax.set_xticks(list(x)); ax.set_xticklabels(df["实验编号"], rotation=15)
        ax.set_ylabel("score"); ax.legend(); ax.grid(alpha=0.3, axis="y")
        ax.set_title("各实验指标对比 (mAP50 / mAP50-95 / P / R)")
        plt.tight_layout()
        plt.savefig(RUNS / "compare_metrics_bar.png", dpi=150)
        plt.close()
    print("\n[figures saved] compare_box_loss.png / compare_cls_loss.png / compare_metrics_bar.png")

if __name__ == "__main__":
    main()
