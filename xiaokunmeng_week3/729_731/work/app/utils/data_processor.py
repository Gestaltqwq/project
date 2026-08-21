"""数据工具：Excel 解析 + 特征工程

【工具层】parse_excel（数据上传解析）+ encode/prepare（特征工程）
"""
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.core.response import BizException

# ===== Excel 解析（数据上传）=====
# 原始列名（保留大小写），入库时再统一转小写下划线
EXCEL_FIELDS = [
    "id", "Gender", "Age", "Driving_License", "Region_Code", "Previously_Insured",
    "Vehicle_Age", "Vehicle_Damage", "Annual_Premium", "Policy_Sales_Channel",
    "Vintage", "Response",
]
# 原始列名 → 入库字段名
RAW_TO_FIELD = {
    "id": "id", "Gender": "gender", "Age": "age", "Driving_License": "driving_license",
    "Region_Code": "region_code", "Previously_Insured": "previously_insured",
    "Vehicle_Age": "vehicle_age", "Vehicle_Damage": "vehicle_damage",
    "Annual_Premium": "annual_premium", "Policy_Sales_Channel": "policy_sales_channel",
    "Vintage": "vintage", "Response": "response",
}


def parse_excel(file_storage) -> tuple[list[dict], list[str]]:
    """解析 Excel → (合法行[保留原始列名], 非法行错误列表)

    - 校验必要列（缺失抛 1001）
    - 逐行校验：空值行收集到 errors，不中断
    - 文件解析失败抛 BizException(2002)
    """
    try:
        df = pd.read_excel(file_storage)
    except Exception:
        raise BizException(2002, "文件解析失败，请上传正确的 Excel 文件")

    df.columns = [str(c).strip() for c in df.columns]  # 保留原始大小写
    missing = [c for c in EXCEL_FIELDS if c not in df.columns]
    if missing:
        raise BizException(1001, f"数据缺少必要列: {', '.join(missing)}")

    records, errors = [], []
    for idx, row in df.iterrows():
        rec = {}
        ok = True
        for col in EXCEL_FIELDS:
            val = row[col]
            if pd.isna(val):
                errors.append(f"第{idx + 2}行 {col} 为空值")
                ok = False
                break
            rec[col] = val
        if ok:
            records.append(rec)
    return records, errors

# 建模特征列（与 work1.py 一致，剔除 id/driving_license）
FEATURE_COLS = [
    "gender", "age", "region_code", "previously_insured",
    "vehicle_age", "vehicle_damage", "annual_premium",
    "policy_sales_channel", "vintage",
]
SCALE_COLS = ["age", "annual_premium", "vintage"]
ALGORITHMS = ["logistic_regression", "xgboost", "random_forest"]

# 分类变量编码映射（AI 方案 §2.2：Gender 无序用 Label，Vehicle_Age 有序用 Ordinal）
GENDER_MAP = {"Male": 0, "Female": 1}          # Label：Male=0, Female=1
VEHICLE_AGE_MAP = {"< 1 Year": 0, "1-2 Year": 1, "> 2 Years": 2}  # Ordinal 保留顺序
VEHICLE_DAMAGE_MAP = {"No": 0, "Yes": 1}       # Label：No=0, Yes=1


def encode(df: pd.DataFrame) -> pd.DataFrame:
    """分类变量编码（与 work1.py 一致）"""
    d = df.copy()
    d["gender"] = d["gender"].map(GENDER_MAP)
    d["vehicle_age"] = d["vehicle_age"].map(VEHICLE_AGE_MAP)
    d["vehicle_damage"] = d["vehicle_damage"].map(VEHICLE_DAMAGE_MAP)
    return d


def prepare(df: pd.DataFrame, scaler: StandardScaler = None, with_target: bool = True):
    """编码 + 特征筛选 + 缩放 → (X, y, scaler)

    - scaler 为空则 fit（训练时）；已存在则 transform（预测时）
    - with_target=False：预测上传数据没有 response 标签，y 返回 None
    - 缺列 / 非法分类值 → 抛 ValueError（由 service 层转成 1001）
    """
    # 列校验必须在 encode 之前（encode 会访问这些列）
    missing = [c for c in FEATURE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"缺少必要特征列: {', '.join(missing)}")
    d = encode(df)
    X = d[FEATURE_COLS].astype(float)
    if X.isna().any().any():
        raise ValueError("特征含无法识别的值（gender需Male/Female，vehicle_damage需Yes/No，vehicle_age需标准车龄）")
    y = d["response"].astype(int) if (with_target and "response" in d.columns) else None
    if scaler is None:
        scaler = StandardScaler()
        X[SCALE_COLS] = scaler.fit_transform(X[SCALE_COLS])
    else:
        X[SCALE_COLS] = scaler.transform(X[SCALE_COLS])
    return X, y, scaler
