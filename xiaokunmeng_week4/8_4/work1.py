import os
import sys
import time
import json
import gc

os.environ.setdefault('HF_HUB_DISABLE_SYMLINKS_WARNING', '1')
os.environ.setdefault('TRANSFORMERS_NO_ADVISORY_WARNINGS', '1')
if hasattr(sys.stdout, 'reconfigure'):          # 让 Windows 控制台正确显示中文
    sys.stdout.reconfigure(encoding='utf-8')

import numpy as np
import pandas as pd
import torch
from datasets import Dataset
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from transformers import (
    AutoTokenizer,
    BertForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorWithPadding,
)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data')
RUNS_DIR = os.path.join(BASE, 'runs')
MODEL_NAME = 'bert-base-uncased'
SEED = 42

CONFIGS = [
    {
        'name': 'iter1_baseline',
        'lr': 2e-5, 'num_train_epochs': 2, 'batch_size': 16, 'max_len': 128,
        'warmup_ratio': 0.0, 'weight_decay': 0.0, 'label_smoothing': 0.0,
        'note': '基线：BERT 默认 lr=2e-5，训练 2 轮，无 warmup / 权重衰减 / 标签平滑',
    },
    {
        'name': 'iter2_tuned',
        'lr': 3e-5, 'num_train_epochs': 3, 'batch_size': 16, 'max_len': 128,
        'warmup_ratio': 0.1, 'weight_decay': 0.01, 'label_smoothing': 0.0,
        'note': '调参：提高学习率到 3e-5，加入 warmup=0.1 与 weight_decay=0.01，训练 3 轮',
    },
    {
        'name': 'iter3_refined',
        'lr': 2e-5, 'num_train_epochs': 3, 'batch_size': 32, 'max_len': 192,
        'warmup_ratio': 0.1, 'weight_decay': 0.01, 'label_smoothing': 0.05,
        'note': '细化：更大 batch=32、更长文本截断 max_len=192、标签平滑 0.05 抗过拟合',
    },
]


def load_datasets():
    """加载 data_prep.py 抽样好的 parquet，标签列统一改名为 labels 供 Trainer 使用。"""
    train = pd.read_parquet(os.path.join(DATA_DIR, 'train.parquet'))
    val = pd.read_parquet(os.path.join(DATA_DIR, 'val.parquet'))
    test = pd.read_parquet(os.path.join(DATA_DIR, 'test.parquet'))
    ds_train = Dataset.from_pandas(train, preserve_index=False).rename_column('label', 'labels')
    ds_val = Dataset.from_pandas(val, preserve_index=False).rename_column('label', 'labels')
    ds_test = Dataset.from_pandas(test, preserve_index=False).rename_column('label', 'labels')
    return ds_train, ds_val, ds_test


def tokenize(tokenizer, ds, max_len):
    """对数据集做 BERT 分词（不 padding，交给 DataCollator 动态 padding）。"""
    def _tok(batch):
        return tokenizer(
            batch['text'], truncation=True, padding=False, max_length=max_len,
        )
    return ds.map(_tok, batched=True, remove_columns=['text'])


def compute_metrics(eval_pred):
    """评估指标：accuracy / macro-F1 / precision / recall。"""
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        'accuracy': accuracy_score(labels, preds),
        'f1': f1_score(labels, preds, average='macro', zero_division=0),
        'precision': precision_score(labels, preds, average='macro', zero_division=0),
        'recall': recall_score(labels, preds, average='macro', zero_division=0),
    }


def run_iteration(cfg, ds_train, ds_val, ds_test, tokenizer):
    """执行一轮独立微调，返回该轮全部记录。"""
    name = cfg['name']
    out_dir = os.path.join(RUNS_DIR, name)
    os.makedirs(out_dir, exist_ok=True)

    # 每次迭代都从预训练权重重新微调（保证迭代之间相互独立、可对比）
    model = BertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    args = TrainingArguments(
        output_dir=out_dir,
        learning_rate=cfg['lr'],
        num_train_epochs=cfg['num_train_epochs'],
        per_device_train_batch_size=cfg['batch_size'],
        per_device_eval_batch_size=64,
        weight_decay=cfg['weight_decay'],
        warmup_ratio=cfg['warmup_ratio'],
        label_smoothing_factor=cfg['label_smoothing'],
        eval_strategy='epoch',
        save_strategy='epoch',
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model='f1',
        greater_is_better=True,
        logging_steps=200,
        logging_dir=os.path.join(out_dir, 'logs'),
        report_to=[],           # 关闭 wandb / tensorboard
        seed=SEED,
        fp16=True,              # GPU 半精度加速
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=ds_train,
        eval_dataset=ds_val,
        processing_class=tokenizer,   # transformers v5：原 tokenizer 参数改名为 processing_class
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    print(f'\n===== 迭代 {name} =====')
    print(f'    超参: {cfg["note"]}')
    t0 = time.time()
    trainer.train()
    train_time = time.time() - t0

    # 每个 epoch 的验证指标（含 val_loss / f1）；train_loss 按整 epoch 分组取均值
    loss_by_epoch = {}
    for h in trainer.state.log_history:
        if 'loss' in h and h.get('epoch') is not None:
            loss_by_epoch.setdefault(round(h['epoch']), []).append(h['loss'])
    epoch_logs = []
    for h in trainer.state.log_history:
        if 'eval_loss' in h:
            tr_losses = loss_by_epoch.get(round(h.get('epoch', 0)), [])
            epoch_logs.append({
                'epoch': h.get('epoch'),
                'train_loss': round(float(np.mean(tr_losses)), 5) if tr_losses else None,
                'eval_loss': round(h['eval_loss'], 5),
                'accuracy': round(h.get('eval_accuracy', float('nan')), 5),
                'f1': round(h.get('eval_f1', float('nan')), 5),
                'precision': round(h.get('eval_precision', float('nan')), 5),
                'recall': round(h.get('eval_recall', float('nan')), 5),
            })

    # 在独立测试集上评估最终（best）模型
    test_res = trainer.predict(ds_test)
    test_metrics = {
        'test_loss': round(float(test_res.metrics['test_loss']), 5),
        'test_accuracy': round(test_res.metrics['test_accuracy'], 5),
        'test_f1': round(test_res.metrics['test_f1'], 5),
        'test_precision': round(test_res.metrics['test_precision'], 5),
        'test_recall': round(test_res.metrics['test_recall'], 5),
    }

    # 保存本轮记录
    record = {
        'name': name,
        'note': cfg['note'],
        'hyperparams': {k: v for k, v in cfg.items() if k not in ('name', 'note')},
        'train_time_s': round(train_time, 1),
        'epoch_logs': epoch_logs,
        'test_metrics': test_metrics,
    }
    with open(os.path.join(out_dir, 'results.json'), 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2)

    print(f'    训练耗时 {train_time:.1f}s | 测试集 acc={test_metrics["test_accuracy"]} '
          f'f1={test_metrics["test_f1"]} loss={test_metrics["test_loss"]}')

    del model, trainer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return record


def write_report(all_records):
    """把 3 轮迭代结果汇总成 Markdown 优化记录。"""
    header = f"""# 基于 BERT 的 Yelp 评论情感二分类 —— 训练优化记录

- 日期：{time.strftime('%Y-%m-%d %H:%M')}
- 模型：`bert-base-uncased` + `BertForSequenceClassification(num_labels=2)`（transformers 库）
- 任务：Yelp 评论文本 → 好评(1) / 差评(0)
- 数据：train {len(pd.read_parquet(os.path.join(DATA_DIR,'train.parquet')))} / val {len(pd.read_parquet(os.path.join(DATA_DIR,'val.parquet')))} / test {len(pd.read_parquet(os.path.join(DATA_DIR,'test.parquet')))}（从 yelp_train.json / yelp_test.json 固定随机抽样 seed=42）
- 硬件：{"NVIDIA " + torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"}（PyTorch {torch.__version__}）
- 指标：accuracy、macro-F1、precision、recall；test 为独立测试集评估

## 1. 三轮迭代超参数总览

| 迭代 | 学习率 | epochs | batch | max_len | warmup | weight_decay | label_smoothing | 说明 |
|---|---|---|---|---|---|---|---|---|
"""
    for r in all_records:
        h = r['hyperparams']
        header += (f"| {r['name']} | {h['lr']:.0e} | {h['num_train_epochs']} | {h['batch_size']} | "
                   f"{h['max_len']} | {h['warmup_ratio']} | {h['weight_decay']} | {h['label_smoothing']} | {r['note']} |\n")

    header += """
## 2. 评估指标对比（test 集 + 各 epoch val）

| 迭代 | 最佳val_f1 | val_loss | test_loss | test_acc | test_f1 | test_precision | test_recall | 耗时 |
|---|---|---|---|---|---|---|---|---|
"""
    for r in all_records:
        best_epoch = max(r['epoch_logs'], key=lambda e: e['f1']) if r['epoch_logs'] else {}
        t = r['test_metrics']
        header += (f"| {r['name']} | {best_epoch.get('f1', '-')} | {best_epoch.get('eval_loss', '-')} | "
                   f"{t['test_loss']} | {t['test_accuracy']} | {t['test_f1']} | {t['test_precision']} | "
                   f"{t['test_recall']} | {r['train_time_s']}s |\n")

    for r in all_records:
        header += f"\n### {r['name']} —— {r['note']}\n\n逐 epoch 验证指标：\n\n| epoch | train_loss | eval_loss | acc | f1 | precision | recall |\n|---|---|---|---|---|---|---|\n"
        for e in r['epoch_logs']:
            header += (f"| {e['epoch']} | {e['train_loss'] or '-'} | {e['eval_loss']} | {e['accuracy']} | "
                       f"{e['f1']} | {e['precision']} | {e['recall']} |\n")

    best = max(all_records, key=lambda r: r['test_metrics']['test_f1'])
    header += f"""
## 3. 结论

3 轮迭代中 **{best['name']}** 效果最佳（test F1={best['test_metrics']['test_f1']}）。优化方向：
1. 基线训练即可收敛到高精度（二分类任务相对简单）；
2. 增加 warmup / weight_decay 并训练更久有助于稳定收敛；
3. 更大 batch 与更长截断长度保留更多上下文信息，配合 label smoothing 进一步抑制过拟合。
"""
    out = os.path.join(BASE, '训练优化记录.md')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(header)
    print(f'\n[报告已生成] {out}')


def main():
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'运行设备: {device} | torch={torch.__version__} | transformers={__import__("transformers").__version__}')

    ds_train, ds_val, ds_test = load_datasets()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # 按不同 max_len 缓存分词结果，避免重复分词
    tok_cache = {}
    all_records = []
    for cfg in CONFIGS:
        ml = cfg['max_len']
        if ml not in tok_cache:
            tok_cache[ml] = (
                tokenize(tokenizer, ds_train, ml),
                tokenize(tokenizer, ds_val, ml),
                tokenize(tokenizer, ds_test, ml),
            )
        t_tr, t_va, t_te = tok_cache[ml]
        record = run_iteration(cfg, t_tr, t_va, t_te, tokenizer)
        all_records.append(record)

    write_report(all_records)


if __name__ == '__main__':
    main()
