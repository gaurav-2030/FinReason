# Finishes the TextGrad optimization for Qwen3-1.7B, tests the optimized prompt on all three test
# sets, then refreshes the analysis, the review documents and the study guide, and runs every test.
cd "$(dirname "$0")/.."
export HF_HUB_OFFLINE=1 PYTHONUNBUFFERED=1
PY=.venv/bin/python
echo "=== TextGrad $(date)"
$PY scripts/optimize_textgrad.py --model ollama:qwen3:1.7b --optimizer-model ollama:qwen3:8b || { echo "!!! TEXTGRAD FAILED"; exit 1; }
T=textgrad:artifacts/textgrad_ollama-qwen3-1.7b.json
for D in finqa tatqa; do $PY scripts/run_experiment.py --dataset $D --n 100 --model ollama:qwen3:1.7b --strategy $T; done
$PY scripts/run_experiment.py --dataset indian --n 44 --model ollama:qwen3:1.7b --strategy $T
echo "=== analysis and documents $(date)"
$PY scripts/analyze.py > /dev/null && echo "analysis done"
$PY reviews/src/screenshots.py > /dev/null 2>&1
$PY reviews/src/build.py > /dev/null && echo "=== REVIEWS REBUILT"
$PY reviews/src/build.py --detailed > /dev/null && echo "=== DETAILED REBUILT"
echo "=== FINISH DONE $(date)"
