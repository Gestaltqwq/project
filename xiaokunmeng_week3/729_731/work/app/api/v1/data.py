"""数据模块路由：upload / customers / export / statistics / quality / visualization

【路由前缀】/api/v1/data
"""
from flask import request, Blueprint

from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required, get_current_user
from app.core.logger import log_action
from app.utils.pagination import parse_pagination
from app.services import data_service

bp = Blueprint("data", __name__, url_prefix="/data")

# 上传大小限制（要求：10MB）
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@bp.route("/upload", methods=["POST"])
@role_required("admin")
@log_action("data_upload")
def upload():
    """上传 Excel 数据（覆盖策略导入，限制 10MB）"""
    file = request.files.get("file")
    if not file:
        raise BizException(1001, "缺少 file 字段")
    # 文件大小限制
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_UPLOAD_BYTES:
        raise BizException(1001, "文件超过 10MB 上限")
    user = get_current_user()
    result = data_service.import_excel(file, user.id)
    return json(result, message="上传成功")


@bp.route("/customers", methods=["GET"])
@login_required
def customers():
    """客户分页列表（支持 gender/age_min/age_max 过滤）"""
    page, per_page = parse_pagination(default_per_page=50)
    keyword = request.args.get("keyword")
    if keyword and not keyword.isdigit():
        raise BizException(1001, "keyword 必须为数字字符串")
    result = data_service.list_customers(
        page, per_page,
        gender=request.args.get("gender"),
        age_min=request.args.get("age_min", type=int),
        age_max=request.args.get("age_max", type=int),
        previously_insured=request.args.get("previously_insured", type=int),
        keyword=keyword,
    )
    return json(result)


@bp.route("/statistics", methods=["GET"])
@login_required
def statistics():
    """数据概览统计"""
    return json(data_service.statistics())


@bp.route("/quality", methods=["GET"])
@login_required
def quality():
    """数据质量报告"""
    return json(data_service.quality_report())


@bp.route("/visualization/<chart_type>", methods=["GET"])
@login_required
def visualization(chart_type):
    """EDA 图表（response_distribution/gender_response/age_distribution/premium_distribution）"""
    try:
        return json(data_service.eda_visualization(chart_type))
    except ValueError as e:
        raise BizException(1001, str(e))
