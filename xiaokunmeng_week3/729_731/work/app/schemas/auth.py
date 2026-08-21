"""请求校验：认证模块的 Pydantic Schema

【MVC 归属】校验层（Schema 层）
【思路】
每个路由对应一个 Request Schema，自动校验字段类型和约束。
校验失败时抛 BizException(1001)，由全局处理器返回统一错误格式。
"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    """注册请求：username + password"""
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=100, description="密码，至少6位")


class LoginRequest(BaseModel):
    """登录请求：username + password"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class UpdateProfileRequest(BaseModel):
    """修改用户名请求"""
    new_username: str = Field(..., min_length=1, max_length=50, description="新用户名")


class UpdatePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., min_length=1, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码，至少6位")
