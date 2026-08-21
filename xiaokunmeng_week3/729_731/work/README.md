# 🛡️ 保险精准营销系统（Insurance AI）

AI 驱动的保险智能营销平台：用 **XGBoost/随机森林/逻辑回归** 预测客户购买车险概率，识别高潜客户，并调用**大模型（LLM）**自动生成个性化营销邮件，实现「数据 → 建模 → 预测 → 营销」全链路闭环。

---

## 目录

- [项目简介](#项目简介)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [目录结构与代码作用](#目录结构与代码作用)
- [业务数据流](#业务数据流)
- [权限体系（RBAC）](#权限体系rbac)
- [快速开始（本地运行）](#快速开始本地运行)
- [Docker 部署](#docker-部署)
- [API 接口概览](#api-接口概览)
- [测试](#测试)

---

## 项目简介

公司拥有 38 万+ 已购人寿保险的用户数据，本系统基于这些数据：

1. **预测**：机器学习模型输出每个客户的购买车险概率（Response_prob），解决"谁更可能买"
2. **筛选**：按概率阈值/分位筛出高潜客户（如概率 ≥ 0.7）
3. **营销**：大模型根据客户画像自动生成个性化营销邮件，替代人工撰写

**核心价值**：把营销资源从"全量撒网"转向"高潜客户精准触达"，降低人力成本、提升转化率。

---

## 功能特性

| 模块 | 能力 |
|------|------|
| 🔐 **认证与权限** | 注册/登录/JWT/登出（黑名单失效）、RBAC 权限隔离（admin/user） |
| 📤 **数据管理** | Excel 批量上传（10MB 限制、重复 id 去重）、质量报告、统计、EDA 可视化 |
| 🤖 **模型中心** | 三算法一键训练（全部超参可调）、ROC-AUC 自动选优、实验记录、评估可视化、模型导入导出 |
| 🎯 **智能预测** | 全量预测回写概率、按阈值/分位筛选高潜客户 |
| ✉️ **邮件营销** | LLM 批量生成个性化邮件、Prompt 模板在线编辑、邮件记录/详情 |
| 📋 **操作日志** | 关键操作审计、按用户/动作过滤 |
| 📊 **仪表盘** | 关键指标总览、潜在用户 Top、数据健康度、快捷操作 |

---

## 技术栈

| 分类 | 技术 |
|------|------|
| Web 框架 | Flask 3.x（MVC 分层架构） |
| ORM | SQLAlchemy 2.0（原生，模型层与框架解耦） |
| 数据校验 | Pydantic 2.x |
| 认证 | python-jose（JWT）+ bcrypt（密码哈希） |
| 机器学习 | scikit-learn / XGBoost / joblib |
| 数据处理 | pandas / numpy / openpyxl |
| 可视化 | matplotlib / seaborn（输出 base64 PNG） |
| 大模型 | openai SDK（OpenAI 兼容协议：deepseek/qwen/glm） |
| 前端 | Bootstrap 5 + 原生 JS（SPA，hash 路由） |
| 部署 | Docker + docker-compose + SQLite |

---

## 目录结构与代码作用

```
work/
├── run_flask.py                 # 启动入口：python run_flask.py
├── requirements.txt             # 依赖清单
├── Dockerfile                   # 镜像定义（清华 apt/pip 源适配国内）
├── docker-compose.yml           # 一键部署（端口/环境变量/数据卷）
├── .dockerignore                # 构建排除清单（密钥/数据/缓存不入镜像）
├── .env.example                 # 环境变量模板（复制为 .env 使用）
├── .env                         # 环境变量（密钥，勿提交）
├── scripts/                     # 开发工具脚本
│   ├── gen_sample.py            #   生成测试样本 Excel（1000 行）
│   ├── smoke_test.py            #   16 步自动化冒烟测试
│   └── gen_postman.py           #   生成 Postman 集合 JSON
├── instance/                    # 运行时 SQLite 数据库
├── data/                        # 模型文件(.joblib)/可视化图片/样本数据
├── docs/                        # 项目文档（PRD/API/测试方案等）
└── app/                         # 应用核心代码
    ├── __init__.py              # 应用工厂 create_app()：建表、种子 admin、异常处理器
    ├── core/                    # 【基础设施层】各层共用工具
    │   ├── config.py            #   配置管理：读 .env，JWT 密钥强校验
    │   ├── database.py          #   引擎/会话/Base + 请求级 DB 管理
    │   ├── response.py          #   统一响应 {code,message,data} + BizException
    │   ├── security.py          #   bcrypt 密码哈希 + JWT 签发/校验
    │   ├── dependencies.py      #   @login_required / @role_required 鉴权装饰器
    │   ├── logger.py            #   操作日志装饰器 @log_action
    │   └── parser.py            #   请求体 Pydantic 解析 parse_body()
    ├── models/                  # 【数据层】ORM 表（类方法封装操作）
    │   ├── user.py              #   用户表（登录锁定/令牌版本）
    │   ├── customer.py          #   客户表（bulk_create/paginate/高潜筛选）
    │   ├── experiment.py        #   模型实验记录表（指标+参数+可视化数据）
    │   ├── prompt_template.py   #   Prompt 模板表
    │   ├── email_record.py      #   邮件记录表
    │   ├── operation_log.py     #   操作日志表
    │   └── token_blacklist.py   #   JWT 黑名单表（登出失效）
    ├── schemas/                 # 【校验层】Pydantic 请求模型
    │   ├── auth.py              #   登录/注册/改密等请求体
    │   ├── email.py             #   邮件生成/模板/记录请求体
    │   └── model.py             #   训练请求体（算法/超参/划分）
    ├── services/                # 【业务层】编排业务流程
    │   ├── data_service.py      #   Excel 导入/统计/质量/EDA
    │   ├── ml_service.py        #   三算法训练/预测/导入导出/评估
    │   ├── llm_service.py       #   大模型调用（严格 JSON 生成邮件）
    │   └── email_service.py     #   高潜筛选/邮件生成/记录管理
    ├── utils/                   # 【工具层】纯函数
    │   ├── data_processor.py    #   Excel 解析 + 特征工程（编码/缩放）
    │   ├── visualizer.py        #   图表生成（base64 + 本地保存）
    │   └── pagination.py        #   分页参数统一校验
    ├── api/v1/                  # 【表现层】路由（Blueprint）
    │   ├── __init__.py          #   蓝图聚合注册
    │   ├── auth.py              #   认证路由（register/login/me/logout/users/...）
    │   ├── data.py              #   数据路由（upload/customers/statistics/quality/...）
    │   ├── model.py             #   模型路由（train/predict/export/import/...）
    │   ├── email.py             #   邮件路由（targets/generate/prompt/records）
    │   └── log.py               #   日志路由（仅 admin）
    └── static/                  # 前端 SPA
        ├── index.html           #   登录页 + 侧边栏 + 7 个功能视图
        ├── css/app.css          #   设计体系（保单文件：墨水/暖纸/金印章）
        └── js/
            ├── api.js           #   fetch 封装（JWT 携带/401 处理）
            └── app.js           #   SPA 逻辑（hash 路由/RBAC 菜单/各视图渲染）
```

### 分层调用规则

```
表现层 api/v1 ──→ 业务层 services ──→ 数据层 models
     │                  │                │
     └── core 基础设施（config/db/安全/响应）──┘
                          utils 工具层
```

上层依赖下层，下层不感知上层；基础设施层被所有层共用。

---

## 业务数据流

```
① 数据上传
   Excel → parse_excel 校验 → Customer.bulk_create 分批入库(5000/批)

② 数据查看
   统计 / 质量报告 / EDA 可视化（客户画像全貌）

③ 模型训练（admin）
   Customer 数据 → 特征工程 → 三算法训练 → ROC-AUC 选优 → 存 .joblib + 实验记录

④ 全量预测（admin）
   加载最优模型 → predict_proba → 回写 customers.predicted_prob

⑤ 高潜筛选
   按概率阈值(≥0.7) 或 top 10% 分位 → 高潜客户列表

⑥ 邮件营销
   高潜客户画像 → 反编码为自然语言 → LLM 生成个性化邮件 → 入库/查看
```

---

## 权限体系（RBAC）

| 角色 | 可用 | 不可用 |
|------|------|--------|
| **admin** | 全部功能 | — |
| **user** | 数据查看、高潜查看、邮件生成、Prompt 编辑 | 模型训练、数据上传、实验记录、模型评估、预测执行、模型导入导出、操作日志 |

- 注册时服务端硬编码 `user` 角色，防越权提权
- 前端按角色生成菜单（admin 7 项 / user 5 项），后端 `@role_required` 双重拦截

---

## 快速开始（本地运行）

### 1. 准备环境

```bash
cd work
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入密钥：

```bash
cp .env.example .env   # Windows: copy .env.example .env
```

`.env` 中 `JWT_SECRET_KEY` 必须为 ≥16 位强随机密钥（可用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成）。

### 3. 启动

```bash
python run_flask.py
```

浏览器访问 `http://localhost:5000`，登录账号 **admin / admin123**（首次启动自动创建）。

### 4. 快速体验流程

```
登录 admin → 数据管理上传 data.xlsx → 模型中心训练 → 智能预测 → 邮件营销生成
```

（测试可用 `python -m scripts.gen_sample` 生成 1000 行样本数据）

---

## Docker 部署

> 国内网络需先配置 Docker 镜像加速（Settings → Docker Engine → registry-mirrors）。

```bash
cd work
docker compose build     # 构建镜像（首次 3-8 分钟）
docker compose up -d     # 启动
docker compose ps        # 状态 Up (healthy)
```

访问 `http://localhost:5000`。日志：`docker compose logs -f insurance-ai`。

**数据持久化**：`./instance`（数据库）、`./data`（模型/图片）通过数据卷挂载，容器删除后数据保留。

---

## API 接口概览

所有接口统一返回 `{code, message, data}`，需鉴权接口携带 `Authorization: Bearer <token>`。

| 模块 | 前缀 | 主要接口 |
|------|------|---------|
| 认证 | `/api/v1/auth` | register / login / me / logout / users / profile / password |
| 数据 | `/api/v1/data` | upload / customers / statistics / quality / visualization |
| 模型 | `/api/v1/model` | train / experiments / best / predict / export / import / visualization |
| 邮件 | `/api/v1/email` | targets / generate / prompt / records |
| 日志 | `/api/v1/logs` | 操作日志（仅 admin） |

完整契约见 `docs/03_API接口文档.md`，Postman 集合由 `python -m scripts.gen_postman` 生成。

### 业务码

| code | 含义 |
|------|------|
| 0 | 成功 |
| 1001 | 参数错误 |
| 1002 | 未授权/认证失败 |
| 1003 | 权限不足 |
| 1004 | 用户名已存在 |
| 2001 | 资源不存在 |
| 2002 | Excel 解析失败 |
| 3002 | 无最佳模型/未预测 |
| 5000 | 服务器内部错误 |

---

## 测试

```bash
python -m scripts.smoke_test    # 16 步自动化冒烟测试（认证→上传→训练→预测→邮件→日志→RBAC）
```

冒烟测试覆盖全部核心链路，全部 `[OK]` 即通过。
