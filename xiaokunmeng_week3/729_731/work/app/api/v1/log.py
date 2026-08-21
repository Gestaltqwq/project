"""日志模块路由：操作日志查询（仅管理员）

【路由前缀】/api/v1/logs
"""
from flask import request, Blueprint

from app.core.response import json
from app.core.dependencies import role_required
from app.core.database import SessionLocal
from app.models.operation_log import OperationLog
from app.utils.pagination import parse_pagination

bp = Blueprint("logs", __name__, url_prefix="/logs")


@bp.route("", methods=["GET"])
@role_required("admin")
def list_logs():
    """操作日志分页查询，支持 user_id / action 过滤"""
    page, per_page = parse_pagination(default_per_page=50)

    db = SessionLocal()
    try:
        q = db.query(OperationLog)
        uid = request.args.get("user_id", type=int)
        action = request.args.get("action")
        if uid:
            q = q.filter(OperationLog.user_id == uid)
        if action:
            q = q.filter(OperationLog.action == action)

        total = q.count()
        pages = (total + per_page - 1) // per_page if per_page else 0
        items = q.order_by(OperationLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return json({
            "items": [log.to_dict() for log in items],
            "total": total, "page": page, "per_page": per_page, "pages": pages,
        })
    finally:
        db.close()
