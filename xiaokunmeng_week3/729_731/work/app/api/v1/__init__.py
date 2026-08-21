"""API v1 蓝图聚合：导入各路由模块并挂载到 v1 蓝图"""
from flask import Blueprint

v1 = Blueprint("v1", __name__, url_prefix="/api/v1")

# 各业务模块子蓝图
from app.api.v1.auth import bp as auth_bp
from app.api.v1.data import bp as data_bp
from app.api.v1.model import bp as model_bp
from app.api.v1.email import bp as email_bp
from app.api.v1.log import bp as logs_bp

v1.register_blueprint(auth_bp)
v1.register_blueprint(data_bp)
v1.register_blueprint(model_bp)
v1.register_blueprint(email_bp)
v1.register_blueprint(logs_bp)
