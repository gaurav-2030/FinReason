#!/usr/bin/env bash
# Start the web app with its own Ollama server (port 11435), so questions asked in the app never
# wait behind the experiments, which use the main server (port 11434).
#   bash scripts/start_app.sh        then open http://localhost:8501
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
# the app is already running (e.g. started earlier in another terminal): just point to it
if curl -s -o /dev/null localhost:8501; then
  echo "FinReason is already running: open http://localhost:8501"
  echo "(to restart it: pkill -f 'streamlit run app/streamlit_app.py' and run this script again)"
  exit 0
fi
# the embedding model for retrieval is cached after the first run; use it offline (no network needed)
if [ -d "$HOME/.cache/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2" ]; then
  export HF_HUB_OFFLINE=1
fi
if ! curl -s localhost:11435/api/tags > /dev/null; then
  OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NUM_PARALLEL=2 OLLAMA_MAX_LOADED_MODELS=2 \
    ollama serve > logs/ollama_app.log 2>&1 &
  until curl -s localhost:11435/api/tags > /dev/null; do sleep 1; done
fi
FINREASON_OLLAMA_URL=http://localhost:11435 exec .venv/bin/python -m streamlit run app/streamlit_app.py \
  --server.headless true --server.port 8501 --server.address localhost
