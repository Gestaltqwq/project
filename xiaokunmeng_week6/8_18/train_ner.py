"""使用 bert-base-chinese 在 wikiann(中文) 上训练 NER 模型，并打印评估指标。"""
import numpy as np
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from datasets import load_dataset
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score

# 1. 加载 wikiann 中文 NER 数据集
#    原 "wikiann" 仓库已从 Hub 移除，官方迁移版为 "unimelb-nlp/wikiann"
dataset = load_dataset("unimelb-nlp/wikiann", "zh")

# 2. 自动获取标签列表
label_list = dataset["train"].features["ner_tags"].feature.names
id2label = {i: label for i, label in enumerate(label_list)}
label2id = {label: i for i, label in enumerate(label_list)}
num_labels = len(label_list)
print("标签列表:", label_list)  # ['O', 'B-PER', 'I-PER', 'B-LOC', 'I-LOC', 'B-ORG', 'I-ORG']

# 3. 加载 tokenizer 和模型（bert-base-chinese）
model_name = "bert-base-chinese"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(
    model_name,
    num_labels=num_labels,
    id2label=id2label,
    label2id=label2id,
)

# 4. 预处理函数（对齐标签到 token）
def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"],
        truncation=True,
        padding=False,
        max_length=128,
        is_split_into_words=True,
        return_tensors=None,
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

# 应用预处理
tokenized_datasets = dataset.map(
    tokenize_and_align_labels,
    batched=True,
    remove_columns=dataset["train"].column_names,
)

# 5. Data collator
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

# 6. 评估指标（micro P/R/F1 + 详细分类报告）
def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_labels = [[label_list[l] for l in label_row if l != -100] for label_row in labels]
    true_predictions = [
        [label_list[p] for (p, l) in zip(pred_row, label_row) if l != -100]
        for pred_row, label_row in zip(predictions, labels)
    ]

    return {
        "precision": precision_score(true_labels, true_predictions, average="micro"),
        "recall": recall_score(true_labels, true_predictions, average="micro"),
        "f1": f1_score(true_labels, true_predictions, average="micro"),
        "classification_report": classification_report(true_labels, true_predictions, digits=4),
    }

# 7. 训练参数
training_args = TrainingArguments(
    output_dir="./bert-ner-wikiann",
    eval_strategy="epoch",            # transformers 5.x：原 evaluation_strategy 已移除
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=8,
    eval_accumulation_steps=4,      # 分段累积评估输出，降低显存峰值
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    fp16=True,                        # RTX 4060 可用半精度加速
    seed=42,
    report_to="none",
)

# 8. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    processing_class=tokenizer,  # transformers 5.x：原 tokenizer 参数已改名为 processing_class
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# 9. 训练
trainer.train()

# 10. 最终评估
print("\n========== 最终评估指标（验证集） ==========")
eval_result = trainer.evaluate()
for key, value in eval_result.items():
    if key != "eval_classification_report":
        print(f"{key}: {value:.4f}")
print("\n详细分类报告：")
print(eval_result.get("eval_classification_report", "未找到详细报告"))

# 11. 保存模型
model.save_pretrained("./bert-ner-wikiann-final")
tokenizer.save_pretrained("./bert-ner-wikiann-final")
print("\n模型已保存至 ./bert-ner-wikiann-final")
