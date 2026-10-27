#!/usr/bin/env python3
"""Mitigation experiment: does an English-reasoning prompt cut the Hinglish token tax on Beam?"""
import json, os, re, time, urllib.request

TOKEN = open('/home/sandbox/.hf_hinglishbench_token').read().strip()
URL = "https://router.huggingface.co/v1/chat/completions"
SYSTEM = ("You are answering a benchmark question written in Hinglish. Think in English if that is easier. "
          "End your reply with a final line containing ONLY the numeric answer (digits only, no units).")

def call(prompt, max_retries=3):
    body = json.dumps({"model": "reflection/Beam-1.0-501B-A23B", "reasoning_effort": "low", "max_tokens": 4000,
        "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception:
            if attempt == max_retries - 1: raise
            time.sleep(6 * (attempt + 1))

def extract_number(text):
    if not text: return None
    lines = [l for l in text.strip().splitlines() if l.strip()]
    for cand in [lines[-1], text]:
        m = re.findall(r'-?\d[\d,]*\.?\d*', cand)
        if m:
            try: return float(m[-1].replace(',', ''))
            except ValueError: pass
    return None

items = [json.loads(l) for l in open('data/gsm8k_hinglish.jsonl')][:30]
out_path = 'runs/mitigation_beam.jsonl'
done = {json.loads(l)['id'] for l in open(out_path)} if os.path.exists(out_path) else set()
out = open(out_path, 'a')
for it in items:
    if it['id'] in done: continue
    resp = call(it['hi'])
    msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
    pred = extract_number(msg.get('content', ''))
    rec = {"id": it['id'], "answer": it['answer'], "pred": pred,
           "correct": (pred is not None and abs(pred - it['answer']) < 1e-6),
           "completion_tokens": usage.get('completion_tokens')}
    out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush()
    print(f"{it['id']} ok={rec['correct']} comp={rec['completion_tokens']}", flush=True)
out.close()
base = {json.loads(l)['id']: json.loads(l) for l in open('runs/gsm8k_reflection_Beam-1_0-501B-A23B.jsonl')}
mit = [json.loads(l) for l in open(out_path)]
pairs = [(base[f"{m['id']}:hi:reflection/Beam-1.0-501B-A23B"], m) for m in mit if f"{m['id']}:hi:reflection/Beam-1.0-501B-A23B" in base]
b_acc = sum(b['correct'] for b, _ in pairs)/len(pairs); m_acc = sum(m['correct'] for _, m in pairs)/len(pairs)
b_tok = sum(b['completion_tokens'] for b, _ in pairs)/len(pairs); m_tok = sum(m['completion_tokens'] for _, m in pairs)/len(pairs)
print(f"n={len(pairs)} baseline: acc={b_acc:.2%} avg_tok={b_tok:.0f} | mitigated: acc={m_acc:.2%} avg_tok={m_tok:.0f} | token change={100*(m_tok-b_tok)/b_tok:+.0f}%")
