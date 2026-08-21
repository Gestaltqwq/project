"""请求体解析：从 Flask request 校验 JSON 参数（共享基础设施层）

【MVC 归属】基础设施层（被各 Controller 路由复用）
【作用】统一 Pydantic 校验，避免每个路由手写 try/except
"""
from flask import request
from pydantic import ValidationError

from app.core.response import BizException


def parse_body(schema_cls, allow_empty: bool = False):
    """从请求 JSON 解析并校验参数，失败抛 BizException(1001)

    - allow_empty=True：允许空 body，用 Schema 默认值（如 train/generate 可不传参）
    """
    data = request.get_json(silent=True)
    if not data:
        if allow_empty:
            return schema_cls()
        raise BizException(1001, "请求体不能为空")
    try:
        return schema_cls(**data)
    except ValidationError as e:
        raise BizException(1001, f"参数错误: {e.errors()}")
