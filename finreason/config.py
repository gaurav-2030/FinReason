"""Project-wide paths and default settings used by every other module."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_INDIAN = ROOT / "data" / "indian"
RESULTS = ROOT / "results"
RUNS_DIR = RESULTS / "runs"
FIGURES_DIR = RESULTS / "figures"
ARTIFACTS = ROOT / "artifacts"
# The response cache is a SQLite database. It lives outside the project folder because cloud-synced
# folders (e.g. an iCloud Desktop) lock open database files; FINREASON_CACHE overrides the location.
CACHE_DB = Path(os.environ.get("FINREASON_CACHE", Path.home() / ".cache" / "finreason" / "llm_cache.sqlite"))

SEED = 42
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_MODEL = "ollama:qwen3:8b"
OLLAMA_URL = os.environ.get("FINREASON_OLLAMA_URL", "http://localhost:11434")   # the app uses its own server

# An answer counts as correct if it is within 0.5% of the gold value (see answers.score).
REL_TOLERANCE = 0.005

# Self-consistency: number of sampled reasoning paths and their sampling temperature.
SC_SAMPLES = 5
SC_TEMPERATURE = 0.7

# US$ per 1M tokens (input, output) for API models. Local Ollama models cost 0.
# Verify against the provider's pricing page before quoting these in the report.
PRICES = {
    "openai:gpt-4o-mini": (0.15, 0.60),
}
