# -*- coding: utf-8 -*-
"""
数据准备脚本：从 Yelp JSONL 中抽样并划分训练/验证/测试集，缓存为 parquet。
- train : 20,000 条（来自 yelp_train.json）
- val   :  5,000 条（来自 yelp_train.json，与 train 不重叠）
- test  :  5,000 条（来自 yelp_test.json，独立测试集）

二分类任务：label=0 差评, label=1 好评（Yelp Polarity）。
"""
import os
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

TRAIN_JSON = os.path.join(BASE, 'yelp_train.json')
TEST_JSON = os.path.join(BASE, 'yelp_test.json')

SEED = 42
N_TRAIN, N_VAL, N_TEST = 20_000, 5_000, 5_000


def sample_from(json_path, n, seed):
    df = pd.read_json(json_path, lines=True, encoding='utf-8')
    return df.sample(n=n, random_state=seed).reset_index(drop=True)


def main():
    print('读取 yelp_train.json ...')
    train_all = sample_from(TRAIN_JSON, N_TRAIN + N_VAL, SEED)
    train_df = train_all.iloc[:N_TRAIN].reset_index(drop=True)
    val_df = train_all.iloc[N_TRAIN:].reset_index(drop=True)

    print('读取 yelp_test.json ...')
    test_df = sample_from(TEST_JSON, N_TEST, SEED)

    for name, df in [('train', train_df), ('val', val_df), ('test', test_df)]:
        out = os.path.join(DATA_DIR, f'{name}.parquet')
        df.to_parquet(out, index=False)
        dist = df['label'].value_counts().sort_index().to_dict()
        print(f'{name:5s}: {len(df):6d} 条 -> {out}  标签分布={dist}')


if __name__ == '__main__':
    main()
