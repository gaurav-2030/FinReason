"""Shared state for every page of the app: cached models, datasets and results, labels and small
helpers. All numbers shown in the app come from results/ (written by scripts/analyze.py) or from
the saved runs, re-scored with the project's own scorer."""
import json
import math
import subprocess
import sys
import urllib.request
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from finreason.config import ARTIFACTS, DATA_INDIAN, FIGURES_DIR, OLLAMA_URL, RESULTS  # noqa: E402
from finreason.data import load_dataset  # noqa: E402
from finreason.figures import DATASET_LABEL, model_label, strategy_label, strategy_rank  # noqa: E402
from finreason.llm import LLM  # noqa: E402
from finreason.retrieval import HybridRetriever  # noqa: E402

SMALL, LARGE = "ollama:qwen3:1.7b", "ollama:qwen3:8b"
MODELS = [SMALL, LARGE]
DATASETS = ["finqa", "tatqa", "indian"]
FULL_N = {"finqa": 100, "tatqa": 100, "indian": 44}
MANUAL = ["direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"]
STYLE_OF = {"direct": "direct", "cot_zs": "cot", "cot_fs": "cot", "sc_cot": "cot",
            "decomp_fs": "decomp", "pot_fs": "pot", "pot_sc": "pot", "vpsc": "pot"}
FEWSHOT = {"direct": False, "cot_zs": False}   # every other hand-written strategy shows 3 worked examples
DESCRIPTION = {
    "direct": "Answer line only. The baseline with no reasoning.",
    "cot_zs": "\"Think step by step\": find the numbers, write the calculation, compute it.",
    "cot_fs": "Step-by-step reasoning after three worked FinQA train examples.",
    "decomp_fs": "Knowledge → Extract → Decompose → Answer, in labelled parts (EEDP).",
    "pot_fs": "The model writes Python; the sandbox runs it; one repair retry on an error.",
    "sc_cot": "Five CoT samples (1 greedy + 4 at T = 0.7), majority vote.",
    "pot_sc": "Five programs, majority vote, no grounding check (VPSC ablation).",
    "vpsc": "Ours: five programs → sandbox → reject numbers not in the report → vote.",
    "dspy-bootstrap": "DSPy picks few-shot demos the model solved correctly on FinQA train.",
    "dspy-mipro": "DSPy MIPROv2 searches instruction + demo sets with Bayesian optimisation.",
    "textgrad": "Zero-shot CoT with a system prompt rewritten by TextGrad's textual gradients.",
}


def model_name(spec):
    """Display name for a model spec; also accepts an already formatted name."""
    return model_label(spec) if ":" in str(spec) else str(spec)


def dataset_label(name):
    return DATASET_LABEL.get(name, name)


def describe(strategy):
    if strategy.startswith("dspy:"):
        return DESCRIPTION["dspy-mipro" if "mipro" in strategy else "dspy-bootstrap"]
    if strategy.startswith("textgrad:"):
        return DESCRIPTION["textgrad"]
    return DESCRIPTION.get(strategy, "")


def short_label(strategy):
    """Strategy label; optimized strategies also name the model they were optimized for."""
    label = strategy_label(strategy)
    if ":" in strategy and "qwen3" in strategy:
        label += " · " + ("8B" if "8b" in strategy else "1.7B")
    return label


# ---------------------------------------------------------------- formatting
def fmt_number(value, digits=2):
    """Readable answer: 16.402847 -> '16.40', 1234567 -> '1,234,567', None -> 'no answer'."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "no answer"
    if isinstance(value, str):
        return value
    if value != 0 and abs(value) < 0.01:
        return f"{value:.4g}"
    if float(value).is_integer() and abs(value) >= 1:
        return f"{value:,.0f}"
    return f"{value:,.{digits}f}"


def exact_number(value):
    if value is None or isinstance(value, str):
        return ""
    return f"exact value {value:.10g}"


def pct(x, digits=0):
    return "–" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{100 * x:.{digits}f}%"


# ---------------------------------------------------------------- models and data
@st.cache_resource(show_spinner=False)
def get_llm(spec):
    return LLM(spec)


@st.cache_resource(show_spinner="Loading the embedding model…")
def get_retriever():
    return HybridRetriever()


@st.cache_data(show_spinner=False)
def get_examples(dataset):
    """Questions offered in the app: the whole Indian set and the evaluated FinQA / TAT-QA samples."""
    return load_dataset(dataset, "test", n=FULL_N[dataset] if dataset != "indian" else None, seed=42)


def strategy_options():
    names = list(MANUAL)
    names += [f"dspy:{p.relative_to(ROOT)}" for p in sorted(ARTIFACTS.glob("dspy_*.json"))
              if not p.name.endswith(".meta.json")]
    names += [f"textgrad:{p.relative_to(ROOT)}" for p in sorted(ARTIFACTS.glob("textgrad_*.json"))]
    return names


def dspy_model(strategy):
    """The model a compiled DSPy program was optimized for (from its .meta.json), or None."""
    meta = ROOT / strategy.split(":", 1)[1].replace(".json", ".meta.json")
    try:
        return json.load(open(meta))["lm_spec"]
    except (OSError, KeyError, ValueError):
        return None


def model_options():
    return MODELS


@st.cache_data(ttl=10, show_spinner=False)
def ollama_online():
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1):
            return True
    except OSError:
        return False


@st.cache_data(ttl=10, show_spinner=False)
def experiments_running():
    """True while the benchmark runner is using the same machine (answers are then slower)."""
    probe = subprocess.run(["pgrep", "-f", "scripts/(run_experiment|optimize_)"], capture_output=True)
    return probe.returncode == 0


def status_pills():
    from theme import pill
    online = ollama_online()
    busy = experiments_running()
    pills = [pill("Ollama online" if online else "Ollama offline", "good" if online else "bad")]
    if busy:
        pills.append(pill("experiments running", "warn"))
    return pills


# ---------------------------------------------------------------- results
def _read_csv(name):
    path = RESULTS / name
    if not path.exists() or path.stat().st_size == 0:
        return None
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def results_csv(name):
    return _read_csv(name)


def summary():
    return results_csv("summary.csv")


def main_summary(include_partial=False):
    """The main comparison: markdown tables, full page, thinking off, original questions.
    Runs that are still in progress (fewer questions than the full sample) are left out unless
    include_partial is set, so a half-finished run is never reported as a result."""
    s = summary()
    if s is None:
        return None
    s = s[(s["fmt"] == "markdown") & (s["context"] == "full") & (~s["think"]) & (~s["perturbed"])].copy()
    if not include_partial:
        s = s[s["n"] >= s["dataset"].map(FULL_N).fillna(0)]
    return s


def partial_runs():
    """Main-setting runs still in progress: (dataset, model, strategy, done, total)."""
    s = main_summary(include_partial=True)
    if s is None:
        return []
    s = s[s["n"] < s["dataset"].map(FULL_N).fillna(0)]
    return [(r.dataset, r.model, r.strategy, int(r.n), FULL_N[r.dataset]) for r in s.itertuples()]


def cell(s, dataset, model, strategy):
    """One summary row (a Series) or None."""
    if s is None:
        return None
    hit = s[(s["dataset"] == dataset) & (s["model"] == model) & (s["strategy"] == strategy)]
    return None if hit.empty else hit.iloc[0]


def complete(row, dataset):
    return row is not None and row["n"] >= FULL_N[dataset]


@st.cache_data(ttl=120, show_spinner="Re-scoring every saved answer…")
def records():
    sys.path.insert(0, str(ROOT / "scripts"))
    import analyze   # scripts/analyze.py: loads every run and re-scores it with the current rules
    return analyze.load_runs()


def main_records():
    df = records()
    return df[(df["fmt"] == "markdown") & (df["context"] == "full") & (~df["think"]) & (~df["perturbed"])]


def refresh_results():
    sys.path.insert(0, str(ROOT / "scripts"))
    import analyze
    analyze.main()
    st.cache_data.clear()


@st.cache_data(ttl=120, show_spinner=False)
def artifacts():
    """Saved optimization artifacts: {name: metadata} for DSPy (meta files) and TextGrad."""
    out = {}
    for p in sorted(ARTIFACTS.glob("dspy_*.meta.json")):
        out[p.name.replace(".meta.json", "")] = json.load(open(p))
    for p in sorted(ARTIFACTS.glob("textgrad_*.json")):
        out[p.stem] = json.load(open(p))
    return out


def figures():
    return sorted(FIGURES_DIR.glob("*.png"))


@st.cache_data(show_spinner=False)
def indian_rows():
    return [json.loads(line) for line in open(DATA_INDIAN / "indian_set.jsonl", encoding="utf-8") if line.strip()]


@st.cache_data(show_spinner="Rendering the report page…", max_entries=16)
def pdf_page_png(pdf_name, page_number, scale=1.6):
    """PNG bytes of one page of an Indian annual-report PDF (None if the PDF is not present)."""
    path = DATA_INDIAN / "reports" / pdf_name
    if not path.exists():
        return None
    import io
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(path))
    try:
        image = pdf[page_number - 1].render(scale=scale).to_pil()
    finally:
        pdf.close()
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
