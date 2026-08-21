"""Token 黑名单表：记录已登出/失效的 JWT

【作用】解决 JWT 无状态导致"登出后 Token 仍有效"的漏洞
【原理】logout 时把 token 写入黑名单，鉴权时先查黑名单
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class TokenBlacklist(Base):
    """Token 黑名单"""
    __tablename__ = "token_blacklists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod
    def is_blacklisted(cls, db: Session, token: str) -> bool:
        """判断 token 是否已失效（纯读，不触发写操作）"""
        return db.query(cls).filter(cls.token == token).first() is not None

    @classmethod
    def add(cls, db: Session, token: str, expires_at: datetime = None):
        """加入黑名单（幂等）；顺带清理已过期记录（只在写操作时，避免每个请求写库）"""
        if not cls.is_blacklisted(db, token):
            db.add(cls(token=token, expires_at=expires_at))
            db.commit()
            db.query(cls).filter(cls.expires_at < datetime.now()).delete()
            db.commit()
