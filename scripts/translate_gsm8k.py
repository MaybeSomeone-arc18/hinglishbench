#!/usr/bin/env python3
"""Translate GSM8K-100 EN items to romanized Hinglish using Beam. Numbers/names must stay identical."""
import json, os, re, sys, time, urllib.request

TOKEN = open('/home/sandbox/.hf_hinglishbench_token').read().strip()
URL = "https://router.huggingface.co/v1/chat/completions"
PROMPT = ("Translate the following English math word problem into natural Hinglish - the Hindi-English "
          "code-mixed style Indian students actually speak, written in English letters only (NO Devanagari). "
          "Rules: keep every number, unit, and name exactly unchanged; keep it a question; output ONLY the translated problem, no commentary.\n\n")

def call(prompt, max_retries=3):
    body = json.dumps({"model": "reflection/Beam-1.0-501B-A23B", "reasoning_effort": "low", "max_tokens": 1500,
        "messages": [{"role": "user", "content": PROMPT + prompt}]}).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception:
            if attempt == max_retries - 1: raise
            time.sleep(6 * (attempt + 1))

def nums(s):
    return re.findall(r'\d[\d,]*\.?\d*', s)

items = [json.loads(l) for l in open('data/gsm8k_100_en.jsonl')]
out_path = 'runs/gsm8k_hi_translations.jsonl'
done = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
out = open(out_path, 'a')
for it in items:
    if it['id'] in done: continue
    resp = call(it['en'])
    msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
    hi = msg.get('content', '').strip()
    same_numbers = sorted(nums(it['en'])) == sorted(nums(hi))
    rec = {"id": it['id'], "en": it['en'], "hi": hi, "answer": it['answer'],
           "numbers_preserved": same_numbers, "completion_tokens": usage.get('completion_tokens')}
    out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush()
    print(f"{it['id']} numbers_ok={same_numbers} comp={usage.get('completion_tokens')}", flush=True)
out.close()
recs = [json.loads(l) for l in open(out_path)]
bad = [r['id'] for r in recs if not r['numbers_preserved']]
print(f"done: {len(recs)} translated, {len(bad)} with number mismatches: {bad}")
