#!/usr/bin/env bash
# TRACE final evaluation (22 Nov 2026). TRACE (finreason/trace.py, finreason/provenance.py, weights in
# trace.py) was frozen after development on FinQA/TAT-QA dev and the n=100 test samples. The held-out
# samples below exclude every question of the n=100 development samples (data.load_dataset "heldout").
# Ordered by importance: on this machine a call takes ~5.5 s, so the whole queue takes ~9-10 hours.
set -e
cd "$(dirname "$0")/.."
export HF_HUB_OFFLINE=1 FINREASON_OLLAMA_URL=http://localhost:11434
RUN=".venv/bin/python scripts/run_experiment.py --workers 4"
SHARED="trace,cot_fs,pot_fs,vpsc2"      # the baselines here reuse TRACE's calls (shared prompts)
Q17="--model ollama:qwen3:1.7b"
# 1. held-out samples
$RUN $Q17 --dataset finqa --split heldout --n 200 --strategy $SHARED
$RUN $Q17 --dataset tatqa --split heldout --n 200 --strategy $SHARED
# 2. Indian annual reports and the numerically perturbed FinQA sample
$RUN $Q17 --dataset indian --n 44 --strategy trace
$RUN $Q17 --dataset finqa --n 100 --strategy trace --perturbed
# 3. program self-consistency and VPSC on the held-out samples (4 extra samples per question)
$RUN $Q17 --dataset finqa --split heldout --n 200 --strategy pot_sc,vpsc
$RUN $Q17 --dataset tatqa --split heldout --n 200 --strategy pot_sc,vpsc
# 4. a second model family (Llama 3.2 3B, held-out) and a larger model (Qwen3-8B; most calls cached)
$RUN --model ollama:llama3.2:latest --dataset finqa --split heldout --n 100 --strategy $SHARED
$RUN --model ollama:qwen3:8b --dataset finqa --n 100 --strategy $SHARED
echo ALL DONE
