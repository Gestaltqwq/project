from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base

# 登录锁定参数
MAX_LOGIN_ATTEMPTS = 3
LOCK_DURATION_MINUTES = 30


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin / user
    login_attempts: Mapped[int] = mapped_column(Integer, default=0)         # 连续失败次数
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # 锁定截止
    token_version: Mapped[int] = mapped_column(Integer, default=1)          # 令牌版本（改密递增失效旧 token）
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @classmethod #查用户不需要有用户实例，可以直接调用类方法调用，逻辑上的优化
    def find_by_username(cls, db: Session, username: str) -> Optional["User"]:
        """按用户名查用户（登录/注册查重用）"""
        return db.query(cls).filter(cls.username == username).first()

    @classmethod
    def find_by_id(cls, db: Session, user_id: int) -> Optional["User"]:
        """按 ID 查用户（JWT 鉴权用，ID 不变故改名不影响登录态）"""
        return db.query(cls).filter(cls.id == user_id).first()

    @classmethod
    def create(cls, db: Session, username: str, password_hash: str, role: str = "user") -> "User":
        """创建用户：add → commit → refresh 拿自增 id"""
        user = cls(username=username, password_hash=password_hash, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def all_users(cls, db: Session) -> list["User"]:
        """查所有用户（admin 接口用，按 id 升序）"""
        return db.query(cls).order_by(cls.id).all()

    def update_username(self, db: Session, new_username: str) -> "User":
        """更新用户名并提交"""
        self.username = new_username
        db.commit()
        db.refresh(self)
        return self

    def update_password(self, db: Session, new_password_hash: str) -> "User":
        """更新密码并递增令牌版本（使所有旧 token 立即失效，防泄露后滥用）"""
        self.password_hash = new_password_hash
        self.token_version += 1
        db.commit()
        db.refresh(self)
        return self

    # ===== 登录锁定（增强）=====
    def is_locked(self) -> bool:
        """是否处于锁定状态"""
        return self.locked_until is not None and self.locked_until > datetime.now()

    def record_fail(self, db: Session):
        """记录一次登录失败；达阈值则锁定 30 分钟"""
        self.login_attempts += 1
        if self.login_attempts >= MAX_LOGIN_ATTEMPTS:
            self.locked_until = datetime.now() + timedelta(minutes=LOCK_DURATION_MINUTES)
        db.commit()

    def reset_login(self, db: Session):
        """登录成功：清零失败次数并解除锁定"""
        self.login_attempts = 0
        self.locked_until = None
        db.commit()
