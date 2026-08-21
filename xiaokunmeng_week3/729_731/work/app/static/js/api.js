/* API 封装：统一请求 + JWT 鉴权 + 401 处理 */

const API = {
    base: "/api/v1",

    get token() {
        return localStorage.getItem("token");
    },
    set token(v) {
        localStorage.setItem("token", v);
    },
    get user() {
        return JSON.parse(localStorage.getItem("user") || "null");
    },
    set user(v) {
        localStorage.setItem("user", JSON.stringify(v));
    },

    async request(method, path, body) {
        const headers = {};
        if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
        const opts = { method, headers };
        if (body !== undefined) {
            headers["Content-Type"] = "application/json";
            opts.body = JSON.stringify(body);
        }
        let resp;
        try {
            resp = await fetch(this.base + path, opts);
        } catch (e) {
            return { code: -1, message: "网络错误，请检查服务是否启动" };
        }
        let data = {};
        try { data = await resp.json(); } catch (e) { /* 非 JSON 响应 */ }

        // 401：token 失效/过期 → 跳登录
        if (data.code === 1002) {
            this.logout();
            App.toLogin();
        }
        return data;
    },

    upload(path, file) {
        const fd = new FormData();
        fd.append("file", file);
        const headers = {};
        if (this.token) headers["Authorization"] = `Bearer ${this.token}`;
        return fetch(this.base + path, { method: "POST", headers, body: fd })
            .then(r => r.json().catch(() => ({})));
    },

    get(path) { return this.request("GET", path); },
    post(path, body) { return this.request("POST", path, body); },
    put(path, body) { return this.request("PUT", path, body); },
    del(path) { return this.request("DELETE", path); },

    logout() {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
    }
};
