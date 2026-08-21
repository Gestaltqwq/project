# -*- coding: utf-8 -*-
"""用 LoRA 微调后的 Qwen2.5-1.5B-Instruct 在 CLUENER test 集上做 NER 抽取演示。
- base_only=True   -> 只用基础模型（对比效果）
- base_only=False  -> 加载 LoRA 适配器
输出: infer_results_base.json / infer_results_lora.json
"""
import json
import os
import sys

BASE = r"D:\code\2026\7_8月实训\8_20"
MODEL = r"C:\Users\LENOVO\.cache\modelscope\models\Qwen--Qwen2.5-1.5B-Instruct\snapshots\master"
ADAPTER = os.path.join(BASE, r"LlamaFactory\saves\Qwen2.5-1.5B-Instruct\lora\cluener_100_20260821")

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

INSTRUCTION = (
    "请从以下文本中识别出所有命名实体，并按类别列出。"
    "实体类别包括：地址、书名、公司、游戏、政府、电影、姓名、组织机构、职位、场景。"
    "只输出识别到的实体，格式为“类别：实体1、实体2；类别2：实体3”，没有的类别不要输出。"
)

TYPE_CN = {
    "address": "地址", "book": "书名", "company": "公司", "game": "游戏",
    "government": "政府", "movie": "电影", "name": "姓名",
    "organization": "组织机构", "position": "职位", "scene": "场景",
}


def load_test():
    path = os.path.join(BASE, "cluener_raw", "test.json")
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def gt_text(label):
    parts = []
    for en_type in ["address", "book", "company", "game", "government",
                    "movie", "name", "organization", "position", "scene"]:
        names = list(label.get(en_type, {}).keys())
        if names:
            parts.append(f"{TYPE_CN[en_type]}：{'、'.join(names)}")
    return "；".join(parts)


def main():
    base_only = len(sys.argv) > 1 and sys.argv[1] == "base"

    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL, torch_dtype=torch.bfloat16, attn_implementation="eager"
    ).to("cuda")
    if not base_only:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, ADAPTER)
        print("已加载 LoRA 适配器:", ADAPTER)
    model.eval()

    tests = load_test()
    chosen = [0, 3, 5, 12, 18, 26, 35, 47, 55, 63, 70, 88, 95, 101, 110, 130]
    results = []
    for idx in chosen:
        try:
            item = tests[idx]
            text = item["text"]
            messages = [{"role": "user", "content": INSTRUCTION + "\n文本：" + text}]
            prompt = tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
            with torch.no_grad():
                out = model.generate(
                    **inputs,
                    max_new_tokens=192,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            gen = out[0][inputs["input_ids"].shape[1]:]
            answer = tokenizer.decode(gen, skip_special_tokens=True).strip()
            results.append({"text": text, "gt": gt_text(item["label"]), "answer": answer})
            print(f"[{idx}] text: {text[:60]}...")
            print(f"     GT : {results[-1]['gt']}")
            print(f"     OUT: {answer}")
        except Exception as e:
            print(f"[{idx}] ERROR: {e!r}", file=sys.stderr)
            results.append({"text": "", "gt": "", "answer": f"[error] {e!r}"})
        print()

    out_name = "infer_results_base.json" if base_only else "infer_results_lora.json"
    with open(os.path.join(BASE, out_name), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("已保存 ->", out_name)


if __name__ == "__main__":
    main()
