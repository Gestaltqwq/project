"""加强版训练：max_len=256（覆盖 99% 样本）、5 epochs、按验证集 F1 自动选择最佳 checkpoint。"""
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

# 1. 数据与标签
dataset = load_dataset("unimelb-nlp/wikiann", "zh")
label_list = dataset["train"].features["ner_tags"].feature.names
id2label = {i: label for i, label in enumerate(label_list)}
label2id = {label: i for i, label in enumerate(label_list)}
num_labels = len(label_list)

# 2. 模型
model_name = "bert-base-chinese"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForTokenClassification.from_pretrained(
    model_name, num_labels=num_labels, id2label=id2label, label2id=label2id
)

# 3. 预处理（max_len=256）
def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(
        examples["tokens"], truncation=True, padding=False, max_length=256,
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

tokenized_datasets = dataset.map(
    tokenize_and_align_labels, batched=True,
    remove_columns=dataset["train"].column_names,
)
data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

# 4. 评估指标
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

# 5. 训练参数：batch 8 + 梯度累积 2（等效 16），5 epochs，按 F1 选最佳
training_args = TrainingArguments(
    output_dir="./bert-ner-wikiann-v2",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    warmup_ratio=0.1,
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    per_device_eval_batch_size=8,
    eval_accumulation_steps=4,
    num_train_epochs=5,
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

# 6. 训练
trainer.train()

# 7. 最终评估（验证集）
print("\n========== V2 最终评估指标（验证集） ==========")
eval_result = trainer.evaluate()
for key, value in eval_result.items():
    if key != "eval_classification_report":
        print(f"{key}: {value:.4f}")
print("\n详细分类报告：")
print(eval_result.get("eval_classification_report", "未找到详细报告"))

# 8. 保存最终模型
model.save_pretrained("./bert-ner-wikiann-final")
tokenizer.save_pretrained("./bert-ner-wikiann-final")
print("\n最终模型已保存至 ./bert-ner-wikiann-final")
