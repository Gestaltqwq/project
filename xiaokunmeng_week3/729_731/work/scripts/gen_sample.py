"""生成测试样本数据：python -m app.scripts.gen_sample

生成 data/sample_customers.xlsx（1000 行，与训练数据同结构）
"""
import os
import random

import pandas as pd

random.seed(42)

OUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "sample_customers.xlsx")


def gen_sample(n=1000) -> pd.DataFrame:
    genders = ["Male", "Female"]
    vehicle_ages = ["< 1 Year", "1-2 Year", "> 2 Years"]
    channels = [26, 152, 156, 157, 124, 160, 22]
    rows = []
    for i in range(1, n + 1):
        previously_insured = 1 if random.random() < 0.47 else 0
        vehicle_damage = "Yes" if random.random() < 0.49 else "No"
        # 让 response 与两个关键特征相关（复现真实分布 ~87:13）
        base = 0.08 + 0.10 * previously_insured + 0.12 * (vehicle_damage == "Yes")
        response = 1 if random.random() < base else 0
        rows.append({
            "id": i,
            "Gender": random.choice(genders),
            "Age": random.randint(20, 80),
            "Driving_License": 1 if random.random() < 0.998 else 0,
            "Region_Code": random.randint(0, 52),
            "Previously_Insured": previously_insured,
            "Vehicle_Age": random.choice(vehicle_ages),
            "Vehicle_Damage": vehicle_damage,
            "Annual_Premium": random.randint(2630, 540165),
            "Policy_Sales_Channel": random.choice(channels),
            "Vintage": random.randint(1, 299),
            "Response": response,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    df = gen_sample()
    df.to_excel(OUT_PATH, index=False)
    print(f"已生成样本数据: {OUT_PATH} ({len(df)} 行)")
    print(f"Response 分布: {df['Response'].value_counts().to_dict()}")
