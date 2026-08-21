"""冒烟测试：python -m app.scripts.smoke_test

顺序跑完核心业务链路，每步打印 ✓，末尾汇总通过数。
"""
import os
import time
import traceback

from app import create_app
from scripts.gen_sample import gen_sample

app = create_app()
client = app.test_client()

STEPS = []
FAILED = []


def step(name, fn):
    STEPS.append(name)
    try:
        fn()
        print(f"  [OK] {name}")
    except Exception as e:
        FAILED.append(name)
        print(f"  [FAIL] {name}: {e}")
        traceback.print_exc()


def expect(resp, code=0, status=200):
    body = resp.get_json()
    assert resp.status_code == status, f"状态码 {resp.status_code} ≠ {status}: {body}"
    if body is not None and "code" in body:
        assert body["code"] == code, f"业务码 {body.get('code')} ≠ {code}: {body}"


def test_auth():
    uname = f"smoke_user_{int(time.time())}"
    r = client.post("/api/v1/auth/register", json={"username": uname, "password": "test123456"})
    expect(r, status=201)
    app.config["smoke_username"] = uname
    # admin 登录
    r = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    expect(r)
    app.config["admin_token"] = r.get_json()["data"]["access_token"]


def test_upload():
    df = gen_sample(200)
    tmp = "data/_smoke_tmp.xlsx"
    os.makedirs("data", exist_ok=True)
    df.to_excel(tmp, index=False)
    with open(tmp, "rb") as f:
        r = client.post("/api/v1/data/upload", headers=_h(),
                        data={"file": (f, "sample.xlsx")}, content_type="multipart/form-data")
    os.remove(tmp)
    expect(r)
    assert r.get_json()["data"]["imported_count"] == 200


def test_data_list():
    r = client.get("/api/v1/data/customers?page=1&per_page=20", headers=_h())
    expect(r)
    assert r.get_json()["data"]["total"] == 200


def test_statistics():
    r = client.get("/api/v1/data/statistics", headers=_h())
    expect(r)


def test_quality():
    r = client.get("/api/v1/data/quality", headers=_h())
    expect(r)


def test_eda():
    for ct in ["response_distribution", "age_distribution"]:
        r = client.get(f"/api/v1/data/visualization/{ct}", headers=_h())
        expect(r)


def test_train():
    r = client.post("/api/v1/model/train", json={"models": ["xgboost"]}, headers=_h())
    expect(r)
    assert r.get_json()["data"]["best_model"] == "xgboost"


def test_best():
    r = client.get("/api/v1/model/best", headers=_h())
    expect(r)


def test_experiments():
    r = client.get("/api/v1/model/experiments", headers=_h())
    expect(r)


def test_predict():
    r = client.post("/api/v1/model/predict", json={}, headers=_h())
    expect(r)


def test_predict_verify():
    r = client.get("/api/v1/data/customers?per_page=5", headers=_h())
    items = r.get_json()["data"]["items"]
    assert all(i["predicted_prob"] is not None for i in items), "predicted_prob 未回写"


def test_model_viz():
    r = client.get("/api/v1/model/visualization/roc_curve", headers=_h())
    expect(r)
    assert "image_base64" in r.get_json()["data"]


def test_targets():
    r = client.get("/api/v1/email/targets?percentile=0.9", headers=_h())
    expect(r)


def test_prompt():
    r = client.get("/api/v1/email/prompt", headers=_h())
    expect(r)


def test_logs():
    r = client.get("/api/v1/logs?page=1", headers=_h())
    expect(r)
    actions = [i["action"] for i in r.get_json()["data"]["items"]]
    assert "login" in actions or "data_upload" in actions


def test_rbac():
    r = client.post("/api/v1/auth/login",
                    json={"username": app.config["smoke_username"], "password": "test123456"})
    user_token = r.get_json()["data"]["access_token"]
    r = client.post("/api/v1/model/train", json={}, headers={"Authorization": f"Bearer {user_token}"})
    expect(r, code=1003, status=403)


def _h():
    return {"Authorization": f"Bearer {app.config['admin_token']}"}


def main():
    print("=" * 40)
    print("冒烟测试开始")
    print("=" * 40)
    start = time.time()

    step("0.1 认证（注册+admin登录）", test_auth)
    step("1.1 上传 Excel", test_upload)
    step("1.2 客户列表", test_data_list)
    step("1.3 数据统计", test_statistics)
    step("1.4 质量报告", test_quality)
    step("1.5 EDA 可视化", test_eda)
    step("2.1 训练 xgboost", test_train)
    step("2.2 实验列表", test_experiments)
    step("2.3 最优模型", test_best)
    step("2.4 全量预测", test_predict)
    step("2.4b 预测回写验证", test_predict_verify)
    step("2.6 模型可视化", test_model_viz)
    step("4.1 高潜筛选", test_targets)
    step("4.3 Prompt 获取", test_prompt)
    step("5.1 日志查询", test_logs)
    step("RBAC 权限拦截", test_rbac)

    print("=" * 40)
    passed = len(STEPS) - len(FAILED)
    print(f"冒烟测试结果：{passed}/{len(STEPS)} 通过")
    if FAILED:
        print(f"失败步骤: {', '.join(FAILED)}")
    print(f"总耗时：{time.time() - start:.1f}s")
    print("=" * 40)


if __name__ == "__main__":
    main()
