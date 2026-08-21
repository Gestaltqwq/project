"""可视化工具：EDA 与模型评估图表 → base64 PNG

【工具层】纯函数，matplotlib 图表统一从这里输出。
所有图表返回 {image_base64, format:"png"}，由前端渲染。
"""
import os
import io
import base64

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix

plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

COLOR_NO, COLOR_YES = "#4A90D9", "#E74C3C"

# 本地图片保存目录（开发环境：同时落盘便于查看）
VIS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "visualizations")


def _to_base64(fig, name: str = "chart") -> dict:
    """Figure → {image_base64, format, local_path}

    - 返回 base64 供前端渲染
    - 同时保存到 data/visualizations/ 本地（开发环境用）
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    os.makedirs(VIS_DIR, exist_ok=True)
    local_path = os.path.join(VIS_DIR, f"{name}.png")
    fig.savefig(local_path, format="png", dpi=100)
    plt.close(fig)
    return {
        "image_base64": base64.b64encode(buf.getvalue()).decode(),
        "format": "png",
        "local_path": local_path,
    }


def eda_chart(df: pd.DataFrame, chart_type: str) -> dict:
    """EDA 图表：response_distribution / gender_response / age_distribution / premium_distribution"""
    fig, ax = plt.subplots(figsize=(8, 5))
    if chart_type == "response_distribution":
        df["response"].value_counts().plot(kind="bar", ax=ax, color=[COLOR_NO, COLOR_YES])
        ax.set_title("目标变量分布")
        ax.set_xticklabels(["未购买", "已购买"], rotation=0)
    elif chart_type == "gender_response":
        pd.crosstab(df["gender"], df["response"], normalize="index").plot(
            kind="bar", stacked=True, ax=ax)
        ax.set_title("性别 vs 购买")
        ax.set_ylabel("比例")
    elif chart_type == "age_distribution":
        df["age"].hist(bins=30, ax=ax, color=COLOR_NO, edgecolor="white")
        ax.set_title("年龄分布")
    elif chart_type == "premium_distribution":
        df["annual_premium"].hist(bins=30, ax=ax, color=COLOR_NO, edgecolor="white")
        ax.set_title("年保费分布")
    else:
        plt.close(fig)
        raise ValueError(f"未知图表类型: {chart_type}")
    fig.tight_layout()
    return _to_base64(fig, f"eda_{chart_type}")


def metrics_comparison_chart(experiments: list) -> dict:
    """三算法指标对比柱状图"""
    fig, ax = plt.subplots(figsize=(8, 5))
    names = [e["model_name"] for e in experiments]
    aucs = [e["roc_auc"] or 0 for e in experiments]
    ax.bar(range(len(names)), aucs, color=COLOR_NO)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=15)
    ax.set_xlabel("算法"); ax.set_ylabel("ROC-AUC"); ax.set_title("三算法指标对比")
    fig.tight_layout()
    return _to_base64(fig, "metrics_comparison")


def roc_chart_data(tpr: list, fpr: list) -> dict:
    """ROC 曲线（从落库数据复原，AI 方案 §2.8）"""
    from sklearn.metrics import auc as auc_score
    auc = float(auc_score(fpr, tpr))
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot(fpr, tpr, color=COLOR_YES, lw=2, label=f"AUC={auc:.4f}")
    ax.plot([0, 1], [0, 1], "k--", alpha=.6)
    ax.set_xlabel("假正率"); ax.set_ylabel("真正率")
    ax.set_title("ROC 曲线"); ax.legend()
    fig.tight_layout()
    return _to_base64(fig, "roc_curve")


def confusion_matrix_chart(y_true, y_pred, model_name: str) -> dict:
    """混淆矩阵热力图"""
    cm = confusion_matrix(y_true, y_pred)
    return confusion_matrix_data(cm, model_name)


def confusion_matrix_data(cm, model_name: str) -> dict:
    """混淆矩阵热力图（从落库数据复原）"""
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", ax=ax,
                xticklabels=["未购买", "已购买"], yticklabels=["未购买", "已购买"])
    ax.set_title(f"混淆矩阵 ({model_name})")
    ax.set_ylabel("真实值"); ax.set_xlabel("预测值")
    fig.tight_layout()
    return _to_base64(fig, f"confusion_matrix_{model_name}")


def feature_importance_chart(features: list, importance: list, model_name: str) -> dict:
    """特征重要性水平柱状图"""
    order = sorted(range(len(importance)), key=lambda i: importance[i], reverse=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh([features[i] for i in order], [importance[i] for i in order], color=COLOR_NO)
    ax.set_xlabel("重要性"); ax.set_title(f"特征重要性 ({model_name})")
    fig.tight_layout()
    return _to_base64(fig, f"feature_importance_{model_name}")
