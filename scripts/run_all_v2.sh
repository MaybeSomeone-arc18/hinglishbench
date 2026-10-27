#!/bin/bash
cd /home/sandbox/hinglishbench
for m in "reflection/Beam-1.0-501B-A23B" "google/gemma-3-27b-it" "Qwen/Qwen3-32B"; do
  safe=$(echo "$m" | tr '/.' '__')
  python3 scripts/run_bench.py "$m" data/gsm8k_hinglish.jsonl "runs/v2_gsm8k_${safe}.jsonl" >> "runs/v2_gsm8k_${safe}.log" 2>&1
done
echo ALL_DONE >> runs/v2_all.log
