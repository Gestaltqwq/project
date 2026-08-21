from flask import Flask, request, jsonify, session, render_template
from datetime import datetime
import secrets
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.json.ensure_ascii = False

# Session 配置 —— 让前端（同源）能够正常使用 cookie
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cms.db')#数据库文件路径


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    #存储新闻
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            category   TEXT    DEFAULT '默认',
            created_at TEXT    NOT NULL
        )
    ''')

    #存储账号信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT    UNIQUE NOT NULL,
            password TEXT    NOT NULL,
            role     TEXT    DEFAULT 'user'
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('admin', 'admin123', 'admin')
        )
        print("创建管理员账号：admin / admin123")

    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def admin_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        if 'username' not in session:
            return jsonify({"code": 401, "msg": "请先登录"}), 401
        if session.get('role') != 'admin':
            return jsonify({"code": 403, "msg": "权限不足，需要管理员权限"}), 403
        return func(*args, **kwargs)
    return decorated

COMPANY_INFO = {
    "name": "示例名字",
    "slogan": "示例口号",
    "description": (
        "示例描述"
    ),
    "founded": "2020",
    "location": "四川省成都市双流区",
    "employees": "500"
}

@app.route('/app')
def frontend():
    return render_template('cms_frontend.html')

@app.route('/', methods=['GET'])
def index():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content, category, created_at "
        "FROM news ORDER BY created_at DESC LIMIT 3"
    )
    latest_news = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        "code": 200,
        "data": {
            "company": COMPANY_INFO,
            "latest_news": latest_news
        }
    })

@app.route('/api/news', methods=['GET'])
def get_news_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content, category, created_at "
        "FROM news ORDER BY created_at DESC"
    )
    news_list = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "code": 200,
        "data": news_list,
        "total": len(news_list)
    })


@app.route('/api/news/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content, category, created_at "
        "FROM news WHERE id = ?",
        (news_id,)
    )
    row = cursor.fetchone()
    conn.close()

    if row is None:
        return jsonify({"code": 404, "msg": "新闻不存在"}), 404

    return jsonify({
        "code": 200,
        "data": dict(row)
    })


@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"code": 400, "msg": "用户名和密码不能为空"}), 400
    username = data['username'].strip()
    password = data['password']
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
        (username, password, 'user')
    )
    conn.commit()
    conn.close()

    return jsonify({
        "code": 200,
        "msg": "注册成功",
        "data": {"username": username, "role": 'user'}
    }), 201

@app.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"code": 400, "msg": "没有读取到username和password"}), 400
    username = data['username']
    password = data['password']

    #查询用户
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT username, password, role FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()
    conn.close()

    if user is None or user['password'] != password:
        return jsonify({"code": 401, "msg": "用户名或密码错误"}), 401

    session['username'] = user['username']
    session['role'] = user['role']
    session.permanent = True

    return jsonify({
        "code": 200,
        "msg": "登录成功",
        "data": {
            "username": user['username'],
            "role": user['role']
        }
    })


@app.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"code": 200, "msg": "已退出登录"})
@app.route('/admin/news', methods=['POST'])
@admin_required#登录验证是否为管理员
def publish_news():
    data = request.get_json()
    if not data or not data.get('title') or not data.get('content'):
        return jsonify({"code": 400, "msg": "标题和内容不能为空"}), 400
    title = data['title']
    content = data['content']
    category = data.get('category', '默认') 
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #插入数据库
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO news (title, content, category, created_at) VALUES (?, ?, ?, ?)",
        (title, content, category, created_at)
    )
    conn.commit()
    news_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "code": 200,
        "msg": "新闻发布成功",
        "data": {
            "id": news_id,
            "title": title,
            "content": content,
            "category": category,
            "created_at": created_at
        }
    }), 201


@app.route('/admin/news/<int:news_id>', methods=['DELETE'])
@admin_required#登录验证是否为管理员
def delete_news(news_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM news WHERE id = ?", (news_id,))
    row = cursor.fetchone()
    if row is None:
        conn.close()
        return jsonify({"code": 404, "msg": "新闻不存在"}), 404
    cursor.execute("DELETE FROM news WHERE id = ?", (news_id,))
    conn.commit()
    conn.close()
    return jsonify({"code": 200, "msg": "新闻删除成功"})

if __name__ == '__main__':
    app.run(host="127.0.0.1", port=5006, debug=True)
