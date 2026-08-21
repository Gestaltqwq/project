"""邮件记录表：存储大模型生成的营销邮件"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class EmailRecord(Base):
    """营销邮件记录"""
    __tablename__ = "email_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)       # 关联 Customer.id
    email_subject: Mapped[str] = mapped_column(String(200), default="")
    email_content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="generated")    # generated/edited/sent/failed
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)         # 生成人
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "email_subject": self.email_subject,
            "email_content": self.email_content,
            "status": self.status,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
