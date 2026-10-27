#!/bin/bash
cd /home/sandbox/hinglishbench
for m in "reflection/Beam-1.0-501B-A23B"; do
  safe=$(echo "$m" | tr '/.' '__')
  BEAM_EFFORT=medium python3 scripts/run_bench.py "$m" data/gsm8k_hinglish.jsonl "runs/v2m_gsm8k_${safe}.jsonl" >> "runs/v2m_gsm8k_${safe}.log" 2>&1
done
echo ALL_DONE >> runs/v2m_all.log
