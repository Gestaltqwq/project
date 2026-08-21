"""操作日志表：记录用户关键操作，实现可追溯审计"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class OperationLog(Base):
    """操作日志"""
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(50), default="")
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # login/upload/train/...
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod
    def add(cls, db: Session, user_id, username, action, details=""):
        """新增一条日志"""
        log = cls(user_id=user_id, username=username, action=action, details=details)
        db.add(log)
        db.commit()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "action": self.action,
            "details": self.details,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
