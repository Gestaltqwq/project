"""加载训练好的 bert-base-chinese NER 模型，对中文句子做命名实体识别演示。"""
import sys
from transformers import AutoTokenizer, AutoModelForTokenClassification
import torch

MODEL_DIR = "./bert-ner-wikiann-final"

def main(sentence: str | None = None):
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)
    model.eval()

    sentences = [sentence] if sentence else [
        "李民基在2009年毕业于首尔大学。",
        "阿里巴巴的总部位于杭州，马云是创始人。",
        "姚明曾效力于休斯敦火箭队，是中国著名的篮球运动员。",
    ]

    for text in sentences:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
        with torch.no_grad():
            logits = model(**inputs).logits
        preds = logits.argmax(dim=-1)[0].tolist()

        tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
        # 合并 [CLS]/[SEP] 和 ## 分词的实体片段
        entities, current, current_label = [], [], None
        for tok, pid in zip(tokens[1:-1], preds[1:-1]):
            label = model.config.id2label[pid]
            if label == "O":
                if current:
                    entities.append(("".join(current).replace("##", ""), current_label))
                    current, current_label = [], None
            elif label.startswith("B-"):
                if current:
                    entities.append(("".join(current).replace("##", ""), current_label))
                current, current_label = [tok], label[2:]
            elif label.startswith("I-") and current and label[2:] == current_label:
                current.append(tok)
            else:
                if current:
                    entities.append(("".join(current).replace("##", ""), current_label))
                    current, current_label = [], None
        if current:
            entities.append(("".join(current).replace("##", ""), current_label))

        print(f"句子: {text}")
        print(f"实体: {entities if entities else '（未识别到实体）'}\n")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
