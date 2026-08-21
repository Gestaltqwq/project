"""模型模块路由：train / experiments / best / predict / export / import / visualization

【路由前缀】/api/v1/model
"""
from flask import request, Blueprint, send_file

from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required
from app.core.logger import log_action
from app.schemas.model import TrainRequest
from app.services import ml_service
from app.utils.pagination import parse_pagination
from app.core.parser import parse_body as _parse_body

bp = Blueprint("model", __name__, url_prefix="/model")


@bp.route("/train", methods=["POST"])
@role_required("admin")
@log_action("model_training")
def train():
    """训练模型（body: {} 训全部；{models:[...]} 指定算法）"""
    req = _parse_body(TrainRequest, allow_empty=True)
    result = ml_service.train(
        models=req.models, params=req.params,
        test_size=req.test_size, random_state=req.random_state)
    return json(result, message="训练完成")


@bp.route("/experiments", methods=["GET"])
@role_required("admin")
def experiments():
    """实验记录列表"""
    page, per_page = parse_pagination(default_per_page=50)
    return json(ml_service.list_experiments(
        page, per_page, model_name=request.args.get("model_name")))


@bp.route("/best", methods=["GET"])
@login_required
def best():
    """获取最优模型"""
    return json(ml_service.get_best())


@bp.route("/predict", methods=["POST"])
@role_required("admin")
@log_action("prediction")
def predict():
    """全量预测（body 可选 model_name，缺省用最优模型）"""
    body = request.get_json(silent=True) or {}
    return json(ml_service.predict_all(body.get("model_name")), message="预测完成")


@bp.route("/predict_upload", methods=["POST"])
@role_required("admin")
@log_action("prediction")
def predict_upload():
    """上传数据预测（不入库）"""
    file = request.files.get("file")
    if not file:
        raise BizException(1001, "缺少 file 字段")
    return json(ml_service.predict_upload(file, request.form.get("model")))


@bp.route("/visualization/<chart_type>", methods=["GET"])
@role_required("admin")
def visualization(chart_type):
    """模型评估图表"""
    model_name = request.args.get("model")
    try:
        return json(ml_service.visualization(chart_type, model_name))
    except ValueError as e:
        raise BizException(1001, str(e))


@bp.route("/export/<model_name>", methods=["GET"])
@role_required("admin")
def export(model_name):
    """导出模型 .joblib 文件"""
    path = ml_service.export_model(model_name)
    return send_file(path, as_attachment=True, download_name=f"{model_name}.joblib")


@bp.route("/import", methods=["POST"])
@role_required("admin")
@log_action("model_import")
def import_model():
    """导入 .joblib 模型文件"""
    file = request.files.get("file")
    if not file:
        raise BizException(1001, "缺少 file 字段")
    return json(ml_service.import_model(file), message="导入成功")
