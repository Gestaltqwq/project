"""认证路由：register / login / me / logout / users / profile / password

【MVC 归属】Controller 层
【路由前缀】/api/v1/auth
"""
from flask import request, Blueprint

from app.core.config import settings
from app.core.database import get_db
from app.core.parser import parse_body as _parse_body
from app.core.response import json, BizException
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import login_required, role_required, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest, LoginRequest, UpdateProfileRequest, UpdatePasswordRequest
)

bp = Blueprint("auth", __name__, url_prefix="/auth")


# ============================================================
# 用户注册
# ============================================================
@bp.route("/register", methods=["POST"])
def register():
    """注册：username + password → 创建普通用户"""
    req = _parse_body(RegisterRequest)
    db = get_db()

    # 查重
    if User.find_by_username(db, req.username):
        raise BizException(1004, "用户名已存在")

    # 密码哈希后创建（默认角色 user）
    user = User.create(db, req.username, hash_password(req.password), role="user")

    # 注册成功直接签发 Token（与测试文档约定一致；subject 用用户 ID 字符串）
    token = create_access_token(str(user.id), token_version=user.token_version)
    return json({
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        },
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }, message="注册成功", status=201)


# ============================================================
# 用户登录
# ============================================================
@bp.route("/login", methods=["POST"])
def login():
    """登录：username + password → 返回 JWT Token"""
    req = _parse_body(LoginRequest)
    db = get_db()

    user = User.find_by_username(db, req.username)

    # 登录锁定校验（增强）：锁定期间拒绝
    if user and user.is_locked():
        raise BizException(1002, "账号已锁定，请30分钟后再试", 401)

    # 凭证校验：失败累计次数
    if not user or not verify_password(req.password, user.password_hash):
        if user:
            user.record_fail(db)
        raise BizException(1002, "用户名或密码错误", 401)

    # 登录成功：清零失败次数
    user.reset_login(db)
    token = create_access_token(str(user.id), token_version=user.token_version)

    # 记录登录日志
    try:
        from app.models.operation_log import OperationLog
        OperationLog.add(db, user.id, user.username, "login", details="用户登录")
    except Exception:
        pass

    return json({
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {"id": user.id, "username": user.username, "role": user.role},
    })


# ============================================================
# 获取当前用户
# ============================================================
@bp.route("/me", methods=["GET"])
@login_required
def me():
    """获取当前登录用户信息"""
    user = get_current_user()
    return json({
        "id": user.id,
        "username": user.username,
        "role": user.role,
    })


# ============================================================
# 用户登出
# ============================================================
@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """登出：把当前 Token 加入黑名单，使其立即失效"""
    from datetime import datetime, timezone
    from app.core.security import decode_payload
    from app.models.token_blacklist import TokenBlacklist

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    db = get_db()

    # 解析 Token 过期时间，用于黑名单清理
    expires_at = None
    payload = decode_payload(token)
    if payload and payload.get("exp"):
        expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)

    TokenBlacklist.add(db, token, expires_at)
    return json(message="已登出")


# ============================================================
# 用户列表（仅管理员）
# ============================================================
@bp.route("/users", methods=["GET"])
@role_required("admin")
def users():
    """获取所有用户列表（仅管理员；不含密码哈希）"""
    db = get_db()
    user_list = User.all_users(db)
    return json([{
        "id": u.id,
        "username": u.username,
        "role": u.role,
    } for u in user_list])


# ============================================================
# 修改用户名（登录用户）
# ============================================================
@bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    """修改用户名：新用户名不得与现有用户重复（排除自己）"""
    req = _parse_body(UpdateProfileRequest)
    db = get_db()
    user = get_current_user()

    # 查重：排除自己，防撞名
    exists = User.find_by_username(db, req.new_username)
    if exists and exists.id != user.id:
        raise BizException(1004, "用户名已存在")

    user.update_username(db, req.new_username)
    return json({"username": user.username}, message="用户名修改成功")


# ============================================================
# 修改密码（登录用户）
# ============================================================
@bp.route("/password", methods=["PUT"])
@login_required
def change_password():
    """修改密码：先验旧密码，再哈希入库并递增令牌版本使旧 token 失效"""
    req = _parse_body(UpdatePasswordRequest)
    db = get_db()
    user = get_current_user()

    # 旧密码校验（防越权改密）
    if not verify_password(req.old_password, user.password_hash):
        raise BizException(1002, "旧密码错误", 400)

    # 新密码哈希后入库 + 递增 token_version（旧 token 全部失效）
    user.update_password(db, hash_password(req.new_password))
    return json(message="密码修改成功")
