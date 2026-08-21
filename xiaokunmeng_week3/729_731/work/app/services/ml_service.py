"""机器学习服务：三算法训练、实验管理、预测、导出导入、可视化

【业务层】编排训练/预测流程，复用工具层 data_processor / visualizer
"""
import json
import os

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
)
import xgboost as xgb

from app.core.database import SessionLocal
from app.core.response import BizException
from app.models.customer import Customer
from app.models.experiment import Experiment
from app.utils.data_processor import prepare, FEATURE_COLS, ALGORITHMS, SCALE_COLS
from app.utils import visualizer

# 模型存储目录（文档规范：data/models/）
MODEL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "models")
os.makedirs(MODEL_DIR, exist_ok=True)


def _load_customers_df() -> pd.DataFrame:
    """从数据库加载客户数据"""
    db = SessionLocal()
    try:
        rows = db.query(Customer).all()
    finally:
        db.close()
    if not rows:
        raise BizException(2001, "暂无数据，请先上传数据")
    return pd.DataFrame([c.to_dict() for c in rows])


def _make_model(name: str, params: dict = None):
    """按算法名构建模型（含默认超参）

    AI 方案 §2.4：LR/RF 用 class_weight="balanced"，XGB 用 scale_pos_weight
    """
    p = params.get(name, {}) if params else {}
    if name == "logistic_regression":
        return LogisticRegression(
            class_weight="balanced",
            C=p.get("C", 1.0),
            penalty=p.get("penalty", "l2"),
            solver=p.get("solver", "lbfgs"),
            max_iter=p.get("max_iter", 1000),
            tol=p.get("tol", 1e-4),
        )
    if name == "xgboost":
        return xgb.XGBClassifier(
            n_estimators=p.get("n_estimators", 200),
            max_depth=p.get("max_depth", 5),
            learning_rate=p.get("learning_rate", 0.05),
            subsample=p.get("subsample", 0.8),
            colsample_bytree=p.get("colsample_bytree", 0.8),
            min_child_weight=p.get("min_child_weight", 1),
            gamma=p.get("gamma", 0),
            reg_alpha=p.get("reg_alpha", 0),
            reg_lambda=p.get("reg_lambda", 1),
            eval_metric="auc", use_label_encoder=False, verbosity=0, random_state=42,
        )
    if name == "random_forest":
        # 前端下拉 "None" 字符串 → sklearn 的 None 对象
        max_features = p.get("max_features", "sqrt")
        if max_features == "None":
            max_features = None
        return RandomForestClassifier(
            class_weight="balanced",
            n_estimators=p.get("n_estimators", 200),
            max_depth=p.get("max_depth", 8),
            min_samples_split=p.get("min_samples_split", 2),
            min_samples_leaf=p.get("min_samples_leaf", 1),
            max_features=max_features,
            random_state=42, n_jobs=-1,
        )
    raise BizException(1001, f"未知算法: {name}")


def _build_viz_data(model, X_te, y_te) -> dict:
    """训练时生成可视化数据（AI 方案 §2.8：JSON 落库，免重训复原图表）"""
    from sklearn.metrics import roc_curve, confusion_matrix
    import numpy as np

    y_pred = model.predict(X_te)
    y_proba = model.predict_proba(X_te)[:, 1]
    fpr, tpr, _ = roc_curve(y_te, y_proba)
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
    elif hasattr(model, "coef_"):
        imp = abs(model.coef_[0])
    else:
        imp = []
    return {
        "roc": {"fpr": [round(float(x), 5) for x in fpr],
                "tpr": [round(float(x), 5) for x in tpr]},
        "confusion_matrix": [[int(x) for x in row] for row in confusion_matrix(y_te, y_pred)],
        "feature_importances": [round(float(x), 6) for x in imp],
        "feature_names": FEATURE_COLS,
    }


def _safe_prepare(df, scaler=None, with_target: bool = True):
    """包装 prepare：数据缺列/非法值 → BizException(1001)"""
    try:
        return prepare(df, scaler=scaler, with_target=with_target)
    except ValueError as e:
        raise BizException(1001, str(e))


def _save_bundle(name: str, model, scaler) -> str:
    """保存模型 bundle → 返回相对路径"""
    path = os.path.join(MODEL_DIR, f"{name}.joblib")
    joblib.dump({"model": model, "scaler": scaler, "features": FEATURE_COLS}, path)
    return f"data/models/{name}.joblib"


def train(models=None, params=None, test_size=0.2, random_state=42) -> dict:
    """训练指定算法（默认全部），返回各算法指标 + 最优模型"""
    names = [m for m in (models or ALGORITHMS) if m in ALGORITHMS]
    if not names:
        raise BizException(1001, "没有有效的算法")

    df = _load_customers_df()
    X, y, scaler = _safe_prepare(df)
    scale_pos_weight = (y == 0).sum() / (y == 1).sum() if (y == 1).sum() else 1.0
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y)

    results = {}
    best_auc, best_name = -1, None

    db = SessionLocal()
    try:
        Experiment.reset_best(db)
        for name in names:
            try:
                model = _make_model(name, params or {})
                if name == "xgboost" and hasattr(model, "scale_pos_weight"):
                    model.set_params(scale_pos_weight=scale_pos_weight)
                model.fit(X_tr, y_tr)

                y_pred = model.predict(X_te)
                y_proba = model.predict_proba(X_te)[:, 1]
                metrics = {
                    "accuracy": round(accuracy_score(y_te, y_pred), 4),
                    "precision": round(precision_score(y_te, y_pred, zero_division=0), 4),
                    "recall": round(recall_score(y_te, y_pred, zero_division=0), 4),
                    "f1_score": round(f1_score(y_te, y_pred, zero_division=0), 4),
                    "roc_auc": round(roc_auc_score(y_te, y_proba), 4),
                }
                results[name] = metrics

                model_path = _save_bundle(name, model, scaler)
                # AI 方案 §2.8：可视化数据 JSON 落库
                viz = _build_viz_data(model, X_te, y_te)
                exp_params = {"hyperparams": params or {}, "visualization": viz}
                db.add(Experiment(model_name=name, is_best=0, **metrics,
                                  params=json.dumps(exp_params, ensure_ascii=False),
                                  model_path=model_path))
                db.commit()

                if metrics["roc_auc"] > best_auc:
                    best_auc, best_name = metrics["roc_auc"], name
            except Exception as e:
                results[name] = {"error": str(e)}

        if best_name:
            best_exp = db.query(Experiment).filter(
                Experiment.model_name == best_name,
                Experiment.roc_auc == best_auc,
            ).order_by(Experiment.id.desc()).first()
            if best_exp:
                best_exp.is_best = 1
                db.commit()
    finally:
        db.close()

    return {"best_model": best_name, "results": results}


def list_experiments(page: int, per_page: int, model_name=None) -> dict:
    db = SessionLocal()
    try:
        q = db.query(Experiment)
        if model_name:
            q = q.filter(Experiment.model_name == model_name)
        total = q.count()
        pages = (total + per_page - 1) // per_page if per_page else 0
        items = q.order_by(Experiment.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        return {
            "items": [e.to_dict(with_viz=True) for e in items],
            "total": total, "page": page, "per_page": per_page, "pages": pages,
        }
    finally:
        db.close()


def get_best() -> dict:
    db = SessionLocal()
    try:
        exp = Experiment.get_best(db)
        if not exp:
            raise BizException(3002, "暂无训练好的模型，请先训练")
        return {"model_name": exp.model_name, "roc_auc": exp.roc_auc, "experiment_id": exp.id}
    finally:
        db.close()


def _load_bundle(model_name: str = None):
    """加载模型 bundle：model_name 缺省用最优模型"""
    if model_name:
        path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
        if not os.path.exists(path):
            raise BizException(3002, f"{model_name} 模型不存在，请先训练")
        return joblib.load(path), model_name
    db = SessionLocal()
    try:
        exp = Experiment.get_best(db)
    finally:
        db.close()
    if not exp:
        raise BizException(3002, "暂无训练好的模型，请先训练")
    path = os.path.join(MODEL_DIR, f"{exp.model_name}.joblib")
    if not os.path.exists(path):
        raise BizException(3002, "模型文件丢失，请重新训练")
    return joblib.load(path), exp.model_name


def predict_all(model_name: str = None) -> dict:
    """全量预测：加载模型（默认最优），回写 customers.predicted_prob"""
    bundle, model_name = _load_bundle(model_name)
    df = _load_customers_df()
    X, _, _ = _safe_prepare(df, scaler=bundle["scaler"])
    proba = bundle["model"].predict_proba(X)[:, 1]

    db = SessionLocal()
    try:
        # 批量更新 predicted_prob（executemany，避免 38 万行逐行 ORM）
        from sqlalchemy import update
        ids = [c.id for c in db.query(Customer).with_entities(Customer.id).all()]
        db.execute(update(Customer), [
            {"id": cid, "predicted_prob": float(p)} for cid, p in zip(ids, proba)
        ])
        db.commit()
    finally:
        db.close()
    return {"model_name": model_name, "predicted_count": len(df)}


def predict_upload(file_storage, model_name: str = None) -> dict:
    """上传新数据预测（不入库）"""
    bundle, model_name = _load_bundle(model_name)
    try:
        df = pd.read_excel(file_storage)
    except Exception:
        raise BizException(2002, "文件解析失败，请上传正确的 Excel 文件")
    df.columns = [str(c).strip().lower() for c in df.columns]

    X, _, _ = _safe_prepare(df, scaler=bundle["scaler"], with_target=False)
    proba = bundle["model"].predict_proba(X)[:, 1]
    df["predicted_prob"] = proba
    # 输出列：优先 id/gender/age，缺失则只输出概率
    out_cols = [c for c in ["id", "gender", "age"] if c in df.columns] + ["predicted_prob"]
    return {
        "model_name": model_name,
        "total_count": len(df),
        "statistics": {"high_value_count": int((proba >= 0.5).sum())},
        "predictions": df[out_cols].to_dict("records"),
    }


def export_model(model_name: str) -> str:
    """返回模型文件绝对路径（供路由发送文件）"""
    path = os.path.join(MODEL_DIR, f"{model_name}.joblib")
    if not os.path.exists(path):
        raise BizException(3002, f"{model_name} 模型不存在，请先训练")
    return path


def import_model(file_storage) -> dict:
    """导入 .joblib 模型文件"""
    try:
        bundle = joblib.load(file_storage)
        name = f"imported_{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}"
        path = _save_bundle(name, bundle["model"], bundle["scaler"])
    except Exception:
        raise BizException(1001, "模型文件格式错误，请上传 .joblib")
    return {"model_name": name, "path": path}


def visualization(chart_type: str, model_name: str = None) -> dict:
    """模型评估可视化 → base64 PNG

    AI 方案 §2.8：从 experiments.params 读取训练时落库的可视化数据复原图表，
    无需重新训练 / 重新预测。
    """
    import numpy as np

    def _wrap(result: dict) -> dict:
        result["chart_type"] = chart_type
        return result

    def _get_exp(model_name: str = None):
        """取指定模型或最优模型的实验记录"""
        db = SessionLocal()
        try:
            q = db.query(Experiment)
            exp = (q.filter(Experiment.model_name == model_name).order_by(Experiment.id.desc()).first()
                   if model_name else q.filter(Experiment.is_best == 1).first())
            if not exp:
                raise BizException(3002, "暂无训练好的模型，请先训练")
            viz = json.loads(exp.params or "{}").get("visualization", {})
            return exp, viz
        finally:
            db.close()

    if chart_type == "roc_curve":
        _, viz = _get_exp(model_name)
        if not viz.get("roc"):
            raise BizException(3002, "该实验缺少 ROC 数据，请重新训练")
        return _wrap(visualizer.roc_chart_data(viz["roc"]["tpr"], viz["roc"]["fpr"]))

    if chart_type == "metrics_comparison":
        db = SessionLocal()
        try:
            exps = [e.to_dict() for e in db.query(Experiment).all()]
        finally:
            db.close()
        if not exps:
            raise BizException(3002, "请先训练模型")
        return _wrap(visualizer.metrics_comparison_chart(exps))

    if chart_type in ("confusion_matrix", "feature_importance"):
        if not model_name:
            raise BizException(1001, f"{chart_type} 必须带 model 参数")
        exp, viz = _get_exp(model_name)
        if chart_type == "confusion_matrix":
            if not viz.get("confusion_matrix"):
                raise BizException(3002, "该实验缺少混淆矩阵数据，请重新训练")
            cm = np.array(viz["confusion_matrix"])
            return _wrap(visualizer.confusion_matrix_data(cm, model_name))
        # feature_importance
        if not viz.get("feature_importances"):
            raise BizException(3002, "该实验缺少特征重要性数据，请重新训练")
        return _wrap(visualizer.feature_importance_chart(
            viz["feature_names"], list(viz["feature_importances"]), model_name))

    raise BizException(1001, f"未知图表类型: {chart_type}")
