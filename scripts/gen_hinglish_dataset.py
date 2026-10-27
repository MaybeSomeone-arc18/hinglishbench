#!/usr/bin/env python3
"""Beam-authored Hinglish reasoning dataset: generate -> auto-check -> dedup -> self-consistency verify.
Resumable: phase A raw gen, phase B checks, phase C solve-verify."""
import json, os, re, sys, time, random, urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

TOKEN = open('/home/sandbox/.hf_hinglishbench_token').read().strip()
URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "reflection/Beam-1.0-501B-A23B"
RAW = 'runs/beamgen_raw.jsonl'
SOLVED = 'runs/beamgen_solved.jsonl'
COSTLOG = 'runs/beamgen_tokens.jsonl'
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 340
PER_CALL = 8

TOPICS = [
    "money and discounts in Indian shops (rupees, dukaan, discount, GST)",
    "time, speed and distance (train, bus, cycle, km per hour)",
    "ages of family members",
    "ratios and sharing between friends",
    "percentages (marks in exam, salary hike, interest)",
    "work rates (aadmi, din, kaam)",
    "averages (cricket score, class marks)",
    "simple geometry (rectangle area, perimeter, fence)",
    "profit and loss (cost price, selling price, fayda, nuksan)",
    "unit conversion and measurement (kg, litre, metre)",
    "counting and sequences (chairs, pages, floors of building)",
    "fractions of quantities (pizza, cake, rope, land)",
]
DIFFS = ["easy", "easy", "medium", "medium", "hard"]

GEN_SYS = ("You write math word problems in romanized Hinglish - the Hindi-English code-mixed style Indian "
           "students actually speak and text, written in English letters only (NO Devanagari).")

def gen_prompt(topic, diff, n):
    return (f"Write {n} NEW and distinct math word problems in romanized Hinglish on the topic: {topic}. "
            f"Difficulty: {diff}.\n"
            "Style example: \"Ek dukaan mein 250 rupaye ki shirt par 20% discount tha. Discount ke baad shirt ki final price kitni hui?\"\n"
            "Requirements:\n"
            "- Natural Hindi grammar with English loanwords mixed in, Latin script only.\n"
            "- Vary the numbers and scenarios; do not reuse the example's numbers.\n"
            "- Each problem has exactly one numeric answer (integer, or decimal up to 2 places).\n"
            "- The answer must be determinable from the problem text alone.\n"
            "Output ONLY a strict JSON array, no commentary: [{\"q\": \"...\", \"answer\": 123}, ...]")

SOLVE_SYS = ("Solve the problem. You may think briefly, then end your reply with a final line: ANSWER: <number only>.")

def call(messages, max_tokens=4000, max_retries=3):
    body = json.dumps({"model": MODEL, "reasoning_effort": "low", "max_tokens": max_tokens,
                       "messages": messages}).encode()
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(URL, data=body, headers={
                "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r)
        except Exception as e:
            if attempt == max_retries - 1:
                return {"error": str(e)}
            time.sleep(6 * (attempt + 1))

def parse_json_array(text):
    if not text: return None
    m = re.search(r'\[.*\]', text, re.S)
    if not m: return None
    try: return json.loads(m.group(0))
    except json.JSONDecodeError: return None

def log_tokens(tag, usage):
    with open(COSTLOG, 'a') as f:
        f.write(json.dumps({"tag": tag, "prompt": usage.get('prompt_tokens', 0),
                            "completion": usage.get('completion_tokens', 0)}) + '\n')

# ---------- Phase A: generation ----------
done_batches = set()
if os.path.exists(RAW):
    for l in open(RAW):
        done_batches.add(json.loads(l).get('batch'))
random.seed(7)
n_calls = -(-TARGET // PER_CALL)
with open(RAW, 'a') as out:
    for b in range(n_calls):
        if f"b{b}" in done_batches: continue
        topic = TOPICS[b % len(TOPICS)]
        diff = DIFFS[b % len(DIFFS)]
        resp = call([{"role": "system", "content": GEN_SYS},
                     {"role": "user", "content": gen_prompt(topic, diff, PER_CALL)}])
        if 'error' in resp:
            print(f"batch {b} ERROR {resp['error']}", flush=True); continue
        msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
        log_tokens(f"gen_b{b}", usage)
        content = msg.get('content') or ''
        arr = parse_json_array(content)
        kept = 0
        if arr:
            for it in arr:
                q = str(it.get('q', '')).strip()
                a = it.get('answer')
                try: a = float(str(a).replace(',', ''))
                except (TypeError, ValueError): continue
                if len(q) < 25: continue
                out.write(json.dumps({"batch": f"b{b}", "topic": topic, "difficulty": diff,
                                      "q": q, "answer": a}, ensure_ascii=False) + '\n')
                kept += 1
        out.flush()
        print(f"batch {b} {diff}/{topic[:30]}: kept {kept}, comp={usage.get('completion_tokens')}", flush=True)

# ---------- Phase B: auto-checks + dedup ----------
raw = [json.loads(l) for l in open(RAW)]
HINDI_MARKERS = re.compile(r'\b(ka|ki|ke|hai|hain|mein|kitna|kitni|kitne|tha|thi|the|aur|karo|kiya|raha|hoga|hogi|baad|tak|se|par|ne|ko|yeh|woh|uska|uski|iska|agar|total|kul|bache|bachi|diye|liya|lagta|lagti)\b', re.I)
def ok_item(r):
    q = r['q']
    if re.search(r'[\u0900-\u097F]', q): return False, 'devanagari'
    if len(HINDI_MARKERS.findall(q)) < 2: return False, 'not_hinglish'
    if not (10 <= len(q) <= 600): return False, 'length'
    if abs(r['answer']) > 1e9: return False, 'answer_range'
    return True, ''

def norm(q): return re.sub(r'\d+', '#', re.sub(r'[^a-z0-9 ]', '', q.lower()))
def grams(q, n=5):
    w = norm(q).split()
    return set(tuple(w[i:i+n]) for i in range(len(w)-n+1)) or {tuple(w)}

checked, rejected = [], []
seen_grams = []
for r in raw:
    ok, why = ok_item(r)
    if not ok:
        rejected.append({"q": r['q'], "why": why}); continue
    g = grams(r['q'])
    dup = any(len(g & gs) / max(1, len(g | gs)) > 0.35 for gs in seen_grams)
    if dup:
        rejected.append({"q": r['q'], "why": 'near_dup'}); continue
    seen_grams.append(g); checked.append(r)
print(f"phase B: {len(raw)} raw -> {len(checked)} passed checks+dedup, {len(rejected)} rejected", flush=True)

# ---------- Phase C: self-consistency solve ----------
solved = {}
if os.path.exists(SOLVED):
    for l in open(SOLVED):
        r = json.loads(l); solved[r['q']] = r
todo = [r for r in checked if r['q'] not in solved]
print(f"phase C: {len(todo)} to solve", flush=True)

def extract_answer(text):
    m = re.search(r'ANSWER:\s*(-?\d[\d,]*\.?\d*)', text or '')
    if m: 
        try: return float(m.group(1).replace(',', ''))
        except ValueError: return None
    nums = re.findall(r'-?\d[\d,]*\.?\d*', text or '')
    if nums:
        try: return float(nums[-1].replace(',', ''))
        except ValueError: pass
    return None

def solve_one(r):
    resp = call([{"role": "system", "content": SOLVE_SYS},
                 {"role": "user", "content": r['q']}], max_tokens=3000)
    if 'error' in resp: return {**r, "solve_error": resp['error']}
    msg = resp['choices'][0]['message']; usage = resp.get('usage', {})
    log_tokens('solve', usage)
    sa = extract_answer(msg.get('content') or '')
    return {**r, "solver_answer": sa, "solver_completion_tokens": usage.get('completion_tokens')}

out = open(SOLVED, 'a')
lock_done = 0
with ThreadPoolExecutor(max_workers=8) as ex:
    futs = {ex.submit(solve_one, r): r for r in todo}
    for f in as_completed(futs):
        rec = f.result()
        out.write(json.dumps(rec, ensure_ascii=False) + '\n'); out.flush()
        lock_done += 1
        if lock_done % 25 == 0: print(f"solved {lock_done}/{len(todo)}", flush=True)
out.close()

all_solved = [json.loads(l) for l in open(SOLVED)]
match, mismatch, err = [], [], []
for r in all_solved:
    if r.get('solve_error'): err.append(r)
    elif r.get('solver_answer') is None: err.append(r)
    elif abs(r['solver_answer'] - r['answer']) < 0.01: match.append(r)
    else: mismatch.append(r)
print(f"VERIFY: {len(match)} match, {len(mismatch)} mismatch, {len(err)} error/unparseable", flush=True)
with open('data/hinglish_reasoning_beam_candidates.jsonl', 'w') as f:
    for i, r in enumerate(match):
        f.write(json.dumps({"id": f"beamgen-{i+1:04d}", "q": r['q'], "answer": r['answer'],
                            "difficulty": r['difficulty'], "topic": r['topic'],
                            "solver_completion_tokens": r.get('solver_completion_tokens')}, ensure_ascii=False) + '\n')
with open('data/beamgen_rejected.jsonl', 'w') as f:
    for r in mismatch + err + rejected:
        r['reject_stage'] = r.get('why') or ('solve_mismatch' if r in mismatch else 'solve_error')
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
tot_p = sum(json.loads(l)['prompt'] for l in open(COSTLOG))
tot_c = sum(json.loads(l)['completion'] for l in open(COSTLOG))
print(f"TOKENS total: prompt={tot_p} completion={tot_c}", flush=True)
