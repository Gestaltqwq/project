# -*- coding: utf-8 -*-
"""
CLUENER2020 -> Alpaca 格式转换脚本（100 条）
- 输入: cluener_raw/train.json (JSONL: text + label)
- 输出: LlamaFactory/data/cluener_alpaca_100.json (alpaca 格式: instruction/input/output)
- 同时注册 dataset_info.json
"""
import json
import os
import random

BASE = os.path.dirname(os.path.abspath(__file__))
RAW_TRAIN = os.path.join(BASE, "cluener_raw", "train.json")
OUT_JSON = os.path.join(BASE, "LlamaFactory", "data", "cluener_alpaca_100.json")
DATASET_INFO = os.path.join(BASE, "LlamaFactory", "data", "dataset_info.json")

# 实体类型 -> 中文名
TYPE_CN = {
    "address": "地址", "book": "书名", "company": "公司", "game": "游戏",
    "government": "政府", "movie": "电影", "name": "姓名",
    "organization": "组织机构", "position": "职位", "scene": "场景",
}

INSTRUCTION = (
    "请从以下文本中识别出所有命名实体，并按类别列出。"
    "实体类别包括：地址、书名、公司、游戏、政府、电影、姓名、组织机构、职位、场景。"
    "只输出识别到的实体，格式为“类别：实体1、实体2；类别2：实体3”，没有的类别不要输出。"
)


def load_jsonl(path):
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def build_output(label):
    """把 label 转换成稳定的输出文本"""
    parts = []
    for en_type in ["address", "book", "company", "game", "government",
                    "movie", "name", "organization", "position", "scene"]:
        entities = label.get(en_type, {})
        names = list(entities.keys())
        if names:
            parts.append(f"{TYPE_CN[en_type]}：{'、'.join(names)}")
    return "；".join(parts)


def main():
    random.seed(42)
    raw = load_jsonl(RAW_TRAIN)
    print(f"原始 train 数据: {len(raw)} 条")

    # 过滤掉无实体的样本
    valid = [x for x in raw if x.get("label") and build_output(x.get("label", {}))]
    print(f"含实体样本: {len(valid)} 条")

    # 有放回抽不到? 直接随机抽取 100 条（保证确定性与类别覆盖）
    sample = random.sample(valid, 100)

    alpaca = []
    for item in sample:
        out = build_output(item["label"])
        alpaca.append({
            "instruction": INSTRUCTION,
            "input": item["text"],
            "output": out,
        })

    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(alpaca, f, ensure_ascii=False, indent=2)
    print(f"已写出 {len(alpaca)} 条 alpaca 数据 -> {OUT_JSON}")

    # 统计类别覆盖
    from collections import Counter
    cnt = Counter()
    for item in sample:
        for t in item["label"]:
            cnt[t] += 1
    print("类别覆盖:", dict(cnt))

    # 注册 dataset_info.json
    with open(DATASET_INFO, "r", encoding="utf-8") as f:
        info = json.load(f)
    info["cluener_alpaca_100"] = {
        "file_name": "cluener_alpaca_100.json",
        "formatting": "alpaca",
        "columns": {
            "prompt": "instruction",
            "query": "input",
            "response": "output",
        },
    }
    with open(DATASET_INFO, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    print("已注册 dataset_info.json -> cluener_alpaca_100")

    # 打印 3 条样例
    print("\n--- 样例 ---")
    for a in alpaca[:3]:
        print(json.dumps(a, ensure_ascii=False))


if __name__ == "__main__":
    main()
