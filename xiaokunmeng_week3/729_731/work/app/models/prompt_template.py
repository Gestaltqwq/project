"""Prompt 模板表：存储大模型邮件生成模板"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class PromptTemplate(Base):
    """Prompt 模板"""
    __tablename__ = "prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1)  # 1=启用
    created_by: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod
    def get_active(cls, db: Session) -> "PromptTemplate | None":
        """获取启用中的模板（默认取第一条）"""
        return db.query(cls).filter(cls.is_active == 1).first()

    @classmethod
    def update_content(cls, db: Session, content: str) -> "PromptTemplate":
        """更新启用模板内容；没有则新建"""
        tpl = cls.get_active(db)
        if tpl:
            tpl.content = content
        else:
            tpl = cls(name="默认模板", content=content, is_active=1)
            db.add(tpl)
        db.commit()
        db.refresh(tpl)
        return tpl

    @classmethod
    def ensure_active(cls, db: Session, default_content: str) -> "PromptTemplate":
        """确保存在启用模板（启动/运行时兜底统一入口）"""
        tpl = cls.get_active(db)
        if not tpl:
            tpl = cls.update_content(db, default_content)
        return tpl

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
        }
