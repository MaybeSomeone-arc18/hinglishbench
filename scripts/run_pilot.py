#!/usr/bin/env python3
"""HinglishBench pilot: run Beam on parallel EN/Hinglish items, exact-match grade, log tokens."""
import json, os, re, sys, time, urllib.request

TOKEN = open('/home/sandbox/.hf_hinglishbench_token').read().strip()
URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "reflection/Beam-1.0-501B-A23B"
SYSTEM = "You are answering a benchmark question. Reply with ONLY the final numeric answer (digits only, no units, no explanation)."

def call(prompt, max_retries=3):
    body = json.dumps({
        "model": MODEL, "reasoning_effort": "low", "max_tokens": 2000,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
    }).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={
                "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception as e:
            if attempt == max_retries - 1: raise
            time.sleep(5 * (attempt + 1))

def extract_number(text):
    if not text: return None
    m = re.findall(r'-?\d[\d,]*\.?\d*', text.strip())
    if not m: return None
    try: return float(m[-1].replace(',', ''))
    except ValueError: return None

def main():
    items = [json.loads(l) for l in open('/home/sandbox/hinglishbench/data/reasoning_pilot.jsonl')]
    out_path = '/home/sandbox/hinglishbench/runs/pilot_v0.jsonl'
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)['key'] for l in open(out_path)}
    out = open(out_path, 'a')
    for item in items:
        for lang in ('en', 'hi'):
            key = f"{item['id']}:{lang}"
            if key in done: continue
            resp = call(item[lang])
            msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
            pred = extract_number(msg.get('content', ''))
            rec = {"key": key, "id": item['id'], "lang": lang, "prompt": item[lang],
                   "answer": item['answer'], "raw": msg.get('content', ''),
                   "pred": pred, "correct": (pred is not None and abs(pred - item['answer']) < 1e-6),
                   "prompt_tokens": usage.get('prompt_tokens'), "completion_tokens": usage.get('completion_tokens'),
                   "reasoning_tokens": usage.get('completion_tokens_details', {}).get('reasoning_tokens')}
            out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush()
            print(f"{key} pred={pred} ans={item['answer']} ok={rec['correct']} comp_tok={rec['completion_tokens']}", flush=True)
    out.close()

    recs = [json.loads(l) for l in open(out_path)]
    for lang in ('en', 'hi'):
        sub = [r for r in recs if r['lang'] == lang]
        if not sub: continue
        acc = sum(r['correct'] for r in sub) / len(sub)
        avg_comp = sum(r['completion_tokens'] for r in sub) / len(sub)
        avg_reas = sum(r['reasoning_tokens'] or 0 for r in sub) / len(sub)
        print(f"[{lang}] n={len(sub)} acc={acc:.2%} avg_completion_tok={avg_comp:.0f} avg_reasoning_tok={avg_reas:.0f}")

if __name__ == '__main__':
    main()
