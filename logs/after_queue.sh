# Runs after logs/queue.sh finishes: the small-model optimization stage (needs Ollama to itself), then the analysis.
cd ~/Desktop/FinReason
until grep -q '=== ALL DONE' logs/queue.log || ! pgrep -f 'bash logs/queue.sh' >/dev/null; do sleep 60; done
echo "=== optimize_small $(date)"
bash scripts/run_all.sh optimize_small && echo "=== OPT DONE $(date)" || echo "!!! OPT FAILED $(date)"
bash scripts/run_all.sh analyze > /dev/null 2>&1
echo "=== AFTER-QUEUE DONE $(date)"
