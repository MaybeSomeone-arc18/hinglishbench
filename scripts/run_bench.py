#!/usr/bin/env python3
"""HinglishBench runner: parallel EN/Hinglish items x model, exact-match grade, token logging."""
import json, os, re, sys, time, urllib.request

TOKEN = open('/home/sandbox/.hf_hinglishbench_token').read().strip()
URL = "https://router.huggingface.co/v1/chat/completions"
SYSTEM = ("Solve the problem. You may think briefly, then end your reply with a final line containing ONLY the numeric answer (digits only, no units).")

def call(model, prompt, max_retries=3):
    body = {"model": model, "max_tokens": 4000,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]}
    if "Beam" in model: body["reasoning_effort"] = os.environ.get("BEAM_EFFORT", "low")
    if "Qwen3" in model: body["chat_template_kwargs"] = {"enable_thinking": False}
    data = json.dumps(body).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(URL, data=data, headers={
                "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception as e:
            if attempt == max_retries - 1:
                return {"error": str(e)}
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

def main():
    model, files, out_path = sys.argv[1], sys.argv[2:-1], sys.argv[-1]
    items = []
    for f in files:
        for l in open(f):
            it = json.loads(l); it.setdefault('tier', 'easy'); items.append(it)
    done = set()
    if os.path.exists(out_path):
        done = {json.loads(l)['key'] for l in open(out_path)}
    out = open(out_path, 'a')
    for item in items:
        for lang in ('en', 'hi'):
            key = f"{item['id']}:{lang}:{model}"
            if key in done: continue
            resp = call(model, item[lang])
            if 'error' in resp:
                rec = {"key": key, "id": item['id'], "lang": lang, "model": model, "tier": item['tier'],
                       "error": resp['error']}
            else:
                msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
                pred = extract_number(msg.get('content', ''))
                rec = {"key": key, "id": item['id'], "lang": lang, "model": model, "tier": item['tier'],
                       "answer": item['answer'], "raw": msg.get('content', ''),
                       "pred": pred, "correct": (pred is not None and abs(pred - item['answer']) < 1e-6),
                       "prompt_tokens": usage.get('prompt_tokens'), "completion_tokens": usage.get('completion_tokens'),
                       "reasoning_tokens": (usage.get('completion_tokens_details') or {}).get('reasoning_tokens')}
            out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush()
            print(f"{key} ok={rec.get('correct')} comp={rec.get('completion_tokens')}", flush=True)
    out.close()

    recs = [json.loads(l) for l in open(out_path) if '"error"' not in l]
    for lang in ('en', 'hi'):
        for tier in ('easy', 'medium', 'hard'):
            sub = [r for r in recs if r['lang'] == lang and r.get('tier') == tier]
            if not sub: continue
            acc = sum(r['correct'] for r in sub) / len(sub)
            avg_c = sum(r['completion_tokens'] for r in sub) / len(sub)
            print(f"[{lang}/{tier}] n={len(sub)} acc={acc:.2%} avg_completion={avg_c:.0f}")

if __name__ == '__main__':
    main()
