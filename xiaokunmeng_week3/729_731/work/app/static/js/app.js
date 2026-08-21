/* 前端 SPA：hash 路由 + RBAC 菜单 + 页面整合 */

// ===== 菜单定义（整合后：admin 7 项 / user 5 项）=====
const MENUS = {
    admin: [
        { hash: "#/dashboard", label: "仪表盘", view: "dashboard", icon: "📊" },
        { hash: "#/data", label: "数据管理", view: "data", icon: "📤" },
        { hash: "#/eda", label: "数据分析", view: "eda", icon: "📈" },
        { hash: "#/model", label: "模型中心", view: "model", icon: "🤖" },
        { hash: "#/predict", label: "智能预测", view: "predict", icon: "🎯" },
        { hash: "#/email", label: "邮件营销", view: "email", icon: "✉️" },
        { hash: "#/logs", label: "操作日志", view: "logs", icon: "📋" },
    ],
    user: [
        { hash: "#/dashboard", label: "仪表盘", view: "dashboard", icon: "📊" },
        { hash: "#/data", label: "数据管理", view: "data", icon: "📤" },
        { hash: "#/eda", label: "数据分析", view: "eda", icon: "📈" },
        { hash: "#/predict", label: "智能预测", view: "predict", icon: "🎯" },
        { hash: "#/email", label: "邮件营销", view: "email", icon: "✉️" },
    ],
};

// 子 Tab 定义：进入页面时默认激活第一个
const SUB_TABS = {
    data: { default: "data-upload", panes: ["data-upload", "data-stats", "data-quality", "data-customers"] },
    model: { default: "model-train", panes: ["model-train", "model-exp", "model-eval"] },
};

const App = {
    page: 1,
    perPage: 10,
    role: null,
    currentView: null,

    /* ---------- 初始化 ---------- */
    init() {
        document.getElementById("btn-login").onclick = () => this.login();
        document.getElementById("btn-register").onclick = () => this.register();
        document.getElementById("login-mode-toggle").onclick = e => {
            e.preventDefault();
            this.toggleAuthMode();
        };
        document.getElementById("login-password").addEventListener("keydown", e => {
            if (e.key === "Enter") this.login();
        });
        document.getElementById("login-confirm").addEventListener("keydown", e => {
            if (e.key === "Enter") this.register();
        });
        document.getElementById("btn-logout").onclick = () => {
            API.logout();
            location.hash = "#/login";
            this.toLogin();
        };

        // 仪表盘潜在用户筛选
        document.getElementById("btn-dash-filter").onclick = () => this.loadDashboard();
        // 上传
        document.getElementById("btn-upload").onclick = () => this.upload();
        // 客户列表
        document.getElementById("btn-filter").onclick = () => this.loadCustomers(1);
        document.getElementById("page-prev").onclick = () => this.loadCustomers(this.page - 1);
        document.getElementById("page-next").onclick = () => this.loadCustomers(this.page + 1);
        // EDA
        document.querySelectorAll(".eda-btn").forEach(b =>
            b.onclick = () => this.loadEda(b.dataset.ct));
        // 训练 / 预测
        document.getElementById("btn-train").onclick = () => this.train();
        document.getElementById("btn-predict").onclick = () => this.predict();
        // 算法切换 → 动态显示对应超参
        document.getElementById("train-algo").addEventListener("change", e => {
            this.applyAlgoParams(e.target.value);
        });
        // 模型评估
        document.querySelectorAll(".meval-btn").forEach(b =>
            b.onclick = () => this.loadModelEval(b.dataset.ct, b.dataset.model));
        // 高潜筛选
        document.getElementById("btn-targets").onclick = () => this.loadTargets();
        // 邮件
        document.getElementById("btn-generate").onclick = () => this.generateEmails();
        document.getElementById("btn-save-prompt").onclick = () => this.savePrompt();
        // 邮件详情查看（事件委托）
        document.getElementById("email-body").addEventListener("click", e => {
            const btn = e.target.closest(".view-email-btn");
            if (btn) this.viewEmail(Number(btn.dataset.id));
        });

        // 子 Tab 切换（data/model 页面）
        document.querySelectorAll(".sub-tabs .nav-link").forEach(btn =>
            btn.onclick = () => this.switchSubTab(btn));

        // hash 路由
        window.addEventListener("hashchange", () => this.router());
        if (API.token) this.enterApp();
    },

    /* ---------- 登录 / 注册 / 登出 ---------- */
    toggleAuthMode() {
        const toRegister = document.getElementById("btn-register").classList.contains("d-none");
        document.getElementById("login-confirm-wrap").classList.toggle("d-none", !toRegister);
        document.getElementById("btn-register").classList.toggle("d-none", !toRegister);
        document.getElementById("btn-login").classList.toggle("d-none", toRegister);
        document.getElementById("login-mode-toggle").textContent =
            toRegister ? "已有账号？去登录" : "没有账号？立即注册";
        document.getElementById("login-error").classList.add("d-none");
    },

    async login() {
        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;
        const errBox = document.getElementById("login-error");
        if (!username || !password) {
            errBox.textContent = "请输入用户名和密码";
            errBox.classList.remove("d-none");
            return;
        }
        const data = await API.post("/auth/login", { username, password });
        if (data.code !== 0) {
            errBox.textContent = data.message;
            errBox.classList.remove("d-none");
            return;
        }
        API.token = data.data.access_token;
        API.user = data.data.user;
        this.enterApp();
    },

    async register() {
        const username = document.getElementById("login-username").value.trim();
        const password = document.getElementById("login-password").value;
        const confirm = document.getElementById("login-confirm").value;
        const errBox = document.getElementById("login-error");
        if (!username || !password) {
            errBox.textContent = "请输入用户名和密码";
            errBox.classList.remove("d-none");
            return;
        }
        if (password.length < 6) {
            errBox.textContent = "密码至少 6 位";
            errBox.classList.remove("d-none");
            return;
        }
        if (password !== confirm) {
            errBox.textContent = "两次输入的密码不一致";
            errBox.classList.remove("d-none");
            return;
        }
        const data = await API.post("/auth/register", { username, password });
        if (data.code !== 0) {
            errBox.textContent = data.message;
            errBox.classList.remove("d-none");
            return;
        }
        // 注册成功自动登录
        API.token = data.data.access_token;
        API.user = data.data.user;
        this.enterApp();
    },

    enterApp() {
        document.getElementById("login-page").classList.add("d-none");
        document.getElementById("app-page").classList.remove("d-none");
        let user = API.user;
        if (!user) {
            API.get("/auth/me").then(data => {
                if (data.code === 0) { API.user = data.data; this._renderApp(data.data); }
                else { API.logout(); this.toLogin(); }
            });
            return;
        }
        this._renderApp(user);
    },

    _renderApp(user) {
        this.role = user.role;
        document.getElementById("nav-user").innerHTML =
            `<span class="me-2">${this.esc(user.username)}</span>` +
            `<span class="badge bg-light text-primary">${user.role}</span>`;

        const menus = MENUS[user.role] || MENUS.user;
        document.getElementById("menu-list").innerHTML = menus.map(m =>
            `<li class="nav-item"><a class="nav-link menu-item" href="${m.hash}">` +
            `<span class="menu-icon">${m.icon}</span>${m.label}</a></li>`
        ).join("");

        // 权限分离：普通用户隐藏 admin 专属 UI
        if (user.role !== "admin") {
            document.getElementById("sub-upload").classList.add("d-none");      // 数据上传
            document.getElementById("data-upload").classList.add("d-none");     // 上传面板
            document.getElementById("dash-experiment-card").classList.add("d-none"); // 最新实验
        }

        if (!location.hash || location.hash === "#/login") location.hash = menus[0].hash;
        else this.router();
    },

    toLogin() {
        document.getElementById("app-page").classList.add("d-none");
        document.getElementById("login-page").classList.remove("d-none");
    },

    /* ---------- hash 路由 ---------- */
    router() {
        const hash = location.hash || "#/dashboard";
        const menus = MENUS[this.role] || MENUS.user;
        let current = menus.find(m => m.hash === hash);
        if (!current) current = menus[0];

        document.querySelectorAll(".view").forEach(v => v.classList.add("d-none"));
        const el = document.getElementById(`view-${current.view}`);
        if (el) el.classList.remove("d-none");

        document.querySelectorAll(".menu-item").forEach(a =>
            a.classList.toggle("active", a.getAttribute("href") === current.hash));

        this.currentView = current.view;
        this.loadViewData(current.view);
    },

    /* ---------- 子 Tab 切换 ---------- */
    switchSubTab(btn) {
        const paneId = btn.dataset.sub;
        const tabList = btn.closest(".sub-tabs");
        tabList.querySelectorAll(".nav-link").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        // 显示对应子面板，隐藏同组其他
        const parent = btn.closest(".view");
        parent.querySelectorAll(".sub-pane").forEach(p => p.classList.add("d-none"));
        document.getElementById(paneId).classList.remove("d-none");

        // 进入子面板时按需加载数据
        if (paneId === "data-stats") this.loadStats();
        if (paneId === "data-quality") this.loadQuality();
        if (paneId === "data-customers") this.loadCustomers(1);
        if (paneId === "model-exp") this.loadExperiments();
    },

    loadViewData(view) {
        switch (view) {
            case "dashboard": this.loadDashboard(); break;
            case "data": this.switchSubTab(document.querySelector('#view-data .sub-tabs .nav-link.active') || document.querySelector('#view-data .sub-tabs .nav-link')); break;
            case "model": this.applyAlgoParams(document.getElementById("train-algo").value); break;
            case "predict": this.loadTargets(); break;
            case "email": this.loadEmailRecords(); this.loadPrompt(); break;
            case "logs": this.loadLogs(); break;
        }
    },

    /* ---------- 工具 ---------- */
    esc(s) {
        return String(s ?? "").replace(/[&<>"']/g, c => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
        }[c]));
    },
    toast(msg, type = "success") {
        const el = document.createElement("div");
        el.className = `toast show align-items-center text-bg-${type} border-0`;
        el.innerHTML = `<div class="d-flex"><div class="toast-body">${this.esc(msg)}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>`;
        document.querySelector(".toast-container").appendChild(el);
        setTimeout(() => el.remove(), 3500);
    },
    setMsg(id, text, cls = "text-success") {
        const el = document.getElementById(id);
        el.textContent = text;
        el.className = `small mt-2 ${cls}`;
    },
    emptyState(msg = "暂无数据", colspan = 8) {
        return `<tr><td colspan="${colspan}"><div class="empty-state">
            <div class="empty-icon">📭</div><div>${this.esc(msg)}</div></div></td></tr>`;
    },

    /* ================= 仪表盘 ================= */
    async loadDashboard() {
        // 并行拉取统计/最优/质量 + 按阈值筛选潜在用户（实验仅 admin 可查）
        const minProb = parseFloat(document.getElementById("dash-min-prob").value) || 0.7;
        const [stats, best, exps, quality, targets] = await Promise.all([
            API.get("/data/statistics"),
            API.get("/model/best"),
            this.role === "admin"
                ? API.get("/model/experiments?page=1&per_page=5")
                : Promise.resolve({ code: -1, data: null }),
            API.get("/data/quality"),
            API.get(`/email/targets?min_prob=${minProb}&page=1&per_page=10`),
        ]);
        const d = stats.data || {};
        const buy = d.response_distribution ? d.response_distribution["1"] : 0;
        const notBuy = d.response_distribution ? d.response_distribution["0"] : 0;
        const ratio = buy > 0 ? (notBuy / buy).toFixed(1) : "—";
        const t = targets.data || {};
        const highValueCount = t.total ?? "-";
        const highValuePct = t.total && d.total ? Math.round(t.total / d.total * 100) : 0;
        document.getElementById("dash-stats").innerHTML = `
            <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-gold"></span>
                <div class="stat-label">客户总数</div><div class="stat-value">${d.total ?? "-"}</div></div></div>
            <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-moss"></span>
                <div class="stat-label">购买用户</div><div class="stat-value">${buy || "-"}</div></div></div>
            <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-rust"></span>
                <div class="stat-label">潜在用户（概率≥${minProb}）</div><div class="stat-value">${highValueCount}</div></div></div>
            <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-ink"></span>
                <div class="stat-label">最优模型 AUC</div><div class="stat-value">${best.code === 0 ? best.data.roc_auc : "-"}</div></div></div>`;

        // 潜在用户列表
        const customers = t.customers || [];
        document.getElementById("dash-target-count").textContent =
            t.threshold != null ? `共 ${t.total} 位潜在用户（购买概率 ≥ ${t.threshold.toFixed(2)}）` : "";
        document.getElementById("dash-targets").innerHTML = customers.length ? customers.map((c, i) => `
            <tr><td>${i + 1}</td><td>${c.id}</td><td>${this.esc(c.gender)}</td><td>${c.age}</td>
                <td>${c.annual_premium}</td>
                <td><span class="badge badge-soft-gold">${c.predicted_prob.toFixed(4)}</span></td></tr>`).join("")
            : this.emptyState(`暂无购买概率 ≥ ${minProb} 的用户，请调整阈值或先预测`, 6);

        // 数据健康度
        const qd = quality.data || {};
        const miss = qd.missing_values ? Object.values(qd.missing_values).reduce((a, b) => a + b, 0) : "-";
        document.getElementById("dash-health").innerHTML = `
            <div class="d-flex justify-content-between mb-1"><span>数据行数</span><b>${qd.total_rows ?? "-"}</b></div>
            <div class="d-flex justify-content-between mb-1"><span>缺失值</span><b>${miss}</b></div>
            <div class="d-flex justify-content-between mb-1"><span>重复行</span><b>${qd.duplicates ?? "-"}</b></div>
            <div class="d-flex justify-content-between"><span>潜在用户占比</span><b>${highValuePct}%</b></div>`;

        // 最新实验
        const expItems = exps.data ? exps.data.items : [];
        document.getElementById("dash-experiment").innerHTML = expItems.length
            ? expItems.slice(0, 3).map(e => `
                <div class="d-flex justify-content-between mb-1">
                    <span>${this.esc(e.model_name)} ${e.is_best ? '<span class="badge badge-soft-gold">最优</span>' : ""}</span>
                    <b class="mono">AUC ${e.roc_auc}</b></div>`).join("")
            : this.esc("暂无实验，点击「模型中心」开始训练");
    },

    /* ================= 数据管理 ================= */
    async upload() {
        const fileInput = document.getElementById("upload-file");
        if (!fileInput.files.length) { this.setMsg("upload-msg", "请先选择 Excel 文件", "text-danger"); return; }
        const data = await API.upload("/data/upload", fileInput.files[0]);
        if (data.code === 0) {
            this.setMsg("upload-msg", `上传成功，导入 ${data.data.imported_count} 条（非法行 ${data.data.invalid_rows}）`);
            this.toast(`导入 ${data.data.imported_count} 条`);
        } else {
            this.setMsg("upload-msg", data.message, "text-danger");
        }
    },

    async loadCustomers(page) {
        this.page = Math.max(1, page);
        const g = document.getElementById("f-gender").value.trim();
        const amin = document.getElementById("f-age-min").value || "";
        const params = new URLSearchParams({ page: this.page, per_page: this.perPage });
        if (g) params.set("gender", g);
        if (amin) params.set("age_min", amin);
        const data = await API.get(`/data/customers?${params}`);
        if (data.code !== 0) return;
        const d = data.data;
        document.getElementById("customer-body").innerHTML = d.items.length ? d.items.map(c => `
            <tr><td>${c.id}</td><td>${this.esc(c.gender)}</td><td>${c.age}</td>
                <td>${this.esc(c.vehicle_age)}</td><td>${this.esc(c.vehicle_damage)}</td>
                <td>${c.annual_premium}</td>
                <td>${c.predicted_prob != null
                    ? `<span class="badge badge-soft-gold">${c.predicted_prob.toFixed(4)}</span>` : "-"}</td>
                <td>${c.response == 1
                    ? '<span class="badge badge-soft-moss">购买</span>'
                    : '<span class="badge badge-soft-line">未购</span>'}</td></tr>`).join("")
            : this.emptyState("暂无客户数据，请先上传 Excel", 8);
        document.getElementById("customer-info").textContent =
            `共 ${d.total} 条 · 第 ${d.page}/${d.pages || 1} 页`;
    },

    async loadStats() {
        const data = await API.get("/data/statistics");
        if (data.code !== 0) { this.toast(data.message, "warning"); return; }
        const d = data.data;
        const buy = d.response_distribution["1"], notBuy = d.response_distribution["0"];
        const ratio = buy > 0 ? (notBuy / buy).toFixed(1) : "—";
        document.getElementById("stats-box").innerHTML = `
            <div class="row g-3">
                <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-gold"></span>
                    <div class="stat-label">客户总数</div><div class="stat-value">${d.total}</div></div></div>
                <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-moss"></span>
                    <div class="stat-label">购买用户</div><div class="stat-value">${buy}</div></div></div>
                <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-rust"></span>
                    <div class="stat-label">未购买用户</div><div class="stat-value">${notBuy}</div></div></div>
                <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-ink"></span>
                    <div class="stat-label">正负样本比</div><div class="stat-value">1:${ratio}</div></div></div>
                <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-ink"></span>
                    <div class="stat-label">男女分布</div><div class="stat-value">${d.gender_distribution.Male}/${d.gender_distribution.Female}</div></div></div>
                <div class="col-md-3 col-6"><div class="stat-card"><span class="stat-dot dot-gold"></span>
                    <div class="stat-label">年龄范围</div><div class="stat-value">${d.age_stats.min}~${d.age_stats.max}</div></div></div>
            </div>`;
    },

    async loadQuality() {
        const data = await API.get("/data/quality");
        if (data.code !== 0) { this.toast(data.message, "warning"); return; }
        const d = data.data;
        const missEntries = Object.entries(d.missing_values).filter(([, v]) => v > 0);
        const miss = missEntries.length
            ? missEntries.map(([k, v]) => `<span class="badge badge-soft-rust">${k}: ${v}</span>`).join(" ")
            : '<span class="badge badge-soft-moss">无缺失</span>';
        document.getElementById("quality-box").innerHTML = `
            <div class="row g-3">
                <div class="col-md-4 col-6"><div class="stat-card"><span class="stat-dot dot-gold"></span>
                    <div class="stat-label">总行数</div><div class="stat-value">${d.total_rows}</div></div></div>
                <div class="col-md-4 col-6"><div class="stat-card"><span class="stat-dot dot-moss"></span>
                    <div class="stat-label">总列数</div><div class="stat-value">${d.total_cols}</div></div></div>
                <div class="col-md-4 col-6"><div class="stat-card"><span class="stat-dot ${d.duplicates > 0 ? "dot-rust" : "dot-moss"}"></span>
                    <div class="stat-label">重复行</div><div class="stat-value">${d.duplicates}</div></div></div>
            </div>
            <div class="mt-3 small"><b class="text-body">缺失值：</b>${miss}</div>
            <div class="mt-2 small text-secondary"><b>字段类型：</b>${JSON.stringify(d.dtypes)}</div>`;
    },

    /* ================= 数据分析 ================= */
    async loadEda(chartType) {
        const data = await API.get(`/data/visualization/${chartType}`);
        if (data.code !== 0) { this.toast(data.message, "warning"); return; }
        document.getElementById("eda-img").innerHTML =
            `<img src="data:image/png;base64,${data.data.image_base64}" class="img-fluid chart-img">`;
    },

    /* ================= 模型中心 ================= */
    /* 按算法动态显示对应超参（不同模型训练参数不同） */
    applyAlgoParams(algo) {
        const labels = {
            xgboost: "XGBoost",
            random_forest: "随机森林",
            logistic_regression: "逻辑回归",
        };
        document.querySelectorAll(".hp-item").forEach(item => {
            const applicable = item.dataset.algo.split(",");
            const show = algo === "all" || applicable.includes(algo);
            item.style.display = show ? "" : "none";
        });
        document.getElementById("hp-hint").textContent = algo === "all"
            ? "全部算法：树模型用 n_estimators/max_depth，XGBoost 额外用 learning_rate，逻辑回归用 max_iter"
            : `当前算法：${labels[algo] || algo}，已自动显示其支持的训练参数`;
    },

    async train() {
        const btn = document.getElementById("btn-train");
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>训练中';
        this.setMsg("train-msg", "训练中，请稍候...", "text-muted");
        try {
            const algo = document.getElementById("train-algo").value;
            const testSize = parseFloat(document.getElementById("train-test-size").value) || 0.2;
            const randomState = parseInt(document.getElementById("hp-random-state").value) || 42;
            const nEst = parseInt(document.getElementById("hp-n-estimators").value) || 200;
            const maxDepth = parseInt(document.getElementById("hp-max-depth").value) || 6;

            // 读取各算法超参（不同模型训练参数不同）
            const num = id => parseFloat(document.getElementById(id).value);
            const int = id => parseInt(document.getElementById(id).value);
            const params = {};
            if (algo === "all" || algo === "xgboost")
                params.xgboost = {
                    n_estimators: nEst, max_depth: maxDepth,
                    learning_rate: num("hp-lr") || 0.05,
                    subsample: num("hp-subsample") || 0.8,
                    colsample_bytree: num("hp-colsample-bytree") || 0.8,
                    min_child_weight: int("hp-min-child-weight") || 1,
                    gamma: num("hp-gamma") || 0,
                    reg_alpha: num("hp-reg-alpha") || 0,
                    reg_lambda: num("hp-reg-lambda") || 1,
                };
            if (algo === "all" || algo === "random_forest")
                params.random_forest = {
                    n_estimators: nEst, max_depth: maxDepth,
                    min_samples_split: int("hp-min-samples-split") || 2,
                    min_samples_leaf: int("hp-min-samples-leaf") || 1,
                    max_features: document.getElementById("hp-max-features").value.trim() || "sqrt",
                };
            if (algo === "all" || algo === "logistic_regression")
                params.logistic_regression = {
                    C: num("hp-C") || 1,
                    penalty: document.getElementById("hp-penalty").value.trim() || "l2",
                    solver: document.getElementById("hp-solver").value.trim() || "lbfgs",
                    max_iter: int("hp-max-iter") || 1000,
                    tol: num("hp-tol") || 1e-4,
                };

            const body = { test_size: testSize, random_state: randomState, params };
            if (algo !== "all") body.models = [algo];
            const data = await API.post("/model/train", body);
            if (data.code !== 0) { this.setMsg("train-msg", data.message, "text-danger"); return; }
            const d = data.data;
            let html = `<div class="col-12 mb-2"><div class="alert alert-success py-2">
                🏆 最优模型：<b>${this.esc(d.best_model)}</b></div></div>`;
            for (const [name, m] of Object.entries(d.results)) {
                if (m.error) continue;
                html += `<div class="col-md-4 col-6"><div class="card hoverable mb-2"><div class="card-body p-3">
                    <h6 class="mb-2">${this.esc(name)}</h6>
                    <div class="row g-1">
                        <div class="col-6"><div class="metric-card p-2"><div class="metric-label">AUC</div><div class="metric-value">${m.roc_auc}</div></div></div>
                        <div class="col-6"><div class="metric-card p-2"><div class="metric-label">F1</div><div class="metric-value">${m.f1_score}</div></div></div>
                        <div class="col-6"><div class="metric-card p-2"><div class="metric-label">精确率</div><div class="metric-value">${m.precision}</div></div></div>
                        <div class="col-6"><div class="metric-card p-2"><div class="metric-label">召回率</div><div class="metric-value">${m.recall}</div></div></div>
                    </div></div></div></div>`;
            }
            document.getElementById("train-result").innerHTML = html;
            this.setMsg("train-msg", "训练完成");
        } finally {
            btn.disabled = false;
            btn.innerHTML = "开始训练";
        }
    },

    async predict() {
        const btn = document.getElementById("btn-predict");
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>预测中';
        try {
            const data = await API.post("/model/predict", {});
            if (data.code === 0) {
                this.setMsg("train-msg", `预测完成，共 ${data.data.predicted_count} 条`);
                this.toast("全量预测完成");
                this.loadTargets();
            } else {
                this.setMsg("train-msg", data.message, "text-danger");
            }
        } finally {
            btn.disabled = false;
            btn.innerHTML = "全量预测";
        }
    },

    async loadExperiments() {
        const data = await API.get("/model/experiments?page=1&per_page=10");
        if (data.code !== 0) return;
        const items = data.data.items;
        document.getElementById("exp-body").innerHTML = items.length ? `
            <table class="table table-sm"><thead><tr>
                <th style="width:8%">ID</th><th style="width:20%">算法</th><th style="width:12%">AUC</th><th style="width:12%">F1</th><th style="width:10%">最优</th><th style="width:28%">路径</th><th style="width:10%">时间</th></tr></thead><tbody>
            ${items.map(e => `<tr><td>${e.id}</td><td>${e.model_name}</td><td>${e.roc_auc}</td>
                <td>${e.f1_score}</td><td>${e.is_best ? '<span class="badge badge-soft-gold">最优</span>' : ""}</td>
                <td class="col-truncate" title="${this.esc(e.model_path)}">${this.esc(e.model_path)}</td>
                <td>${e.created_at}</td></tr>`).join("")}</tbody></table>`
            : `<div class="empty-state"><div class="empty-icon">🧪</div><div>暂无实验记录</div></div>`;
    },

    async loadModelEval(chartType, model) {
        const q = model ? `?model=${model}` : "";
        const data = await API.get(`/model/visualization/${chartType}${q}`);
        if (data.code !== 0) { this.toast(data.message, "warning"); return; }
        document.getElementById("meval-img").innerHTML =
            `<img src="data:image/png;base64,${data.data.image_base64}" class="img-fluid chart-img">`;
    },

    /* ================= 智能预测 ================= */
    async loadTargets() {
        const percentile = document.getElementById("percentile").value || "0.9";
        const data = await API.get(`/email/targets?percentile=${percentile}&page=1&per_page=20`);
        if (data.code !== 0) { this.toast(data.message, "warning"); return; }
        const d = data.data;
        document.getElementById("target-body").innerHTML = d.customers.length ? d.customers.map((c, i) => `
            <tr><td>${i + 1}</td><td>${c.id}</td><td>${this.esc(c.gender)}</td><td>${c.age}</td>
                <td>${c.annual_premium}</td>
                <td><span class="badge badge-soft-gold">${c.predicted_prob.toFixed(4)}</span></td></tr>`).join("")
            : this.emptyState("暂无高潜客户，请先训练并全量预测", 6);
    },

    /* ================= 邮件营销 ================= */
    async generateEmails() {
        const limit = document.getElementById("email-limit").value || 5;
        const data = await API.post("/email/generate", { limit: Number(limit) });
        if (data.code === 0) {
            const d = data.data;
            this.toast(`生成 ${d.generated_count} 封，失败 ${d.failed_count} 封`, d.failed_count ? "warning" : "success");
            this.loadEmailRecords();
        } else {
            this.toast(data.message, "danger");
        }
    },

    async loadEmailRecords() {
        const data = await API.get("/email/records?page=1&per_page=10");
        if (data.code !== 0) return;
        document.getElementById("email-body").innerHTML = data.data.items.length ? data.data.items.map(r => `
            <tr><td>${r.id}</td><td>${r.customer_id}</td>
                <td class="col-truncate" title="${this.esc(r.email_subject)}">${this.esc(r.email_subject)}</td>
                <td>${this.statusBadge(r.status)}</td>
                <td>${r.created_at || "-"}</td>
                <td><button class="btn btn-sm btn-outline-primary view-email-btn" data-id="${r.id}">查看</button></td></tr>`).join("")
            : this.emptyState("暂无邮件记录", 6);
    },

    /* 查看邮件详情（sandbox iframe 安全渲染 HTML 内容） */
    async viewEmail(id) {
        const data = await API.get(`/email/records/${id}`);
        if (data.code !== 0) { this.toast(data.message, "warning"); return; }
        const r = data.data;
        document.getElementById("email-modal-title").textContent = r.email_subject || "邮件详情";
        const frame = document.getElementById("email-content-frame");
        frame.srcdoc = r.email_content || "<p style='padding:1rem'>（无正文）</p>";
        bootstrap.Modal.getOrCreateInstance(document.getElementById("email-modal")).show();
    },

    statusBadge(status) {
        const map = {
            generated: '<span class="badge badge-soft-moss">已生成</span>',
            failed: '<span class="badge badge-soft-rust">失败</span>',
            edited: '<span class="badge badge-soft-gold">已编辑</span>',
            sent: '<span class="badge badge-soft-gold">已发送</span>',
        };
        return map[status] || `<span class="badge badge-soft-line">${this.esc(status)}</span>`;
    },

    async loadPrompt() {
        const data = await API.get("/email/prompt");
        if (data.code === 0) document.getElementById("prompt-content").value = data.data.content;
    },

    async savePrompt() {
        const content = document.getElementById("prompt-content").value;
        const data = await API.put("/email/prompt", { content });
        if (data.code === 0) this.toast("模板已保存");
        else this.toast(data.message, "danger");
    },

    /* ================= 操作日志 ================= */
    async loadLogs() {
        const data = await API.get("/logs?page=1&per_page=20");
        if (data.code !== 0) return;
        document.getElementById("log-body").innerHTML = data.data.items.length ? data.data.items.map(l => `
            <tr><td>${l.id}</td><td>${this.esc(l.username)}</td><td>${this.esc(l.action)}</td>
                <td class="col-truncate" title="${this.esc(l.details)}">${this.esc(l.details)}</td>
                <td>${l.created_at || "-"}</td></tr>`).join("")
            : this.emptyState("暂无操作日志", 5);
    },
};

document.addEventListener("DOMContentLoaded", () => App.init());
