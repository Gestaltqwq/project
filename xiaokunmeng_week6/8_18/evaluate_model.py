"""加载训练好的 NER 模型（默认取验证集 F1 最高的 checkpoint），在验证集/测试集上打印评估指标。"""
import sys
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification
from datasets import load_dataset
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

CHECKPOINT_DIR = sys.argv[1] if len(sys.argv) > 1 else "./bert-ner-wikiann/checkpoint-2500"
OUTPUT_DIR = "./bert-ner-wikiann-final"

# 1. 加载模型与 tokenizer
print(f"加载模型: {CHECKPOINT_DIR}")
tokenizer = AutoTokenizer.from_pretrained(CHECKPOINT_DIR)
model = AutoModelForTokenClassification.from_pretrained(CHECKPOINT_DIR)
model.eval()
label_list = [model.config.id2label[i] for i in range(model.config.num_labels)]
print("标签列表:", label_list)

# 2. 加载 wikiann 中文数据集
dataset = load_dataset("unimelb-nlp/wikiann", "zh")

# 3. 对齐标签
def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"], truncation=True, padding=False, max_length=128,
        is_split_into_words=True, return_tensors=None,
    )
    labels = []
    for i, label in enumerate(examples["ner_tags"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)
        previous_word_idx = None
        label_ids = []
        for word_idx in word_ids:
            if word_idx is None:
                label_ids.append(-100)
            elif word_idx != previous_word_idx:
                label_ids.append(label[word_idx])
            else:
                label_ids.append(-100)
            previous_word_idx = word_idx
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

tokenized = dataset.map(
    tokenize_and_align_labels, batched=True,
    remove_columns=["ner_tags"],  # 保留 tokens 列供推理时重新编码
)

# 4. 批量推理
def predict(split: str):
    inputs = tokenized[split]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    all_preds, all_labels = [], []
    bs = 8
    for start in range(0, len(inputs), bs):
        batch = inputs[start:start + bs]
        enc = tokenizer(
            batch["tokens"], truncation=True, padding=True, max_length=128,
            is_split_into_words=True, return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            logits = model(**enc).logits
        preds = logits.argmax(dim=-1).cpu().numpy()
        for pred_row, label_row in zip(preds, batch["labels"]):
            true = [label_list[l] for l in label_row if l != -100]
            pred = [label_list[p] for (p, l) in zip(pred_row, label_row) if l != -100]
            all_preds.append(pred)
            all_labels.append(true)
    return all_labels, all_preds

# 5. 打印指标
for split in ["validation", "test"]:
    print(f"\n========== {split.upper()} 集评估指标 ==========")
    true_labels, true_predictions = predict(split)
    print(f"precision (micro): {precision_score(true_labels, true_predictions, average='micro'):.4f}")
    print(f"recall    (micro): {recall_score(true_labels, true_predictions, average='micro'):.4f}")
    print(f"f1        (micro): {f1_score(true_labels, true_predictions, average='micro'):.4f}")
    print("\n详细分类报告（按实体类型）：")
    print(classification_report(true_labels, true_predictions, digits=4))

# 6. 输出为最终模型目录
print(f"\n保存最终模型至 {OUTPUT_DIR}")
model.save_pretrained(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)
print("完成。")
