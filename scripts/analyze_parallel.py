#!/usr/bin/env python3
"""Analyze the beamgen parallel run: per-model EN vs HI accuracy + token tax."""
import json, glob, statistics
recs = []
for f in glob.glob('runs/vp_*.jsonl'):
    for l in open(f):
        r = json.loads(l)
        if 'error' not in r: recs.append(r)
models = sorted({r['model'] for r in recs})
print(f"total records: {len(recs)}")
summary = {}
for m in models:
    sub = [r for r in recs if r['model'] == m]
    out = {}
    for lang in ('en', 'hi'):
        sl = [r for r in sub if r['lang'] == lang]
        acc = sum(r['correct'] for r in sl) / len(sl) if sl else 0
        out[lang] = (len(sl), acc, statistics.median(r['completion_tokens'] for r in sl if r.get('completion_tokens')))
    # paired token tax (median of per-pair ratios, same as GSM8K methodology)
    byid = {}
    for r in sub: byid.setdefault(r['id'], {})[r['lang']] = r
    ratios = [v['hi']['completion_tokens'] / v['en']['completion_tokens'] for v in byid.values()
              if 'en' in v and 'hi' in v and v['en'].get('completion_tokens') and v['hi'].get('completion_tokens')]
    tax = statistics.median(ratios) if ratios else None
    print(f"{m}: EN {out['en'][1]:.1%} (n={out['en'][0]}) | HI {out['hi'][1]:.1%} (n={out['hi'][0]}) | median comp tok EN {out['en'][2]:.0f} HI {out['hi'][2]:.0f} | token tax {tax:.2f}x (paired n={len(ratios)})")
    summary[m] = {'en_acc': out['en'][1], 'hi_acc': out['hi'][1], 'en_n': out['en'][0], 'hi_n': out['hi'][0],
                  'en_med_tok': out['en'][2], 'hi_med_tok': out['hi'][2], 'tax': tax, 'pairs': len(ratios)}
json.dump(summary, open('runs/beamgen_parallel_summary.json', 'w'), indent=1)
