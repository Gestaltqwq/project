"""生成 Postman 集合：python -m scripts.gen_postman → docs/postman_collection.json

覆盖 API 文档全部 29 个接口，分 5 个文件夹，登录/注册带 token 存储脚本。
"""
import json
import os

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")
OUT = os.path.join(DOCS_DIR, "postman_collection.json")


def req(method, path, name, auth=True, body=None, tests=None, desc=""):
    """构造一个 Postman 请求"""
    headers = []
    if auth:
        headers.append({"key": "Authorization", "value": "Bearer {{admin_token}}", "type": "text"})
    if body is not None:
        headers.append({"key": "Content-Type", "value": "application/json", "type": "text"})
    r = {
        "name": name,
        "request": {
            "method": method,
            "header": headers,
            "url": {"raw": f"{{{{base_url}}}}{path}", "host": ["{{base_url}}"], "path": path.strip("/").split("/")},
            "description": desc,
        },
        "response": [],
    }
    if body is not None:
        r["request"]["body"] = {"mode": "raw", "raw": json.dumps(body, ensure_ascii=False)}
    if tests:
        r["event"] = [{"listen": "test", "script": {"type": "text/javascript", "exec": tests}}]
    return r


def folder(name, items):
    return {"name": name, "item": items}


def build():
    auth = folder("01-认证", [
        req("POST", "/auth/login", "登录", auth=False,
            body={"username": "admin", "password": "admin123"},
            tests=['pm.environment.set("admin_token", pm.response.json().data.access_token);',
                   'pm.test("登录成功", () => pm.response.json().code === 0);']),
        req("POST", "/auth/register", "注册", auth=False,
            body={"username": "student01", "password": "stu123456"},
            tests=['pm.environment.set("user_token", pm.response.json().data.access_token);']),
        req("GET", "/auth/me", "获取当前用户"),
        req("POST", "/auth/logout", "登出", body={}),
        req("GET", "/auth/users", "用户列表（管理员）"),
    ])

    data = folder("02-数据", [
        {"name": "上传 Excel", "request": {
            "method": "POST",
            "header": [{"key": "Authorization", "value": "Bearer {{admin_token}}", "type": "text"}],
            "body": {"mode": "formdata", "formdata": [
                {"key": "file", "type": "file", "src": "data/sample_customers.xlsx"}]},
            "url": {"raw": "{{base_url}}/data/upload", "host": ["{{base_url}}"], "path": ["data", "upload"]}},
            "response": []},
        req("GET", "/data/customers?page=1&per_page=20", "客户列表分页"),
        req("GET", "/data/statistics", "数据概览统计"),
        req("GET", "/data/quality", "数据质量报告"),
        req("GET", "/data/visualization/response_distribution", "EDA 可视化"),
    ])

    model = folder("03-模型", [
        req("POST", "/model/train", "训练模型", body={"models": ["xgboost"]}),
        req("GET", "/model/experiments", "实验记录分页"),
        req("GET", "/model/best", "获取最佳模型"),
        req("POST", "/model/predict", "全量预测", body={}),
        {"name": "上传数据预测", "request": {
            "method": "POST",
            "header": [{"key": "Authorization", "value": "Bearer {{admin_token}}", "type": "text"}],
            "body": {"mode": "formdata", "formdata": [
                {"key": "file", "type": "file", "src": "data/sample_customers.xlsx"},
                {"key": "model", "type": "text", "value": "xgboost"}]},
            "url": {"raw": "{{base_url}}/model/predict_upload", "host": ["{{base_url}}"], "path": ["model", "predict_upload"]}},
            "response": []},
        req("GET", "/model/visualization/roc_curve", "模型可视化-ROC"),
        req("GET", "/model/visualization/metrics_comparison", "模型可视化-指标对比"),
        req("GET", "/model/visualization/confusion_matrix?model=xgboost", "模型可视化-混淆矩阵"),
        req("GET", "/model/visualization/feature_importance?model=xgboost", "模型可视化-特征重要性"),
        req("GET", "/model/export/xgboost", "导出模型"),
        {"name": "导入模型", "request": {
            "method": "POST",
            "header": [{"key": "Authorization", "value": "Bearer {{admin_token}}", "type": "text"}],
            "body": {"mode": "formdata", "formdata": [
                {"key": "file", "type": "file", "src": "data/models/xgboost.joblib"}]},
            "url": {"raw": "{{base_url}}/model/import", "host": ["{{base_url}}"], "path": ["model", "import"]}},
            "response": []},
    ])

    email = folder("04-邮件", [
        req("GET", "/email/targets?percentile=0.9", "高潜客户筛选"),
        req("POST", "/email/generate", "生成营销邮件", body={"limit": 5}),
        req("GET", "/email/prompt", "获取 Prompt 模板"),
        req("PUT", "/email/prompt", "更新 Prompt 模板",
            body={"content": "你是保险营销文案专家。请根据客户画像{gender}/{age}生成邮件。仅返回严格JSON：{{\"subject\":\"主题\",\"content\":\"正文\"}}"}),
        req("GET", "/email/records?page=1&per_page=20", "邮件记录列表"),
        req("GET", "/email/records/1", "邮件详情"),
        req("PUT", "/email/records/1", "更新邮件记录", body={"email_subject": "新标题"}),
        req("PATCH", "/email/records/1", "标记邮件状态", body={"status": "sent"}),
        req("DELETE", "/email/records/1", "删除单条邮件"),
        req("DELETE", "/email/records", "批量删除邮件", body={"record_ids": [1, 2, 3]}),
    ])

    logs = folder("05-日志", [
        req("GET", "/logs?page=1&per_page=20", "操作日志查询"),
    ])

    collection = {
        "info": {
            "name": "保险精准营销系统",
            "description": "基于 03_API接口文档.md 的 29 个接口",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [auth, data, model, email, logs],
    }
    return collection


if __name__ == "__main__":
    os.makedirs(DOCS_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(build(), f, ensure_ascii=False, indent=2)
    print(f"已生成: {OUT}")
