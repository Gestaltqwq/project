# -*- coding: utf-8 -*-
"""Validate the exported ShareGPT dataset file."""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

path = sys.argv[1]
with open(path, encoding='utf-8') as f:
    data = json.load(f)

assert isinstance(data, list), 'root must be a list'
print(f'total entries: {len(data)}')

roles_ok = 0
bad = []
qs = set()
dup_q = 0
empty_a = 0
for i, item in enumerate(data):
    conv = item.get('conversations')
    if not isinstance(conv, list) or len(conv) < 2:
        bad.append((i, 'conversations missing/short'))
        continue
    froms = [m.get('from') for m in conv]
    if froms[:2] == ['human', 'gpt']:
        roles_ok += 1
    q = conv[0].get('value', '')
    a = conv[1].get('value', '')
    if q in qs:
        dup_q += 1
    qs.add(q)
    if not a.strip():
        empty_a += 1

print(f'entries with human->gpt roles: {roles_ok}')
print(f'duplicate questions: {dup_q}')
print(f'empty answers: {empty_a}')
print(f'malformed: {len(bad)}')
if bad[:5]:
    print('malformed examples:', bad[:5])

print('\n--- 3 samples ---')
for item in data[:3]:
    conv = item['conversations']
    print('Q:', conv[0]['value'][:100])
    print('A:', conv[1]['value'][:150])
    print('label:', item.get('label', ''))
    print('---')
