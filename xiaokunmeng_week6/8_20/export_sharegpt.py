# -*- coding: utf-8 -*-
"""Assemble ShareGPT dataset from EasyDataset Datasets table and save into 8_20."""
import sqlite3, sys, io, json, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

DB = r'C:\Users\LENOVO\AppData\Roaming\easy-dataset\local-db\db.sqlite'
OUT_DIR = r'D:\code\2026\7_8月实训\project\xiaokunmeng_week6\8_20'
include_cot = '--with-cot' in sys.argv

con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute("""
  SELECT questionId, question, answer, cot, chunkName, questionLabel, confirmed, createAt
  FROM Datasets
  WHERE projectId='p8enYumHAED2'
  ORDER BY createAt ASC
""").fetchall()
con.close()

# dedup by questionId, keep the LATEST row per question
best = {}
for r in rows:
    if not (r['question'] or '').strip() or not (r['answer'] or '').strip():
        continue
    best[r['questionId']] = r  # later rows overwrite earlier ones (keep latest)
rows = list(best.values())
print(f'unique questions with valid Q&A: {len(rows)} (raw rows: {len(rows) + sum(1 for r in [] )})')

entries = []
skipped = 0
for r in rows:
    q = (r['question'] or '').strip()
    a = (r['answer'] or '').strip()
    if not q or not a:
        skipped += 1
        continue
    conv = [{'from': 'human', 'value': q}, {'from': 'gpt', 'value': a}]
    item = {'conversations': conv}
    if r['questionLabel']:
        item['label'] = r['questionLabel']
    if include_cot and r['cot']:
        item['cot'] = r['cot']
    entries.append(item)

stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
fn = f'sharegpt_easydataset_{len(entries)}_pairs_{stamp}.json'
json_path = OUT_DIR + '\\' + fn
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(entries, f, ensure_ascii=False, indent=2)

jsonl_path = json_path.replace('.json', '.jsonl')
with open(jsonl_path, 'w', encoding='utf-8') as f:
    for it in entries:
        f.write(json.dumps(it, ensure_ascii=False) + '\n')

print(f'entries: {len(entries)}, skipped: {skipped}')
print(f'saved: {json_path}')
print(f'saved: {jsonl_path}')
