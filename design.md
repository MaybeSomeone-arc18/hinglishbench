# HinglishBench v0.1 - design (Oct 22-23)

Goal: first code-mixed (romanized Hindi-English, "Hinglish") evaluation of Beam-1.0-501B-A23B, for the
Reflection x HF "Build with Beam" challenge (deadline Nov 2). Zero spend beyond $25 claimed HF credits.

## Why this is novel
- Beam model card: "developed predominantly for English". Code-mix gap is unknown and interesting to Reflection.
- Existing challenge language entry (Mada-Bench, Malagasy) is monolingual low-resource; code-MIX is a different phenomenon.
- No public EN/Hinglish parallel benchmark for frontier open models. GLUECoS (Microsoft, 2020) is code-mixed but
  pre-LLM (encoder tasks); no generative reasoning set exists.

## Core design: parallel pairs
Same problems in English and in romanized Hinglish => accuracy gap + token-cost gap attributable to language,
not difficulty. Answers verifiable (numeric exact match).

- Task A (core): ~100 math/word-problem pairs (EN, HI-Latin). Metric: exact-match accuracy per lang; gap.
- Task B (established anchor): code-mixed sentiment on an existing public dataset (3-class exact match).
- Task C (cost): completion/reasoning token counts + $ per item, EN vs Hinglish (token inflation, cf. Mada-Bench 3x on Malagasy).
- Task D (stretch): Hinglish -> EN translation chrF on a small established set.

## Models
- Beam-1.0-501B-A23B (HF Inference Providers / Baseten), reasoning_effort=low (community standard in this challenge).
- Comparison (full run, cheap on providers): 1-2 open models, e.g. Qwen3-32B, Gemma-3-27B-it (availability TBC).

## Budget guardrails
- Pilot: 50 prompts (25 EN + 25 Hinglish pairs), Beam only. Measure tokens + actual billed $ from HF billing.
- Hard stop: if projected full benchmark (Beam + 2 models x ~600 gens) > $10, cut scope.
- Full run target <= ~2,000 generations.

## Prompting
System: "You are answering a benchmark question. Reply with ONLY the final numeric answer (digits only)."
No few-shot (zero-shot, single sample per item, documented as a limit).

## Limits to state in writeup
Single run, no few-shot, reasoning_effort=low only, small set (~100), romanized only (no Devanagari),
author-built items (validated by construction), one provider.

## Deliverables (Oct 28-29)
- HF dataset repo: items EN+HI, per-item predictions, tokens, grades (CC BY-SA or MIT; no Beam ToS issue - outputs allowed)
- HF Space: leaderboard + "try your own Hinglish prompt"
- Writeup in dataset card, comment on rules thread (HE posts, after his approval)
