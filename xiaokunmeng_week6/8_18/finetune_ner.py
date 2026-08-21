"""从最佳 checkpoint 继续微调 bert-base-chinese NER 模型（更低学习率，2 个 epoch），提升评估指标。"""
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

# 0. 从最佳 checkpoint 继续训练（保留已学到的权重）
BASE_CKPT = "./bert-ner-wikiann-final"
OUTPUT_DIR = "./bert-ner-wikiann-finetune2"

tokenizer = AutoTokenizer.from_pretrained(BASE_CKPT)
model = AutoModelForTokenClassification.from_pretrained(BASE_CKPT)
label_list = [model.config.id2label[i] for i in range(model.config.num_labels)]
print("标签列表:", label_list)

# 1. 加载 wikiann 中文数据集（离线模式用本地缓存）
dataset = load_dataset("unimelb-nlp/wikiann", "zh")

# 2. 预处理
def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"], truncation=True, padding=False, max_length=256,
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

tokenized_datasets = dataset.map(
    tokenize_and_align_labels,
    batched=True,
    remove_columns=dataset["train"].column_names,
)

data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

# 3. 评估指标
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

# 4. 训练参数：更低学习率，继续精调
training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=1e-5,             # 精调阶段降低学习率
    warmup_ratio=0.1,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=8,
    eval_accumulation_steps=4,
    num_train_epochs=2,             # 再训练 2 个 epoch
    weight_decay=0.01,
    logging_steps=50,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    fp16=True,
    seed=42,
    report_to="none",
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    processing_class=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# 5. 训练
trainer.train()

# 6. 最终评估
print("\n========== 微调后最终评估指标（验证集） ==========")
eval_result = trainer.evaluate()
for key, value in eval_result.items():
    if key != "eval_classification_report":
        print(f"{key}: {value:.4f}")
print("\n详细分类报告：")
print(eval_result.get("eval_classification_report", "未找到详细报告"))

# 7. 保存最终模型
model.save_pretrained("./bert-ner-wikiann-final")
tokenizer.save_pretrained("./bert-ner-wikiann-final")
print("\n最终模型已保存至 ./bert-ner-wikiann-final")
