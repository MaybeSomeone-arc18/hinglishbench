#!/usr/bin/env python3
"""Translate Beam-authored Hinglish items to English (reverse direction). Numbers/units preserved check."""
import json, os, re, time, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

TOKEN = open('/home/sandbox/.hf_hinglishbench_token').read().strip()
URL = "https://router.huggingface.co/v1/chat/completions"
PROMPT = ("Translate the following Hinglish (romanized Hindi-English) math word problem into natural English. "
          "Rules: keep every number, unit, and name exactly unchanged; keep it a question; "
          "output ONLY the translated problem, no commentary.\n\n")

def call(prompt, max_retries=3):
    body = json.dumps({"model": "reflection/Beam-1.0-501B-A23B", "reasoning_effort": "low", "max_tokens": 800,
        "messages": [{"role": "user", "content": PROMPT + prompt}]}).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception as e:
            if attempt == max_retries - 1: return {"error": str(e)}
            time.sleep(6 * (attempt + 1))

def nums(s):
    return re.findall(r'\d[\d,]*\.?\d*', s)

items = [json.loads(l) for l in open('data/hinglish_reasoning_beam_candidates.jsonl')]
out_path = 'runs/beamgen_en_translations.jsonl'
done = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
todo = [it for it in items if it['id'] not in done]
print(f"{len(todo)} to translate", flush=True)
out = open(out_path, 'a')
count = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(call, it['q']): it for it in todo}
    for f in as_completed(futs):
        it = futs[f]; resp = f.result()
        if 'error' in resp:
            print(f"{it['id']} ERROR {resp['error']}", flush=True); continue
        msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
        en = (msg.get('content') or '').strip()
        ok = sorted(nums(it['q'])) == sorted(nums(en))
        out.write(json.dumps({"id": it['id'], "hi": it['q'], "en": en, "answer": it['answer'],
                              "difficulty": it['difficulty'], "topic": it['topic'],
                              "numbers_preserved": ok}, ensure_ascii=False) + '\n'); out.flush()
        count += 1
        if count % 40 == 0: print(f"translated {count}/{len(todo)}", flush=True)
out.close()
recs = [json.loads(l) for l in open(out_path)]
bad = [r['id'] for r in recs if not r['numbers_preserved']]
print(f"done: {len(recs)} translated, {len(bad)} number mismatches: {bad}", flush=True)
