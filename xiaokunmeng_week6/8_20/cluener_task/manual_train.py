# -*- coding: utf-8 -*-
"""CLUENER alpaca(100条) LoRA 手动训练循环（完全可控、逐步骤计时）
- 正确 mask: prompt 部分 -100, response 部分真实 token
- 超参: rank8/alpha16/lr1e-4/cosine/30epochs/有效batch16/cutoff512/eager
"""
import json
import os
import sys
import time

MODEL = r"C:\Users\LENOVO\.cache\modelscope\models\Qwen--Qwen2.5-1.5B-Instruct\snapshots\master"
BASE = r"D:\code\2026\7_8月实训\8_20"
DATA = os.path.join(BASE, r"LlamaFactory\data\cluener_alpaca_100.json")
OUT = os.path.join(BASE, r"LlamaFactory\saves\Qwen2.5-1.5B-Instruct\lora\cluener_100_20260821")
HB = os.path.join(BASE, "hb2.txt")


def hb(msg):
    with open(HB, "a", encoding="utf-8") as f:
        f.write(f'{time.strftime("%H:%M:%S")} {msg}\n')


hb("start")
import torch
from torch.utils.data import DataLoader
from transformers import AutoModelForCausalLM, AutoTokenizer, get_cosine_schedule_with_warmup
from peft import LoraConfig, get_peft_model, TaskType
from datasets import Dataset

hb("imports done")
tok = AutoTokenizer.from_pretrained(MODEL)
tok.pad_token = tok.eos_token
with open(DATA, "r", encoding="utf-8") as f:
    raw = json.load(f)


def make_sample(ex):
    prompt = f"{ex['instruction']}\n{ex['input']}\n"
    full = prompt + ex["output"]
    p = tok(prompt, truncation=True, max_length=768)
    f = tok(full, truncation=True, max_length=768)
    labels = [-100] * len(p["input_ids"]) + f["input_ids"][len(p["input_ids"]):]
    return {"input_ids": f["input_ids"], "attention_mask": f["attention_mask"], "labels": labels}


samples = [make_sample(ex) for ex in raw]
train, eval_s = samples[:95], samples[95:]
hb(f"samples: train={len(train)} eval={len(eval_s)}")


def collate(batch):
    def pad_list(ts, pad_val):
        max_len = max(t.size(0) for t in ts)
        out = torch.full((len(ts), max_len), pad_val, dtype=torch.long)
        for i, t in enumerate(ts):
            out[i, : t.size(0)] = t
        return out

    input_ids = [torch.tensor(x["input_ids"]) for x in batch]
    attn = [torch.tensor(x["attention_mask"]) for x in batch]
    labels = [torch.tensor(x["labels"]) for x in batch]
    return {
        "input_ids": pad_list(input_ids, tok.pad_token_id),
        "attention_mask": pad_list(attn, 0),
        "labels": pad_list(labels, -100),
    }


# 有效 batch=16 (batch4 x accum4); 95 样本 -> 6 步/epoch; 30 epochs -> 180 步
ACCUM = 8
TOTAL_STEPS = int(os.environ.get("TOTAL_STEPS", "120"))
PROBE = os.environ.get("PROBE", "0") == "1"
if PROBE:
    TOTAL_STEPS = 12
train_dl = DataLoader(train, batch_size=2, shuffle=True, collate_fn=collate)
hb(f"config: TOTAL_STEPS={TOTAL_STEPS} ACCUM={ACCUM} PROBE={PROBE}")
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, attn_implementation="eager")
lora = LoraConfig(
    task_type=TaskType.CAUSAL_LM, r=8, lora_alpha=16, lora_dropout=0,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(model, lora)
model = model.to("cuda")
model.train()
hb("model ready")

opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
sched = get_cosine_schedule_with_warmup(opt, num_warmup_steps=9, num_training_steps=TOTAL_STEPS)

log = []
step = 0
t_start = time.time()
t_last = t_start
epoch = 0
while step < TOTAL_STEPS:
    for batch in train_dl:
        batch = {k: v.to("cuda") for k, v in batch.items()}
        out = model(**batch)
        loss = out.loss / ACCUM
        loss.backward()
        if (step + 1) % ACCUM == 0:
            grad = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            opt.zero_grad()
            now = time.time()
            log.append({"step": step + 1, "loss": float(loss.item() * ACCUM),
                        "lr": sched.get_last_lr()[0], "grad_norm": float(grad),
                        "epoch": round((step + 1) / 6, 3),
                        "step_time": round(now - t_last, 2)})
            t_last = now
            if (step + 1) % 5 == 0:
                hb(f"step {step+1}/{TOTAL_STEPS} loss={log[-1]['loss']:.4f} lr={log[-1]['lr']:.2e} "
                   f"t/step={log[-1]['step_time']}s elapsed={round((now-t_start)/60,1)}min")
                print(json.dumps(log[-1]), flush=True)
        step += 1
        if step >= TOTAL_STEPS:
            break

hb(f"training done in {round((time.time()-t_start)/60,1)}min, saving")
os.makedirs(OUT, exist_ok=True)
model.save_pretrained(OUT)
tok.save_pretrained(OUT)
with open(os.path.join(OUT, "train_results.json"), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
hb("saved. ALL DONE")
print("ALL DONE", flush=True)
