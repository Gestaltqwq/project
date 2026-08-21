"""应用工厂：create_app

【职责】
1. 创建 Flask 实例并加载配置（含静态目录）
2. 初始化数据库（建表 + 种子管理员 + 默认 Prompt 模板）
3. 注册蓝图
4. 注册请求钩子和三级异常处理器
"""
from flask import Flask
from werkzeug.exceptions import HTTPException

from app.core.config import settings
from app.core.database import engine, Base, close_db, SessionLocal
from app.core.response import json, BizException
from app.core.security import hash_password

# 先导入所有模型，确保 create_all 建出全部表
from app import models  # noqa: F401
from app.models.user import User


def seed_admin():
    """初始化一个管理员账号（admin / admin123），已存在则跳过"""
    db = SessionLocal()
    try:
        if not User.find_by_username(db, "admin"):
            User.create(db, "admin", hash_password("admin123"), role="admin")
    finally:
        db.close()


def seed_prompt_template():
    """初始化默认 Prompt 模板（统一入口 PromptTemplate.ensure_active）"""
    from app.services.llm_service import DEFAULT_PROMPT_TEMPLATE
    from app.models.prompt_template import PromptTemplate
    db = SessionLocal()
    try:
        PromptTemplate.ensure_active(db, DEFAULT_PROMPT_TEMPLATE)
    finally:
        db.close()


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="/static")

    # === 配置 ===
    app.config["SECRET_KEY"] = settings.JWT_SECRET_KEY

    # === 数据库：建表 + 种子数据 ===
    with app.app_context():
        Base.metadata.create_all(bind=engine)
        seed_admin()
        seed_prompt_template()

    # === 注册蓝图 ===
    from app.api.v1 import v1
    app.register_blueprint(v1)

    # === 前端 SPA 根路由 ===
    @app.route("/")
    def index():
        return app.send_static_file("index.html")

    # === 请求钩子：请求结束关闭 DB 会话 ===
    app.teardown_appcontext(close_db)

    # === 三级异常处理器（具体 → 宽泛） ===
    @app.errorhandler(BizException)
    def handle_biz_exception(e: BizException):
        """业务异常：返回业务码"""
        return json(code=e.code, message=e.message, status=e.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_exception(e: HTTPException):
        """框架 HTTP 异常（404/405/415 等）"""
        if e.code == 404:
            return json(code=-5, message="接口不存在", status=404)
        return json(code=-1, message=e.description or "请求错误", status=e.code)

    @app.errorhandler(Exception)
    def handle_exception(e: Exception):
        """兜底异常：不泄露堆栈，统一返回 5000"""
        app.logger.exception(e)
        return json(code=5000, message="服务器内部错误", status=500)

    return app
