"""Replay TRACE decisions from logged candidates: ablations, the adaptive policy, weight selection on
dev, oracle coverage and selective prediction (risk-coverage). No model calls are made: every
candidate of a `trace` run is logged with its answer, audit findings and its own token cost, so each
variant below is an exact deterministic re-decision over the same calls.

    python scripts/trace_replay.py            # writes results/trace_*.csv and results/trace_report.md
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finreason.answers import score
from finreason.config import RESULTS, RUNS_DIR
from finreason.strategies import _same_answer
from finreason.trace import W_FLAGGED, W_PROGRAM, W_SOFT, W_TEXT, pool_vote

CELL_KINDS = {"name_cell", "name_year", "question_span"}
VIEWS_ALL = ["pot_guided", "cot", "pot_plain", "pot_guided_t", "cot_t", "decomp"]

VARIANTS = {
    # name: config
    "TRACE (full)": {},
    "TRACE adaptive": {"adaptive": True},
    "- repair": {"repair": False},
    "- cell-level audit (v1+v2 checks only)": {"kinds": "no_cell"},
    "- audit entirely (no filter, no repair)": {"kinds": "none", "repair": False},
    "- text views (programs only)": {"views": ["pot_guided", "pot_plain", "pot_guided_t"]},
    "- decomposition view": {"views": ["pot_guided", "cot", "pot_plain", "pot_guided_t", "cot_t"]},
    "- view diversity (guided programs + CoT only)": {"views": ["pot_guided", "pot_guided_t", "cot", "cot_t"]},
    "- ans fix": {"ans_fix": False},
}


def load(path):
    return [json.loads(line) for line in open(path)]


def problems_of(c, kinds):
    probs = c.get("problems") or []
    if kinds == "none":
        return []
    if kinds == "no_cell":
        return [p for p in probs if p[0] not in CELL_KINDS]
    return probs


def weight(c, cfg, kinds):
    if c["answer"] is None:
        return 0.0
    if not c["is_program"]:
        return 0.0 if problems_of(c, kinds) else cfg.get("w_text", W_TEXT)
    if not cfg.get("ans_fix", True) and c.get("ans_fixed"):
        return 0.0
    sev = [p[1] for p in problems_of(c, kinds)]
    if not sev:
        return cfg.get("w_program", W_PROGRAM)
    return cfg.get("w_flagged", W_FLAGGED) if max(sev) >= 1.0 else cfg.get("w_soft", W_SOFT)


def decide(record, cfg):
    """Return (answer, confidence, cost dict, early_exit) for one logged trace record under cfg."""
    cands = record["extra"]["candidates"]
    kinds = cfg.get("kinds", "all")
    views = cfg.get("views", VIEWS_ALL)
    by_view = {c["view"]: c for c in cands}
    cost = lambda cs: {k: sum(c["cost"][k] for c in cs) for k in ("calls", "prompt_tokens",
                                                                  "completion_tokens", "latency")}
    pg, cg = by_view.get("pot_guided"), by_view.get("cot")
    if cfg.get("adaptive"):
        clean = pg and pg["answer"] is not None and not problems_of(pg, kinds) and \
            (cfg.get("ans_fix", True) or not pg.get("ans_fixed"))
        if clean and cg and cg["answer"] is not None and _same_answer(pg["answer"], cg["answer"]):
            return pg["answer"], 1.0, cost([pg, cg]), True
    use = [c for c in cands if c["view"] in views]
    if cfg.get("repair", True) and kinds != "none":
        for c in cands:
            parent = c.get("parent")
            if not parent or parent not in views:
                continue
            p = by_view[parent]
            hard = [x for x in problems_of(p, kinds) if x[1] >= 1.0]
            # the repair call happens only if the parent failed under this variant's audit
            if hard or (p["answer"] is None and p.get("error")):
                use.append(c)
    weights = [weight(c, cfg, kinds) for c in use]
    repaired = {c.get("parent") for c, w in zip(use, weights) if c.get("parent") and w > 0}
    weights = [0.0 if c["view"] in repaired else w for c, w in zip(use, weights)]
    chosen, best, total = pool_vote(use, weights)
    if chosen is None:
        chosen = next((c for c in use if c["answer"] is not None), None)
    answer = chosen["answer"] if chosen else None
    return answer, (best / total if total else 0.0), cost(use), False


def correct(record, answer):
    return bool(score(answer, record["gold"], record["question"], record["scale"])[0])


def evaluate(records, cfg):
    rows = []
    for r in records:
        a, conf, cost, early = decide(r, cfg)
        rows.append({"uid": r["uid"], "correct": correct(r, a), "confidence": conf, "early": early,
                     "tokens": cost["prompt_tokens"] + cost["completion_tokens"], "calls": cost["calls"],
                     "latency": cost["latency"]})
    return pd.DataFrame(rows)


def oracle(records):
    return np.mean([any(c["answer"] is not None and correct(r, c["answer"])
                        for c in r["extra"]["candidates"]) for r in records])


def risk_coverage(correct_flags, confidence):
    """Sort by confidence (ties broken randomly with a fixed seed); return coverage, selective
    accuracy, AURC (area under the risk-coverage curve; lower is better) and accuracy at 50/80%."""
    rng = np.random.default_rng(0)
    order = np.lexsort((rng.random(len(confidence)), -np.asarray(confidence)))
    c = np.asarray(correct_flags, dtype=float)[order]
    n = len(c)
    acc = np.cumsum(c) / np.arange(1, n + 1)
    coverage = np.arange(1, n + 1) / n
    aurc = float(np.mean(1 - acc))
    at = lambda q: float(acc[max(0, int(np.ceil(q * n)) - 1)])
    return coverage, acc, aurc, at(0.5), at(0.8)


def tune_on_dev(dev_records):
    """Pick vote weights on the dev splits only (grid), maximizing mean dev accuracy."""
    grid = itertools.product([0.0, 0.25], [0.0, 0.5, 1.0], [0.5, 0.75, 1.0])
    best = None
    for w_flagged, w_soft, w_text in grid:
        cfg = {"w_flagged": w_flagged, "w_soft": w_soft, "w_text": w_text}
        acc = np.mean([evaluate(recs, cfg)["correct"].mean() for recs in dev_records.values()])
        if best is None or acc > best[0] + 1e-9:
            best = (acc, cfg)
    return best


def main():
    runs = sorted(RUNS_DIR.glob("*__trace__*.jsonl"))
    dev = {p.name.split("__")[0]: load(p) for p in runs if "_dev_" in p.name}
    test = {p.name.split("__")[0] + "__" + p.name.split("__")[1]: load(p) for p in runs
            if "_dev_" not in p.name}
    lines = ["# TRACE replay\n"]
    if dev:
        acc, cfg = tune_on_dev(dev)
        lines.append(f"Weights selected on dev ({', '.join(dev)}): {cfg} -> mean dev accuracy {acc:.3f}\n")
    rows, rc_rows = [], []
    for name, records in {**{k + " (dev)": v for k, v in dev.items()}, **test}.items():
        for variant, cfg in VARIANTS.items():
            df = evaluate(records, cfg)
            rows.append({"run": name, "variant": variant, "n": len(df), "accuracy": df["correct"].mean(),
                         "tokens_per_q": df["tokens"].mean(), "calls_per_q": df["calls"].mean(),
                         "early_exit_rate": df["early"].mean(),
                         "accuracy_early": df.loc[df["early"], "correct"].mean() if df["early"].any() else np.nan})
        df = evaluate(records, {})
        _, _, aurc, a50, a80 = risk_coverage(df["correct"], df["confidence"])
        rc_rows.append({"run": name, "method": "TRACE", "accuracy": df["correct"].mean(), "aurc": aurc,
                        "acc_at_50": a50, "acc_at_80": a80, "oracle": oracle(records)})
    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "trace_ablations.csv", index=False)
    pd.DataFrame(rc_rows).to_csv(RESULTS / "trace_selective.csv", index=False)
    lines.append(out.to_markdown(index=False, floatfmt=".3f"))
    lines.append("\n\n" + pd.DataFrame(rc_rows).to_markdown(index=False, floatfmt=".3f"))
    (RESULTS / "trace_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
