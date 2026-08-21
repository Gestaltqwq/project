# -*- coding: utf-8 -*-
"""EasyDataset API driver (local server http://127.0.0.1:1717)."""
import json, sys, time, urllib.request, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'http://127.0.0.1:1717'
PROJECT = 'p8enYumHAED2'

# Model config from the existing completed task (DeepSeek, user's key)
MODEL_INFO = {
    "id": "rRw6neHOO3j59QAtmJC3z",
    "projectId": PROJECT,
    "providerId": "deepseek",
    "providerName": "DeepSeek",
    "endpoint": "https://api.deepseek.com/v1/",
    "apiKey": "sk-cd096381e2e2413e976ecd5252093e04",
    "modelId": "deepseek-v4-flash",
    "modelName": "deepseek-v4-flash",
    "type": "text",
    "temperature": 0.4,
    "maxTokens": 8192,
    "topP": 0.9,
    "topK": 0,
    "status": 1,
}


def req(method, path, body=None, timeout=30):
    url = BASE + path
    data = json.dumps(body).encode('utf-8') if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
                               headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


def create_task(task_type, note, total_count=0):
    body = {
        'taskType': task_type,
        'modelInfo': MODEL_INFO,
        'language': 'zh-CN',
        'detail': '',
        'totalCount': total_count,
        'note': note,
    }
    st, data = req('POST', f'/api/projects/{PROJECT}/tasks', body)
    print(f'[create_task] {task_type} -> status {st}')
    if st == 200:
        print('  task id:', data.get('data', {}).get('id'))
    else:
        print('  response:', str(data)[:500])
    return data.get('data', {}).get('id') if st == 200 else None


def task_status(task_id):
    st, data = req('GET', f'/api/projects/{PROJECT}/tasks/list?status=0')
    if st == 200:
        for t in data if isinstance(data, list) else data.get('data', []):
            if t.get('id') == task_id:
                return t
    return None


def poll_task(task_id, poll_sec=15, max_wait=7200):
    """Poll task until terminal. Returns final task dict."""
    start = time.time()
    while time.time() - start < max_wait:
        t = task_status(task_id)
        if t is None:
            # try direct endpoint
            st, d = req('GET', f'/api/projects/{PROJECT}/tasks/list?page=0&limit=50')
            if st == 200:
                items = d if isinstance(d, list) else d.get('data', [])
                t = next((x for x in items if x.get('id') == task_id), None)
        if t:
            status = t.get('status')
            note = (t.get('note') or '')[:200]
            detail = (t.get('detail') or '')[:160]
            done = t.get('completedCount')
            total = t.get('totalCount')
            print(f'  [{time.strftime("%H:%M:%S")}] status={status} done={done}/{total} note={note} detail={detail}')
            if status in (1, 2, 3):  # completed / failed / interrupted
                return t
        time.sleep(poll_sec)
    return None


def db_count(table, where=''):
    import sqlite3
    con = sqlite3.connect(r'C:\Users\LENOVO\AppData\Roaming\easy-dataset\local-db\db.sqlite')
    cur = con.cursor()
    n = cur.execute(f'SELECT COUNT(*) FROM {table} {where}').fetchone()[0]
    con.close()
    return n


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else ''
    if mode == 'retry-questions':
        failed = ["9yWGFgR6actEfgdn0XiKz", "mrDm9vWiMMDb7mx35eS4u", "2E8j5v_L3BMmsfNrP5lMG",
                  "i_0umcDkbnRtzoK3ezNeB", "k4kBBWcCsCIcjJhiOXcgv", "IJe1lcW2lUSk8Xdc_ITCS",
                  "rtIA6O5iLwinHDSQU4sDC", "__P94ZXCgnR_Qn0g0_nTF", "4ZfP8GtYqL2-jl0dMy1dt",
                  "y11rppDq8bSYKCHdH1r0j", "B8xoLiHQzHFNkWiI2uRD_"]
        tid = create_task('question-generation', {'chunkIds': failed}, len(failed))
        print('task:', tid)
    elif mode == 'topup-questions':
        chunk_ids = json.loads(sys.argv[2])
        tid = create_task('question-generation', {'chunkIds': chunk_ids}, len(chunk_ids))
        print('task:', tid)
    elif mode == 'poll':
        tid = sys.argv[2]
        t = poll_task(tid)
        print('FINAL:', json.dumps({k: t.get(k) for k in ('id', 'status', 'completedCount', 'totalCount', 'note')}, ensure_ascii=False) if t else None)
    elif mode == 'answers':
        tid = create_task('answer-generation', {}, 0)
        print('task:', tid)
    elif mode == 'counts':
        print('questions:', db_count('Questions'))
        print('datasets:', db_count('Datasets'))
        print('answered:', db_count('Questions', 'WHERE answered=1'))
