"""分页参数解析（统一校验，防止 page=0/负值/per_page=0 产生错误分页）"""
from flask import request

from app.core.response import BizException


def parse_pagination(default_per_page: int = 50):
    """从 query 解析 page/per_page；非法值统一抛 1001

    - page 从 1 开始
    - per_page 限制在 [1, 100]
    """
    try:
        page = int(request.args.get("page", 1))
        per_page = min(int(request.args.get("per_page", default_per_page)), 100)
    except ValueError:
        raise BizException(1001, "分页参数必须是数字")
    if page < 1 or per_page < 1:
        raise BizException(1001, "page 和 per_page 必须为正整数")
    return page, per_page
