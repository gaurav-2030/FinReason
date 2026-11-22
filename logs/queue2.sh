# Finishes every pending experiment (started 2026-10-14), most important first:
# small-model reruns (cache hits) and optimization, then the 8B grid, optimizers and ablations.
cd "$(dirname "$0")/.."
export HF_HUB_OFFLINE=1
run() { echo "=== $* $(date)"; env "$@" || echo "!!! failed: $*"; }
S=ollama:qwen3:1.7b; L=ollama:qwen3:8b
run MODELS=$S bash scripts/run_all.sh main proposed indian
run bash scripts/run_all.sh optimize_small analyze
run MODELS=$L bash scripts/run_all.sh main proposed indian analyze
run bash scripts/run_all.sh optimize_large analyze
run MODELS=$L bash scripts/run_all.sh perturb analyze
run bash scripts/run_all.sh retrieval_large formats_large analyze
echo "=== ALL DONE $(date)"
