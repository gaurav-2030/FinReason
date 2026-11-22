"""Load every experiment result through the project's own analysis code (scripts/analyze.py), so the
review documents always show exactly the numbers the analysis pipeline computes."""
import json
import sys
from functools import lru_cache

import pandas as pd

from common import ROOT

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import analyze  # noqa: E402  (scripts/analyze.py)
from finreason.figures import model_label, strategy_label, strategy_rank  # noqa: E402

MAIN_ORDER = ["direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"]
DATASETS = ["finqa", "tatqa", "indian"]
DLABEL = {"finqa": "FinQA", "tatqa": "TAT-QA", "indian": "Indian reports"}
SMALL, LARGE = "ollama:qwen3:1.7b", "ollama:qwen3:8b"
FULL_N = {"finqa": 100, "tatqa": 100, "indian": 44}
PERTURBED_N = 88   # FinQA questions of the 100-question sample that can be perturbed safely


@lru_cache(None)
def runs():
    return analyze.load_runs()


@lru_cache(None)
def summary():
    return analyze.summarize(runs())


@lru_cache(None)
def main_summary():
    return analyze.main_summary(analyze.complete_runs(summary()))   # finished runs only


@lru_cache(None)
def complete_runs():
    return analyze.complete_records(runs())


@lru_cache(None)
def significance():
    return analyze.significance(complete_runs())


@lru_cache(None)
def perturbation():
    return analyze.perturbation(runs())


@lru_cache(None)
def optimization_costs():
    return analyze.optimization_costs()


def main_runs():
    return analyze.main_setting(complete_runs())


MANUAL = ["direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot"]


def model_ready(m):
    """A model's results are reported once its main grid (6 strategies) is complete on FinQA; any other
    run is shown only when it is complete (cell() hides unfinished runs), so partial runs never appear
    as findings."""
    for d in ["finqa"]:
        for s in MANUAL:
            r = cell(d, m, s)
            if r is None or r["n"] < FULL_N[d]:
                return False
    return True


def models():
    m = list(main_summary()["model"].unique())
    ordered = [x for x in (SMALL, LARGE) if x in m] + [x for x in m if x not in (SMALL, LARGE)]
    return [x for x in ordered if model_ready(x)]


def cell(dataset, model, strategy, fmt="markdown", context="full", think=False, perturbed=False, partial=False):
    """One row of the summary (a pandas Series), or None if that run does not exist. A run that is
    still in progress (fewer questions than the full sample) counts as missing unless partial=True,
    so an unfinished run is never reported as a result."""
    s = summary()
    r = s[(s.dataset == dataset) & (s.model == model) & (s.strategy == strategy) & (s.fmt == fmt)
          & (s.context == context) & (s.think == think) & (s.perturbed == perturbed)]
    if r.empty:
        return None
    r = r.iloc[0]
    full = PERTURBED_N if perturbed else FULL_N[dataset]
    return r if partial or r.n >= full else None


def complete(row, dataset):
    return row is not None and row["n"] >= FULL_N[dataset]


def optimized_strategies(model):
    s = main_summary()
    names = s[(s.model == model) & (s.strategy.str.contains(":"))]["strategy"].unique()
    return sorted(names, key=strategy_rank)


def retrieval_recall():
    p = ROOT / "results" / "retrieval_recall.csv"
    return pd.read_csv(p) if p.exists() else None


def dataset_stats():
    """Parse results/dataset_stats.md (written by scripts/dataset_stats.py)."""
    p = ROOT / "results" / "dataset_stats.md"
    lines = [l for l in p.read_text().splitlines() if l.startswith("|") and not l.startswith("|:")]
    head = [h.strip() for h in lines[0].strip("|").split("|")]
    rows = [[c.strip() for c in l.strip("|").split("|")] for l in lines[1:]]
    return pd.DataFrame(rows, columns=head)


def vpsc_diagnostics(model):
    """How often the grounding check fired and whether it changed the vote, per dataset."""
    out = []
    df = main_runs()
    for d in DATASETS:
        v = df[(df.dataset == d) & (df.model == model) & (df.strategy == "vpsc")]
        p = df[(df.dataset == d) & (df.model == model) & (df.strategy == "pot_sc")].set_index("uid")
        if v.empty or p.empty:
            continue
        progs = executed = ungrounded = flagged_q = fallback = changed = 0
        flagged_correct = 0
        for r in v.itertuples():
            e = r.extra
            votes, grounded = e["votes"], e["grounded"]
            progs += len(votes)
            executed += e["n_executed"]
            ung = [1 for a, g in zip(votes, grounded) if a is not None and not g]
            ungrounded += len(ung)
            if ung:
                flagged_q += 1
                flagged_correct += bool(r.correct)
            if e["n_executed"] and not any(grounded):
                fallback += 1
            if r.uid in p.index and str(p.loc[r.uid, "answer"]) != str(r.answer):
                changed += 1
        agreement = v["extra"].map(lambda e: e.get("agreement", 0)).mean()
        out.append(dict(dataset=d, questions=len(v), programs=progs, executed=executed, ungrounded=ungrounded,
                        flagged_questions=flagged_q, flagged_correct=flagged_correct, all_ungrounded=fallback,
                        answers_changed=changed, agreement=agreement))
    return pd.DataFrame(out)


def artifacts():
    """Saved optimization artifacts (DSPy meta files and TextGrad prompts)."""
    a = ROOT / "artifacts"
    out = {}
    for p in sorted(a.glob("dspy_*.meta.json")):
        out[p.name.replace(".meta.json", "")] = json.load(open(p))
    for p in sorted(a.glob("textgrad_*.json")):
        out[p.stem] = json.load(open(p))
    return out


def pct(x, d=1):
    return "–" if x is None or pd.isna(x) else f"{100 * x:.{d}f}"


__all__ = ["model_label", "strategy_label", "strategy_rank"]


@lru_cache(None)
def code_stats():
    """(library modules, library lines, automated tests) counted from the project itself."""
    import subprocess
    modules = [p for p in (ROOT / "finreason").glob("*.py") if p.name != "__init__.py"]
    lines = sum(len(p.read_text().splitlines()) for p in modules)
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q"], cwd=ROOT, capture_output=True,
                         text=True, env={**__import__("os").environ, "HF_HUB_OFFLINE": "1"}).stdout
    tests = next((int(l.split()[0]) for l in out.splitlines() if l.split() and l.split()[1:2] == ["tests"]), 0)
    return len(modules), lines, tests


APP_PAGES = ["Overview", "Ask", "Compare", "Results", "Optimization", "Robustness", "Errors", "Data", "Method"]
