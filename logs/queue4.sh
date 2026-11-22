# Experiment queue for the 15-Oct presentation (started 2026-10-14 ~23:00 IST).
# Priority order: 1.7B prompt optimizers and their tests, then the Qwen3-8B main grid on TAT-QA
# (so the 1.7B-vs-8B comparison is complete on both FinQA and TAT-QA), then VPSC and the Indian set
# on 8B. New steps stop at DEADLINE and a step still running then is stopped (runs resume later and
# unfinished runs are never reported). Finally: analysis, app screenshots, review documents.
cd "$(dirname "$0")/.."
export HF_HUB_OFFLINE=1
DEADLINE=$(date -j -f "%Y-%m-%d %H:%M" "2026-10-15 07:00" +%s)
PY=.venv/bin/python
RUN="$PY scripts/run_experiment.py"
S=ollama:qwen3:1.7b; L=ollama:qwen3:8b
OPT_S=dspy:artifacts/dspy_bootstrap_ollama-qwen3-1.7b.json,dspy:artifacts/dspy_mipro_ollama-qwen3-1.7b.json,textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json
SINGLE=direct,cot_zs,cot_fs,decomp_fs,pot_fs

( while [ "$(date +%s)" -lt "$DEADLINE" ]; do sleep 30; done
  pkill -f scripts/run_experiment.py; pkill -f scripts/optimize_ ) &
WATCH=$!

step() {
  if [ "$(date +%s)" -ge "$DEADLINE" ]; then echo "--- skipped (deadline): $*"; return; fi
  echo "=== $* $(date)"; "$@" || echo "!!! failed or stopped: $*"
}

echo "=== waiting for the running MIPROv2 optimization $(date)"
while pgrep -f "scripts/optimize_dspy.py" > /dev/null; do sleep 20; done
ls artifacts/dspy_mipro_ollama-qwen3-1.7b.json > /dev/null 2>&1 && echo "MIPROv2 artifact saved" \
  || step $PY scripts/optimize_dspy.py --model $S --optimizer mipro
step $PY scripts/optimize_textgrad.py --model $S --optimizer-model $L
for D in finqa tatqa; do step $RUN --dataset $D --n 100 --model $S --strategy $OPT_S; done
step $RUN --dataset indian --n 44 --model $S --strategy $OPT_S
step $RUN --dataset tatqa --n 100 --model $L --strategy $SINGLE,sc_cot
step $RUN --dataset finqa --n 100 --model $L --strategy vpsc,pot_sc
step $RUN --dataset indian --n 44 --model $L --strategy $SINGLE,sc_cot
step $RUN --dataset indian --n 44 --model $L --strategy vpsc,pot_sc
step $RUN --dataset tatqa --n 100 --model $L --strategy vpsc,pot_sc
step $RUN --dataset finqa --n 100 --model $L --strategy cot_fs,pot_fs,vpsc --perturbed
kill $WATCH 2>/dev/null

echo "=== analysis and review documents $(date)"
$PY scripts/dataset_stats.py > /dev/null
$PY scripts/analyze.py > /dev/null && echo "analysis done"
$PY reviews/src/screenshots.py || echo "!!! screenshots failed (is the app running?)"
$PY reviews/src/build.py && echo "=== REVIEWS REBUILT $(date)" || echo "!!! REVIEW BUILD FAILED $(date)"
$PY reviews/src/build.py --detailed > /dev/null 2>&1 && echo "=== DETAILED REVIEWS REBUILT $(date)" || echo "!!! DETAILED BUILD FAILED"
echo "=== QUEUE DONE $(date)"
