cd ~/Desktop/FinReason
run() { echo "=== $* $(date)"; env "$@" || echo "!!! failed: $*"; }
S=ollama:qwen3:1.7b; L=ollama:qwen3:8b
for st in main proposed indian perturb; do run MODELS=$S bash scripts/run_all.sh $st; done
for st in optimize_small formats_small retrieval_small thinking; do run bash scripts/run_all.sh $st; done
for st in main proposed indian perturb; do run MODELS=$L bash scripts/run_all.sh $st; done
for st in optimize_large retrieval_large formats_large mipro_large analyze; do run bash scripts/run_all.sh $st; done
echo "=== ALL DONE $(date)"
