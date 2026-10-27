#!/usr/bin/env python3
"""HinglishBench analysis: accuracy, token tax, paired diffs, charts."""
import json, glob, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

RUNS = '/home/sandbox/hinglishbench/runs'
OUT = '/home/sandbox/hinglishbench/analysis'
os.makedirs(OUT, exist_ok=True)

def load(pattern):
    recs = []
    for f in glob.glob(f'{RUNS}/{pattern}'):
        for l in open(f):
            r = json.loads(l)
            if 'error' not in r: recs.append(r)
    return recs

MODELS = {"reflection/Beam-1.0-501B-A23B": "Beam-1.0-501B",
          "google/gemma-3-27b-it": "Gemma-3-27B",
          "Qwen/Qwen3-32B": "Qwen3-32B"}

def summarize(recs, label):
    print(f"\n===== {label} =====")
    stats = {}
    for m, mname in MODELS.items():
        for lang in ('en', 'hi'):
            sub = [r for r in recs if r['model'] == m and r['lang'] == lang]
            if not sub: continue
            acc = sum(r['correct'] for r in sub) / len(sub)
            comp = [r['completion_tokens'] for r in sub]
            stats[(mname, lang)] = dict(n=len(sub), acc=acc, avg_comp=sum(comp)/len(comp))
            print(f"{mname:16s} {lang}  n={len(sub):3d}  acc={acc:6.2%}  avg_completion={sum(comp)/len(comp):6.1f}")
    # paired diff
    for m, mname in MODELS.items():
        en = {r['id']: r for r in recs if r['model'] == m and r['lang'] == 'en'}
        hi = {r['id']: r for r in recs if r['model'] == m and r['lang'] == 'hi'}
        both = set(en) & set(hi)
        if not both: continue
        en_only = [i for i in both if en[i]['correct'] and not hi[i]['correct']]
        hi_only = [i for i in both if hi[i]['correct'] and not en[i]['correct']]
        # token tax on paired items
        tax = [hi[i]['completion_tokens'] / max(en[i]['completion_tokens'], 1) for i in both]
        print(f"{mname:16s} paired n={len(both)}  EN-correct-only={len(en_only)} {en_only}  HI-correct-only={len(hi_only)} {hi_only}  median_token_tax={sorted(tax)[len(tax)//2]:.2f}x")
    return stats

def charts(stats_gsm):
    models = list(MODELS.values())
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    x = range(len(models)); w = 0.35
    axes[0].bar([i - w/2 for i in x], [stats_gsm.get((m, 'en'), {}).get('acc', 0)*100 for m in models], w, label='English')
    axes[0].bar([i + w/2 for i in x], [stats_gsm.get((m, 'hi'), {}).get('acc', 0)*100 for m in models], w, label='Hinglish')
    axes[0].set_title('GSM8K accuracy: English vs Hinglish'); axes[0].set_ylabel('Accuracy %'); axes[0].set_ylim(0, 105)
    axes[0].set_xticks(list(x)); axes[0].set_xticklabels(models, rotation=12); axes[0].legend()
    axes[1].bar([i - w/2 for i in x], [stats_gsm.get((m, 'en'), {}).get('avg_comp', 0) for m in models], w, label='English')
    axes[1].bar([i + w/2 for i in x], [stats_gsm.get((m, 'hi'), {}).get('avg_comp', 0) for m in models], w, label='Hinglish')
    axes[1].set_title('Completion tokens per answer (the cost of Hinglish)'); axes[1].set_ylabel('avg tokens')
    axes[1].set_xticks(list(x)); axes[1].set_xticklabels(models, rotation=12); axes[1].legend()
    plt.tight_layout(); plt.savefig(f'{OUT}/gsm8k_charts.png', dpi=150)
    print(f"\nchart -> {OUT}/gsm8k_charts.png")

if __name__ == '__main__':
    gsm = load('gsm8k_*-*.jsonl') + load('gsm8k_Qwen*.jsonl')
    stats = summarize(gsm, 'GSM8K-Hinglish (82 pairs)')
    if stats: charts(stats)
    beam_tiered = load('pilot_v0.jsonl')
    for r in beam_tiered: r['model'] = 'reflection/Beam-1.0-501B-A23B'
    v02 = load('beam_v02.jsonl')
    allt = beam_tiered + v02
    if allt: summarize(allt, 'Author-built tiered set, Beam deep-dive (100 pairs)')
