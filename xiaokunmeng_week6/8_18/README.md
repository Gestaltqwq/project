# bert-base-chinese NER 命名实体识别

使用 `bert-base-chinese` 在 **wikiann 中文数据集** 上微调训练命名实体识别（NER）模型，打印精确率 / 召回率 / F1 评估指标，并提供推理演示脚本。

## 数据集

- 原始 `wikiann` 仓库已从 Hugging Face Hub 移除，本项目使用官方迁移版 **`unimelb-nlp/wikiann`**（`zh` 配置）。
- 划分：train 20,000 / validation 10,000 / test 10,000。
- 标签：`O, B-PER, I-PER, B-ORG, I-ORG, B-LOC, I-LOC`（人名 / 组织 / 地点）。

## 环境要求

```bash
pip install torch transformers datasets seqeval
```

- Python 3.12、transformers 5.x、PyTorch（CUDA 可用时自动用 GPU + fp16 训练）。
- 网络受限时可加 `HF_DATASETS_OFFLINE=1` 使用本地缓存（离线模式跳过联网检查）。

## 训练

```bash
python train_ner.py          # 基础版：max_len=128、3 epochs
python train_ner_v2.py       # 加强版（推荐）：max_len=256、5 epochs、按验证集 F1 自动选最佳
python finetune_ner.py       # 精调版：从 ./bert-ner-wikiann-final 低学习率继续训练 2 epochs
```

训练完成后自动：

- 每个 epoch 结束打印验证集指标，训练结束打印最终评估与详细分类报告；
- 将最佳模型保存至 `./bert-ner-wikiann-final`。

> 注意：脚本按 8GB 显存设定 batch（train 16 / eval 8 + 分段累积），训练时请关闭其他占用显存的程序（如浏览器硬件加速、其他训练任务），避免评估阶段 CUDA OOM。

## 评估

```bash
python evaluate_model.py                       # 默认评估最优 checkpoint
python evaluate_model.py ./bert-ner-wikiann-final   # 指定模型目录
```

在验证集与测试集上打印 micro P / R / F1 和按实体类型（LOC / ORG / PER）的详细分类报告。

## 推理演示

```bash
python predict_ner.py "姚明曾效力于休斯敦火箭队。"
python predict_ner.py          # 运行内置示例句子
```

示例输出：

```
句子: 姚明曾效力于休斯敦火箭队，是中国著名的篮球运动员。
实体: [('休斯敦火箭队', 'ORG')]
```

## 评估结果（Test 集，同一评估协议对比）

| 版本 | 说明 | micro P | micro R | micro F1 |
|---|---|---|---|---|
| V1 | 3 epochs，max_len=128 | 0.7724 | 0.8095 | 0.7905 |
| V1+精调 | 再训 2 epochs（lr=1e-5） | 0.7740 | 0.8227 | 0.7976 |
| **V2（最终模型）** | **5 epochs，max_len=256，自动选最佳** | **0.7844** | **0.8307** | **0.8069** |

V2 最终模型 Test 集按实体类型：

| 类型 | precision | recall | f1 | support |
|---|---|---|---|---|
| LOC（地点） | 0.8010 | 0.8544 | 0.8268 | 4451 |
| ORG（组织） | 0.7157 | 0.7610 | 0.7377 | 4076 |
| PER（人名） | 0.8379 | 0.8762 | 0.8566 | 3918 |
| micro avg | 0.7844 | 0.8307 | 0.8069 | 12445 |

Validation 集：micro P 0.7791 / R 0.8289 / F1 0.8032。

训练超参（V2）：lr=2e-5、warmup 0.1、batch 8 + 梯度累积 2（等效 16）、5 epochs、max_len=256、weight_decay=0.01、fp16、seed=42。优化点：max_len 128→256（覆盖 99% 样本，此前 2.2% 长句实体被截断）、epoch 数 3→5 并按验证集 F1 自动选取最优（验证集 F1 全程上升至 epoch 5）。

## 目录结构

```
├── train_ner.py        # 基础训练脚本（3 epoch，max_len=128）
├── train_ner_v2.py     # 加强版训练脚本（5 epoch，max_len=256，自动选最佳）
├── finetune_ner.py     # 精调脚本（低学习率继续训练）
├── evaluate_model.py   # 独立评估脚本（验证集/测试集指标）
├── predict_ner.py      # 推理演示脚本
├── bert-ner-wikiann/   # V1 训练 checkpoint（gitignore，不入库）
├── bert-ner-wikiann-v2/  # V2 训练 checkpoint（gitignore，不入库）
├── bert-ner-wikiann-final/  # 最终模型（gitignore，不入库）
└── README.md
```

> 模型权重约 400MB，超过 GitHub 单文件 100MB 限制，故不入库；如需发布模型可上传至 Hugging Face Hub。
