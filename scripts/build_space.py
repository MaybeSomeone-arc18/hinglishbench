#!/usr/bin/env python3
"""Build the static Space: leaderboard + per-item explorer + methodology, no live paid inference."""
import json, glob, html, os

HB = '/home/sandbox/hinglishbench'
MODELS = {"reflection/Beam-1.0-501B-A23B": "Beam-1.0-501B-A23B",
          "google/gemma-3-27b-it": "Gemma-3-27B-it",
          "Qwen/Qwen3-32B": "Qwen3-32B"}

def load():
    recs = []
    for f in glob.glob(f'{HB}/runs/v2_gsm8k_*.jsonl'):
        for l in open(f):
            r = json.loads(l)
            if 'error' not in r: recs.append(r)
    return recs

recs = load()
items = {json.loads(l)['id']: json.loads(l) for l in open(f'{HB}/data/gsm8k_hinglish.jsonl')}

board = []
for m, mname in MODELS.items():
    row = {'model': mname}
    for lang in ('en', 'hi'):
        sub = [r for r in recs if r['model'] == m and r['lang'] == lang]
        if sub:
            row[f'acc_{lang}'] = round(100*sum(r['correct'] for r in sub)/len(sub), 1)
            row[f'tok_{lang}'] = round(sum(r['completion_tokens'] for r in sub)/len(sub), 1)
    en = {r['id']: r for r in recs if r['model']==m and r['lang']=='en'}
    hi = {r['id']: r for r in recs if r['model']==m and r['lang']=='hi'}
    both = set(en)&set(hi)
    if both:
        tax = sorted(hi[i]['completion_tokens']/max(en[i]['completion_tokens'],1) for i in both)
        row['median_tax'] = round(tax[len(tax)//2], 2)
    board.append(row)

explorer = []
for iid, it in sorted(items.items()):
    entry = {'id': iid, 'en': it['en'], 'hi': it['hi'], 'answer': it['answer'], 'models': {}}
    for m, mname in MODELS.items():
        entry['models'][mname] = {lang: None for lang in ('en','hi')}
        for lang in ('en','hi'):
            r = next((x for x in recs if x['model']==m and x['lang']==lang and x['id']==iid), None)
            if r:
                entry['models'][mname][lang] = {'pred': r.get('pred'), 'correct': r['correct'],
                                                 'tokens': r['completion_tokens'], 'raw': r['raw'][:1500]}
    explorer.append(entry)

data = {'leaderboard': board, 'items': explorer}
with open(f'{HB}/space/data.js', 'w') as f:
    f.write('const DATA = ' + json.dumps(data, ensure_ascii=False) + ';')
print(f"space data: {len(board)} models, {len(explorer)} items")
