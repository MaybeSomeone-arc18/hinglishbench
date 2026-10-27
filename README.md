# HinglishBench - runner code

Reproducible runner code behind **HinglishBench**, a parallel English/Hinglish reasoning evaluation for open LLMs (Beam-1.0-501B-A23B, Gemma-3-27B-it, Qwen3-32B).

- Dataset (items, predictions, full card, methodology, limits): https://huggingface.co/datasets/MaybeSomeone19/hinglishbench
- Explorer (leaderboard + per-item outputs, static): https://huggingface.co/spaces/MaybeSomeone19/hinglishbench

## What is here

- `scripts/translate_gsm8k.py` - GSM8K EN -> romanized Hinglish translation via Beam, with automated numeric-preservation check
- `scripts/run_bench.py` - resumable benchmark runner (fair CoT prompt, exact-match grading on the final line, token accounting); `BEAM_EFFORT` env var sets Beam's `reasoning_effort`
- `scripts/run_all_models.sh`, `scripts/run_all_v2.sh`, `scripts/run_beam_medium.sh` - the 3-model matrix runs (low effort) and the Beam medium-effort run
- `scripts/mitigation.py` - "think in English" mitigation experiment
- `scripts/gen_hinglish_dataset.py` - Beam-authored Hinglish reasoning data: generate -> automated checks -> dedup -> self-consistency verify
- `scripts/beamgen_translate_en.py` - reverse-direction (HI -> EN) parallel translation with numeric check
- `scripts/analyze.py`, `scripts/analyze_parallel.py`, `scripts/run_pilot.py`, `scripts/build_space.py` - analysis, pilot, and the static Space builder
- `design.md`, `OPTIMIZATION.md` - working notes from the build

## Data

All datasets and per-item predictions live in the Hugging Face dataset repo linked above (CC BY-SA 4.0). The scripts expect the jsonl files from that repo under `data/`.

## Setup

No dependencies - the runner uses only the Python 3 standard library.

The scripts read an HF Inference Providers token from `/home/sandbox/.hf_hinglishbench_token`
(edit the path at the top of each script to point at your own token file). Beam ran via Baseten; Gemma and Qwen via the default providers. Running the full matrix costs paid inference credits - the published results used about $0.95 total.

## Methodology in one paragraph

100 GSM8K test items (seed 42) were translated to romanized Hinglish by Beam; 18 failed the automated numeric-preservation check and were excluded, leaving 82 parallel pairs. Every model got the identical zero-shot prompt ("Solve the problem. You may think briefly, then end your reply with a final line containing ONLY the numeric answer."). Grading is numeric exact match on the final line (fallback: last number anywhere). Token tax is the per-item ratio of completion tokens (Hinglish/English), reported as the median over pairs. Two more sets replicate the tax: 100 author-built tiered pairs, and 309 reverse-direction pairs (Beam-authored Hinglish-first items translated to English). See the dataset card for full methodology and limits.

## Headline numbers (82 GSM8K pairs, zero-shot, single run)

| Model | English | Hinglish | Median token tax (HI/EN) |
|---|---|---|---|
| Beam-1.0-501B-A23B (effort=low) | 96.3% | 95.1% | 1.47x |
| Gemma-3-27B-it | 91.5% | 93.9% | 0.96x |
| Qwen3-32B | 90.2% | 82.9% | 1.00x |

These three models on this set; accuracy differences of one item (1.2 pts) are within noise at n=82. Negative results (prompting and effort do not remove Beam's tax) are in the dataset card.

## License

Code: MIT (see LICENSE). Data: CC BY-SA 4.0 (dataset repo). GSM8K itself is MIT-licensed (OpenAI).
