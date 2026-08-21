import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_curve, auc,
    accuracy_score, precision_score, recall_score, f1_score
)

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
print("客户流失预测二分类模型")
np.random.seed(42)
n_samples = 1000

data = pd.DataFrame({
    '年龄': np.random.randint(18, 65, n_samples),
    '月消费金额': np.random.exponential(200, n_samples),
    '使用时长_月': np.random.randint(1, 60, n_samples),
    '投诉次数': np.random.poisson(0.5, n_samples),
    '是否流失': np.zeros(n_samples, dtype=int)
})

churn_prob = (
    -0.03 * (data['年龄'] - 40)
    - 0.004 * (data['月消费金额'] - 200)
    - 0.02 * (data['使用时长_月'] - 30)
    + 0.5 * data['投诉次数']
    + np.random.randn(n_samples) * 0.5
)
churn_prob = 1 / (1 + np.exp(-churn_prob))
data['是否流失'] = (churn_prob > 0.5).astype(int)

print(f"生成样本数: {n_samples}")
print(f"流失客户(正类): {data['是否流失'].sum()} ({data['是否流失'].mean()*100:.1f}%)")
print(f"留存客户(负类): {(1-data['是否流失']).sum()} ({(1-data['是否流失']).mean()*100:.1f}%)")

print("\n数据前5行:")
print(data.head())
print("\n数据统计描述:")
print(data.describe())

feature_cols = ['年龄', '月消费金额', '使用时长_月', '投诉次数']
X = data[feature_cols].values
y = data['是否流失'].values



X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)


print(f"训练集: {X_train.shape[0]} 样本")
print(f"测试集: {X_test.shape[0]} 样本")
print(f"训练集流失率: {y_train.mean()*100:.1f}%")
print(f"测试集流失率: {y_test.mean()*100:.1f}%")
print(f"特征数: {X_train.shape[1]}")
print(f"标准化后均值(≈0): {X_train_scaled.mean(axis=0).round(4)}")
print(f"标准化后方差(≈1): {X_train_scaled.std(axis=0).round(4)}")



models = {
    '逻辑回归': LogisticRegression(max_iter=1000, random_state=42),
    'SVM': SVC(kernel='rbf', probability=True, random_state=42),
    '随机森林': RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
}

results = []
predictions = {}
probabilities = {}

for name, model in models.items():
    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    predictions[name] = y_pred
    probabilities[name] = y_prob

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)

    print(f"  准确率(Accuracy):  {acc:.4f}")
    print(f"  精确率(Precision): {prec:.4f}")
    print(f"  召回率(Recall):    {rec:.4f}")
    print(f"  F1-Score:          {f1:.4f}")

    results.append({
        '模型': name,
        'Accuracy': round(acc, 4),
        'Precision': round(prec, 4),
        'Recall': round(rec, 4),
        'F1-Score': round(f1, 4)
    })


for name in models:
    print(f"模型: {name}")
    print(classification_report(y_test, predictions[name],
                                target_names=['留存(0)', '流失(1)'],
                                zero_division=0))
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
for ax, (name, _) in zip(axes, models.items()):
    cm = confusion_matrix(y_test, predictions[name])
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=ax,
                xticklabels=['预测留存', '预测流失'],
                yticklabels=['实际留存', '实际流失'])
    ax.set_title(f'{name} - 混淆矩阵')
    ax.set_ylabel('真实标签')
    ax.set_xlabel('预测标签')
plt.tight_layout()
plt.savefig('work2_混淆矩阵对比.png', dpi=100)
plt.close()
print("已保存: work2_混淆矩阵对比.png")

plt.figure(figsize=(10, 8))
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

for idx, (name, _) in enumerate(models.items()):
    fpr, tpr, _ = roc_curve(y_test, probabilities[name])
    roc_auc = auc(fpr, tpr)
    plt.plot(fpr, tpr, color=colors[idx], lw=2,
             label=f'{name} (AUC = {roc_auc:.4f})')
    print(f"{name} AUC = {roc_auc:.4f}")

plt.plot([0, 1], [0, 1], color='gray', lw=2, linestyle='--', label='随机猜测')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('假正率 (FPR)', fontsize=12)
plt.ylabel('真正率 (TPR)', fontsize=12)
plt.title('ROC曲线 - 三个模型对比', fontsize=14)
plt.legend(loc='lower right', fontsize=11)
plt.grid(alpha=0.3)
plt.savefig('work2_ROC曲线对比.png', dpi=100)
plt.close()
print("已保存: work2_ROC曲线对比.png")



df_results = pd.DataFrame(results).set_index('模型')
print(f"\n{df_results}")

fig, ax = plt.subplots(figsize=(12, 6))
metrics_plot = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
x = np.arange(len(metrics_plot))
width = 0.25
colors_bar = ['#FF6B6B', '#4ECDC4', '#45B7D1']

for i, (name, _) in enumerate(models.items()):
    values = [df_results.loc[name, m] for m in metrics_plot]
    bars = ax.bar(x + i * width, values, width, label=name, color=colors_bar[i])
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                f'{v:.3f}', ha='center', va='bottom', fontsize=9)

ax.set_xlabel('评估指标', fontsize=12)
ax.set_ylabel('分数', fontsize=12)
ax.set_title('三个模型效果综合对比', fontsize=14)
ax.set_xticks(x + width)
ax.set_xticklabels(metrics_plot, fontsize=11)
ax.legend(fontsize=11)
ax.set_ylim([0, 1.15])
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('work2_模型综合对比.png', dpi=100)
plt.close()
print("已保存: work2_模型综合对比.png")


best_model_name = df_results['F1-Score'].idxmax()

print(f"【最佳模型】: {best_model_name}")
print("各模型的表现")


for name in models:
    row = df_results.loc[name]
    print(f"  -> {name}:")
    print(f"     准确率={row['Accuracy']:.4f}, 精确率={row['Precision']:.4f}, "
          f"召回率={row['Recall']:.4f}, F1={row['F1-Score']:.4f}")
