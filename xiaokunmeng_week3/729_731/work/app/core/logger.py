"""操作日志：记录用户关键操作（登录/上传/训练/预测/邮件）

【MVC 归属】基础设施层（被 Controller 层调用）
"""
from functools import wraps
from flask import g, request

from app.core.database import get_db
from app.models.operation_log import OperationLog


def log_action(action: str):
    """操作日志装饰器：请求成功后自动记录一条日志

    用法：@bp.route('/train') \n @role_required('admin') \n @log_action('model_training')
    需在 @login_required / @role_required 之后使用（保证 g.current_user 已挂载）
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            resp = f(*args, **kwargs)
            try:
                user = g.get("current_user")
                user_id = user.id if user else None
                username = user.username if user else ""
                OperationLog.add(get_db(), user_id, username, action,
                                 details=f"{request.method} {request.path}")
            except Exception:
                pass  # 日志失败不影响主流程
            return resp
        return wrapper
    return decorator
