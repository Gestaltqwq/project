"""模型实验记录表：每次训练保存一条，标记最优模型"""
import json
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class Experiment(Base):
    """模型训练实验记录"""
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)   # xgboost 等
    accuracy: Mapped[float] = mapped_column(Float, nullable=True)
    precision: Mapped[float] = mapped_column(Float, nullable=True)
    recall: Mapped[float] = mapped_column(Float, nullable=True)
    f1_score: Mapped[float] = mapped_column(Float, nullable=True)
    roc_auc: Mapped[float] = mapped_column(Float, nullable=True)
    params: Mapped[str] = mapped_column(Text, default="{}")               # 超参 JSON
    model_path: Mapped[str] = mapped_column(String(255), default="")      # 模型文件路径
    is_best: Mapped[int] = mapped_column(Integer, default=0)              # 1=最优
    trained_by: Mapped[int] = mapped_column(Integer, nullable=True)       # 训练人
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod
    def reset_best(cls, db: Session):
        """清空所有 is_best 标记（训练前调用）"""
        db.query(cls).update({cls.is_best: 0})

    @classmethod
    def get_best(cls, db: Session) -> "Experiment | None":
        return db.query(cls).filter(cls.is_best == 1).first()

    def to_dict(self, with_viz: bool = False) -> dict:
        """序列化；with_viz=True 时附带可视化数据（用于 /experiments 明细）"""
        try:
            raw = json.loads(self.params) if self.params else {}
        except (ValueError, TypeError):
            raw = {}
        # AI 方案 §2.8：params 结构为 {hyperparams, visualization}
        hyperparams = raw.get("hyperparams", raw)
        result = {
            "id": self.id,
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "roc_auc": self.roc_auc,
            "params": hyperparams,
            "model_path": self.model_path,
            "is_best": self.is_best,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
        if with_viz and isinstance(raw, dict) and "visualization" in raw:
            result["visualization"] = raw["visualization"]
        return result
