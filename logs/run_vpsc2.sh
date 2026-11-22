#!/usr/bin/env bash
# VPSC v2 runs (13 Nov 2026): test sets, then a held-out dev check of v1 vs v2.
set -e
cd "$(dirname "$0")/.."
export HF_HUB_OFFLINE=1 FINREASON_OLLAMA_URL=http://localhost:11434
RUN=".venv/bin/python scripts/run_experiment.py --model ollama:qwen3:1.7b --workers 4"
$RUN --dataset tatqa --n 100 --strategy vpsc2
$RUN --dataset finqa --n 100 --strategy vpsc2
$RUN --dataset indian --n 44 --strategy vpsc2
$RUN --dataset finqa --n 100 --strategy vpsc2 --perturbed
$RUN --dataset tatqa --split dev --n 50 --strategy vpsc,vpsc2
$RUN --dataset finqa --split dev --n 50 --strategy vpsc,vpsc2
echo ALL DONE
