"""数据服务：Excel 导入、质量报告、统计、EDA 可视化

【业务层】编排数据导入与统计，图表复用工具层 visualizer
"""
from typing import Optional

import pandas as pd

from app.core.database import SessionLocal
from app.core.response import BizException
from app.models.customer import Customer
from app.utils import visualizer
from app.utils.data_processor import parse_excel, RAW_TO_FIELD


def import_excel(file_storage, user_id: int) -> dict:
    """上传并导入数据（覆盖策略：先清空旧数据）

    - parse_excel 保留原始列名并校验，非法行收集 errors
    - 入库时统一转小写下划线，记录 uploaded_by=user_id
    - AI 方案 §5：bulk_insert_mappings 分批 5000 条，避免锁库
    """
    records, errors = parse_excel(file_storage)  # 保留原始列名（Gender/Age...）

    # 原始列名 → 小写下划线入库字段
    rows = []
    for rec in records:
        rows.append({
            field: (int(rec[raw]) if field not in ("gender", "vehicle_age", "vehicle_damage") else str(rec[raw]))
            for raw, field in RAW_TO_FIELD.items()
        })

    # 按 id 去重（重复主键会导致 UNIQUE 冲突 500，重复行计入 errors）
    seen, dedup, dup = set(), [], []
    for row in rows:
        if row["id"] in seen:
            dup.append(f"重复 id: {row['id']}，已跳过")
        else:
            seen.add(row["id"])
            dedup.append(row)
    errors = list(errors) + dup
    rows = dedup

    # 质量报告（合法行的 DataFrame，保留原列名）
    quality = build_quality_report(pd.DataFrame(records))

    # 覆盖导入：清空 → Customer.bulk_create（分批 + uploaded_by）
    db = SessionLocal()
    try:
        Customer.clear(db)
        Customer.bulk_create(db, rows, user_id)
    finally:
        db.close()

    return {"imported_count": len(rows), "invalid_rows": len(errors), "errors": errors[:10],
            "quality_report": quality}


def build_quality_report(df: pd.DataFrame) -> dict:
    """生成数据质量报告"""
    return {
        "total_rows": int(df.shape[0]),
        "total_cols": int(df.shape[1]),
        "missing_values": {str(k): int(v) for k, v in df.isnull().sum().to_dict().items()},
        "duplicates": int(df.duplicated().sum()),
        "dtypes": {str(k): str(v) for k, v in df.dtypes.to_dict().items()},
    }


# 质量报告只统计上传的输入字段（排除系统派生字段：predicted_prob/uploaded_by/created_at）
QUALITY_COLS = [
    "id", "gender", "age", "driving_license", "region_code",
    "previously_insured", "vehicle_age", "vehicle_damage",
    "annual_premium", "policy_sales_channel", "vintage", "response",
]


def quality_report() -> dict:
    """查询当前库内数据的质量报告（仅统计输入字段，不把 predicted_prob 误算为缺失）"""
    db = SessionLocal()
    try:
        rows = db.query(Customer).all()
        df = pd.DataFrame([{k: getattr(c, k) for k in QUALITY_COLS} for c in rows])
    finally:
        db.close()
    if df.empty:
        raise BizException(2001, "暂无数据，请先上传")
    return build_quality_report(df)


def list_customers(page: int, per_page: int, gender: Optional[str] = None,
                   age_min: Optional[int] = None, age_max: Optional[int] = None,
                   previously_insured: Optional[int] = None, keyword: Optional[str] = None) -> dict:
    """客户分页列表（复用 Customer.paginate 类方法）"""
    db = SessionLocal()
    try:
        return Customer.paginate(db, page, per_page, {
            "gender": gender,
            "age_min": age_min,
            "age_max": age_max,
            "previously_insured": previously_insured,
            "keyword": keyword,
        })
    finally:
        db.close()


def statistics() -> dict:
    """数据概览统计"""
    db = SessionLocal()
    try:
        total = db.query(Customer).count()
        if total == 0:
            raise BizException(2001, "暂无数据，请先上传")

        rows = db.query(Customer).all()
        genders = [c.gender for c in rows]
        responses = [c.response for c in rows]
        ages = [c.age for c in rows]
        return {
            "total": total,
            "gender_distribution": {
                "Male": genders.count("Male"),
                "Female": genders.count("Female"),
            },
            "response_distribution": {
                "0": responses.count(0),
                "1": responses.count(1),
            },
            "age_stats": {
                "min": min(ages),
                "max": max(ages),
                "avg": round(sum(ages) / len(ages), 1),
            },
        }
    finally:
        db.close()


def eda_visualization(chart_type: str) -> dict:
    """EDA 图表 → base64 PNG（复用工具层 visualizer）"""
    db = SessionLocal()
    try:
        df = pd.DataFrame([c.to_dict() for c in db.query(Customer).all()])
    finally:
        db.close()
    if df.empty:
        raise BizException(2001, "暂无数据，请先上传")
    try:
        result = visualizer.eda_chart(df, chart_type)
        result["chart_type"] = chart_type
        return result
    except ValueError as e:
        raise BizException(1001, str(e))
