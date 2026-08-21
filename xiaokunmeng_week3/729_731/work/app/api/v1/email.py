"""邮件模块路由：targets / generate / prompt / records CRUD

【路由前缀】/api/v1/email
"""
from flask import request, Blueprint

from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required, get_current_user
from app.core.logger import log_action
from app.schemas.email import (
    GenerateEmailRequest, PromptUpdateRequest, EmailUpdateRequest,
    EmailStatusRequest, BatchDeleteRequest,
)
from app.services import email_service
from app.utils.pagination import parse_pagination
from app.core.parser import parse_body as _parse_body

bp = Blueprint("email", __name__, url_prefix="/email")


@bp.route("/targets", methods=["GET"])
@login_required
def targets():
    """筛选高潜客户（percentile 分位，默认 0.9）"""
    percentile = request.args.get("percentile", type=float)
    min_prob = request.args.get("min_prob", type=float)
    if percentile is not None and not (0 < percentile <= 1):
        raise BizException(1001, "percentile 必须在 (0,1] 之间")
    if min_prob is not None and not (0 <= min_prob <= 1):
        raise BizException(1001, "min_prob 必须在 [0,1] 之间")
    page, per_page = parse_pagination(default_per_page=20)
    return json(email_service.targets(percentile, min_prob, page, per_page))


@bp.route("/generate", methods=["POST"])
@login_required
@log_action("email_generation")
def generate():
    """批量生成营销邮件"""
    req = _parse_body(GenerateEmailRequest, allow_empty=True)
    user = get_current_user()
    result = email_service.generate(req.limit, req.customer_ids, user.id)
    return json(result, message="生成完成")


@bp.route("/prompt", methods=["GET"])
@login_required
def get_prompt():
    """获取当前 Prompt 模板"""
    return json(email_service.get_prompt())


@bp.route("/prompt", methods=["PUT"])
@login_required
@log_action("prompt_update")
def update_prompt():
    """更新 Prompt 模板"""
    req = _parse_body(PromptUpdateRequest)
    return json(email_service.update_prompt(req.content), message="模板已更新")


@bp.route("/records", methods=["GET"])
@login_required
def records():
    """邮件记录列表（admin 看全部，user 看自己的）"""
    page, per_page = parse_pagination(default_per_page=50)
    user = get_current_user()
    is_admin = user.role == "admin"
    return json(email_service.list_records(
        page, per_page, request.args.get("status"), user.id, is_admin))


def _current_user_ctx():
    """返回 (user_id, is_admin) 供记录操作做归属校验"""
    user = get_current_user()
    return user.id, user.role == "admin"


@bp.route("/records/<int:record_id>", methods=["GET"])
@login_required
def record_detail(record_id):
    """邮件详情"""
    uid, is_admin = _current_user_ctx()
    return json(email_service.get_record(record_id, uid, is_admin))


@bp.route("/records/<int:record_id>", methods=["PUT"])
@login_required
@log_action("email_update")
def update_record(record_id):
    """更新邮件内容"""
    req = _parse_body(EmailUpdateRequest)
    uid, is_admin = _current_user_ctx()
    return json(email_service.update_record(
        record_id, req.email_subject, req.email_content, uid, is_admin), message="已更新")


@bp.route("/records/<int:record_id>", methods=["PATCH"])
@login_required
@log_action("email_mark")
def set_status(record_id):
    """标记邮件状态"""
    req = _parse_body(EmailStatusRequest)
    uid, is_admin = _current_user_ctx()
    return json(email_service.set_status(record_id, req.status, uid, is_admin), message="状态已更新")


@bp.route("/records/<int:record_id>", methods=["DELETE"])
@login_required
@log_action("email_delete")
def delete_record(record_id):
    """删除单条邮件"""
    uid, is_admin = _current_user_ctx()
    return json(email_service.delete_record(record_id, uid, is_admin), message="已删除")


@bp.route("/records", methods=["DELETE"])
@login_required
@log_action("email_delete")
def batch_delete():
    """批量删除邮件"""
    req = _parse_body(BatchDeleteRequest)
    uid, is_admin = _current_user_ctx()
    return json(email_service.batch_delete(req.record_ids, uid, is_admin), message="批量删除完成")
