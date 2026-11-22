#!/usr/bin/env bash
# Every experiment in the project, in the order they were run.
#   bash scripts/run_all.sh all        # everything (about 30 hours on an M4 MacBook, 24 GB)
#   bash scripts/run_all.sh main       # one stage only; see the stage names below
# All runs resume where they stopped, and every model response is cached (~/.cache/finreason).
# Start Ollama first with parallel slots:  OLLAMA_NUM_PARALLEL=4 ollama serve
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
RUN="$PY scripts/run_experiment.py"
SMALL=ollama:qwen3:1.7b
LARGE=ollama:qwen3:8b
MANUAL=direct,cot_zs,cot_fs,decomp_fs,pot_fs,sc_cot
MODELS=${MODELS:-"$SMALL $LARGE"}   # e.g. MODELS=ollama:qwen3:1.7b bash scripts/run_all.sh main

main() {        # 6 hand-written strategies x 2 models x FinQA, TAT-QA (100 questions each)
  for M in $MODELS; do
    for D in finqa tatqa; do $RUN --dataset $D --n 100 --model $M --strategy $MANUAL; done
  done
}

indian() {      # generalization to the 44 Indian annual-report questions
  for M in $MODELS; do $RUN --dataset indian --n 44 --model $M --strategy $MANUAL; done
}

proposed() {    # our method (VPSC) and its ablation without verification (PoT self-consistency)
  for M in $MODELS; do
    for D in finqa tatqa; do $RUN --dataset $D --n 100 --model $M --strategy vpsc,pot_sc; done
    $RUN --dataset indian --n 44 --model $M --strategy vpsc,pot_sc
  done
}

perturb() {     # memorization check: same FinQA questions with changed numbers
  for M in $MODELS; do $RUN --dataset finqa --n 100 --model $M --strategy cot_fs,pot_fs,vpsc --perturbed; done
}

optimize_small() {   # DSPy and TextGrad for the small model (TextGrad feedback from the 8B model)
  $PY scripts/optimize_dspy.py --model $SMALL --optimizer bootstrap
  $PY scripts/optimize_dspy.py --model $SMALL --optimizer mipro
  $PY scripts/optimize_textgrad.py --model $SMALL --optimizer-model $LARGE
  S=dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json,dspy:artifacts/dspy_mipro_ollama-qwen3-1.7b.json,textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json
  $RUN --dataset finqa --n 100 --model $SMALL --strategy $S
  $RUN --dataset tatqa --n 100 --model $SMALL --strategy $S
  $RUN --dataset indian --n 44 --model $SMALL --strategy $S
}

optimize_large() {   # DSPy BootstrapFewShot, MIPROv2 and TextGrad for the 8B model
  $PY scripts/optimize_dspy.py --model $LARGE --optimizer bootstrap
  $PY scripts/optimize_dspy.py --model $LARGE --optimizer mipro
  $PY scripts/optimize_textgrad.py --model $LARGE --optimizer-model $LARGE
  S=dspy:artifacts/dspy_bootstrap_ollama-qwen3-8b.json,dspy:artifacts/dspy_mipro_ollama-qwen3-8b.json,textgrad:artifacts/textgrad_ollama-qwen3-8b.json
  $RUN --dataset finqa --n 100 --model $LARGE --strategy $S
  $RUN --dataset tatqa --n 100 --model $LARGE --strategy $S
  $RUN --dataset indian --n 44 --model $LARGE --strategy $S
}

formats_small() {   # table serialization: json, html and row-wise text (markdown is in main)
  for F in json html text; do
    for D in finqa tatqa; do $RUN --dataset $D --n 100 --model $SMALL --strategy cot_fs --fmt $F; done
  done
}

formats_large() {
  for F in json html text; do $RUN --dataset finqa --n 100 --model $LARGE --strategy cot_fs --fmt $F; done
}

retrieval_small() { # evidence retrieval (top-5 rows/sentences) instead of the full page
  $PY scripts/eval_retrieval.py
  for D in finqa tatqa; do $RUN --dataset $D --n 100 --model $SMALL --strategy pot_fs --context retrieved --k 5; done
}

retrieval_large() {
  for D in finqa tatqa; do $RUN --dataset $D --n 100 --model $LARGE --strategy pot_fs --context retrieved --k 5; done
}

thinking() {    # the model's built-in thinking mode (much more output tokens)
  $RUN --dataset finqa --n 100 --model $SMALL --strategy cot_zs --think
}

analyze() {
  $PY scripts/dataset_stats.py
  $PY scripts/analyze.py
}

# ordered so that every small-model stage finishes before the expensive 8B ones
all() {
  MODELS=$SMALL; main; proposed; indian; perturb; optimize_small; formats_small; retrieval_small; thinking
  MODELS=$LARGE; main; proposed; indian; optimize_large; perturb; retrieval_large; formats_large
  analyze
}

for stage in "$@"; do "$stage"; done
