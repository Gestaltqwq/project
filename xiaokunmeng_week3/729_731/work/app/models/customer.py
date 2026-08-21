"""客户表：对应 data.xlsx 的用户画像数据

【字段】与训练数据列一致，另加 uploaded_by（上传人）/ predicted_prob（预测概率）
【写法】对齐 app/models/user.py：类方法封装数据操作
"""
from datetime import datetime
from typing import Optional
import numpy as np
from sqlalchemy import String, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class Customer(Base):
    """客户信息表"""
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)          # Male/Female
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    region_code: Mapped[int] = mapped_column(Integer, nullable=False)
    policy_sales_channel: Mapped[int] = mapped_column(Integer, nullable=False)
    previously_insured: Mapped[int] = mapped_column(Integer, nullable=False) # 0/1
    annual_premium: Mapped[int] = mapped_column(Integer, nullable=False)
    vintage: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_age: Mapped[str] = mapped_column(String(20), nullable=False)     # < 1 Year 等
    vehicle_damage: Mapped[str] = mapped_column(String(10), nullable=False)  # Yes/No
    driving_license: Mapped[int] = mapped_column(Integer, nullable=False)    # 0/1
    response: Mapped[int] = mapped_column(Integer, nullable=False)           # 目标变量
    uploaded_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 关联 users.id
    predicted_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # ===== 类方法：封装数据操作（对齐 user.py 风格）=====

    @classmethod
    def bulk_create(cls, db: Session, rows: list[dict], user_id: int) -> int:
        """批量插入客户（rows 为已校验 dict 列表），记录上传人，分批防锁库"""
        for row in rows:
            row["uploaded_by"] = user_id
        BATCH = 5000
        for i in range(0, len(rows), BATCH):
            db.bulk_insert_mappings(cls, rows[i:i + BATCH])
        db.commit()
        return len(rows)

    @classmethod
    def paginate(cls, db: Session, page: int, per_page: int, filters: Optional[dict] = None) -> dict:
        """分页查询，filters 支持 gender/age_min/age_max/previously_insured/keyword"""
        q = db.query(cls)
        filters = filters or {}
        if filters.get("gender"):
            q = q.filter(cls.gender == filters["gender"])
        if filters.get("age_min") is not None:
            q = q.filter(cls.age >= filters["age_min"])
        if filters.get("age_max") is not None:
            q = q.filter(cls.age <= filters["age_max"])
        if filters.get("previously_insured") is not None:
            q = q.filter(cls.previously_insured == filters["previously_insured"])
        if filters.get("keyword"):
            q = q.filter(cls.id == int(filters["keyword"]))

        total = q.count()
        pages = (total + per_page - 1) // per_page if per_page else 0
        items = q.order_by(cls.id).offset((page - 1) * per_page).limit(per_page).all()
        return {
            "items": [c.to_dict() for c in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @classmethod
    def count(cls, db: Session) -> int:
        """客户总数"""
        return db.query(cls).count()

    @classmethod
    def find_high_potential(cls, db: Session, top_percent: float = 0.9) -> list["Customer"]:
        """按预测概率分位筛选高潜客户（默认 top 10%），按概率降序"""
        rows = db.query(cls).filter(cls.predicted_prob.isnot(None)).all()
        if not rows:
            return []
        probs = np.array([c.predicted_prob for c in rows])
        # top_percent=0.9 → 第 90 分位，仅概率最高的 10% 超过阈值
        threshold = float(np.quantile(probs, top_percent))
        targets = [c for c in rows if c.predicted_prob >= threshold]
        targets.sort(key=lambda c: c.predicted_prob, reverse=True)
        return targets

    @classmethod
    def clear(cls, db: Session):
        """清空全部客户数据（上传采用覆盖策略）"""
        db.query(cls).delete()
        db.commit()

    def to_dict(self) -> dict:
        """序列化为字典"""
        return {
            "id": self.id,
            "gender": self.gender,
            "age": self.age,
            "driving_license": self.driving_license,
            "region_code": self.region_code,
            "previously_insured": self.previously_insured,
            "vehicle_age": self.vehicle_age,
            "vehicle_damage": self.vehicle_damage,
            "annual_premium": self.annual_premium,
            "policy_sales_channel": self.policy_sales_channel,
            "vintage": self.vintage,
            "response": self.response,
            "predicted_prob": self.predicted_prob,
        }
