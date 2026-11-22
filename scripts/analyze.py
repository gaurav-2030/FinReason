"""Aggregate every run in results/runs into summary tables, significance tests and figures.

    python scripts/analyze.py
Writes results/*.csv, results/report.md and results/figures/*.png.
"""
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finreason.answers import score, token_f1
from finreason.config import ARTIFACTS, FIGURES_DIR, RESULTS, RUNS_DIR, SEED
from finreason.data import load_dataset
from finreason.errors import CATEGORIES, classify_error
from finreason import figures
from finreason.figures import strategy_rank
from finreason.metrics import bootstrap_ci, holm, mcnemar
from finreason.perturb import perturb_dataset
from finreason.strategies import Prediction

SETTING = ["dataset", "perturbed", "model", "fmt", "context", "think"]
BASELINE = "cot_fs"


def example_index(df):
    """(dataset, uid) -> Example for every question that appears in the runs."""
    index = {}
    for dataset, split in df[["dataset", "split"]].drop_duplicates().itertuples(index=False):
        for ex in load_dataset(dataset, split):
            index[(dataset, ex.uid)] = ex
    for run in df.loc[df["perturbed"], "run"].unique():
        n = int(re.search(r"_n(\d+)__", run).group(1))
        for ex in perturb_dataset(load_dataset("finqa", "test", n=n, seed=SEED), seed=SEED):
            index[("finqa", ex.uid)] = ex
    return index


def _value(v):
    return None if v is None or (isinstance(v, float) and math.isnan(v)) else v


def rescore(df):
    """Score every saved answer again with the current rules, so a change to the scoring
    (e.g. the tolerance) never requires re-running the models."""
    index = example_index(df)
    rows = []
    for r in df.itertuples():
        ex = index[(r.dataset, r.uid)]
        answer = _value(r.answer)
        correct, exact = score(answer, ex.gold, ex.question, ex.scale)
        pred = Prediction(answer=answer, code=r.code or "", output=r.output or "")
        rows.append({"correct": correct, "exact_match": exact,
                     "correct_1pct": score(answer, ex.gold, ex.question, ex.scale, rel_tol=0.01)[0],
                     "f1": token_f1(answer, ex.gold, ex.question, ex.scale),
                     "error_category": classify_error(pred, ex, correct)})
    rescored = pd.DataFrame(rows, index=df.index)
    for column in rescored:
        df[column] = rescored[column]
    return df


def load_runs():
    rows = []
    for path in sorted(RUNS_DIR.glob("*.jsonl")):
        if " " in path.name:   # cloud-sync conflict copies ("name 2.jsonl") are not real runs
            print(f"skipping {path.name}", file=sys.stderr)
            continue
        rows += [json.loads(line) for line in open(path)]
    df = rescore(pd.DataFrame(rows))
    df["total_tokens"] = df["prompt_tokens"] + df["completion_tokens"]
    df["format_failure"] = df["how"].isna() | (df["how"] == "last_number")
    df["code_failure"] = (df["sandbox_error"].fillna("") != "") & df["answer"].isna()
    return df


def summarize(df):
    rows = []
    for keys, g in df.groupby(SETTING + ["strategy"]):
        lo, hi = bootstrap_ci(g["correct"].astype(int))
        rows.append(dict(zip(SETTING + ["strategy"], keys), n=len(g),
                         accuracy=g["correct"].mean(), ci_low=lo, ci_high=hi,
                         accuracy_1pct=g["correct_1pct"].mean(),
                         exact_match=g["exact_match"].mean(), f1=g["f1"].mean(),
                         format_failure=g["format_failure"].mean(),
                         code_failure=g["code_failure"].mean(),
                         calls=g["n_calls"].mean(), prompt_tokens=g["prompt_tokens"].mean(),
                         completion_tokens=g["completion_tokens"].mean(),
                         total_tokens=g["total_tokens"].mean(), latency_s=g["latency"].mean(),
                         cost_per_1k_usd=1000 * g["cost_usd"].mean()))
    out = pd.DataFrame(rows)
    out["tokens_per_correct"] = out["total_tokens"] / out["accuracy"].where(out["accuracy"] > 0)
    out["order"] = out["strategy"].map(strategy_rank)
    return out.sort_values(SETTING + ["order", "strategy"]).drop(columns="order")


def significance(df):
    """McNemar test of every strategy against few-shot CoT on the same questions (Holm-adjusted
    within each setting)."""
    rows = []
    for keys, g in df.groupby(SETTING):
        pivot = g.pivot_table(index="uid", columns="strategy", values="correct", aggfunc="first")
        if BASELINE not in pivot:
            continue
        group_rows = []
        for strategy in pivot.columns:
            if strategy == BASELINE:
                continue
            paired = pivot[[BASELINE, strategy]].dropna()
            b, c, p = mcnemar(paired[strategy].astype(bool), paired[BASELINE].astype(bool))
            group_rows.append(dict(zip(SETTING, keys), strategy=strategy, n=len(paired),
                                   accuracy=paired[strategy].mean(), baseline=paired[BASELINE].mean(),
                                   wins=b, losses=c, p_value=p))
        if group_rows:
            for row, adj in zip(group_rows, holm([r["p_value"] for r in group_rows])):
                row["p_holm"] = adj
            rows += group_rows
    return pd.DataFrame(rows)


def main_setting(df):
    """The main comparison: markdown tables, full context, no thinking, original questions."""
    return df[(df["fmt"] == "markdown") & (df["context"] == "full") & (~df["think"])
              & (~df["perturbed"])]


def stratified(df):
    main = main_setting(df).copy()
    main["steps"] = main["n_steps"].clip(upper=3).map({1: "1 step", 2: "2 steps", 3: "3+ steps"})
    by_steps = main.pivot_table(index=["dataset", "model", "strategy"], columns="steps",
                                values="correct", aggfunc="mean")
    by_evidence = main.pivot_table(index=["dataset", "model", "strategy"], columns="evidence",
                                   values="correct", aggfunc="mean")
    return by_steps, by_evidence


def error_table(df):
    main = main_setting(df)
    wrong = main[~main["correct"]]
    table = wrong.pivot_table(index=["dataset", "model", "strategy"], columns="error_category",
                              values="uid", aggfunc="count", fill_value=0)
    return table.reindex(columns=[c for c in CATEGORIES if c in table.columns])


def perturbation(df):
    """Accuracy on original vs perturbed versions of the same FinQA questions."""
    rows = []
    pert = df[df["perturbed"]]
    expected = pert.groupby("run")["uid"].nunique().max() if len(pert) else 0
    for keys, g in pert.groupby(["model", "strategy", "fmt", "context", "think"]):
        model, strategy, fmt, context, think = keys
        g = g.assign(original_uid=g["meta"].map(lambda m: m["original_uid"]))
        orig = df[(~df["perturbed"]) & (df["dataset"] == "finqa") & (df["model"] == model)
                  & (df["strategy"] == strategy) & (df["fmt"] == fmt) & (df["context"] == context)
                  & (df["think"] == think)].set_index("uid")["correct"]
        g = g[g["original_uid"].isin(orig.index)]
        if g.empty:
            continue
        if len(g) < expected:   # still running
            continue
        before = orig.loc[g["original_uid"]].astype(bool).values
        after = g["correct"].astype(bool).values
        b, c, p = mcnemar(before, after)
        rows.append({"model": model, "strategy": strategy, "n": len(g),
                     "original_accuracy": before.mean(), "perturbed_accuracy": after.mean(),
                     "drop": before.mean() - after.mean(), "only_original_right": b,
                     "only_perturbed_right": c, "p_value": p})
    return pd.DataFrame(rows)


def complete_runs(summary):
    """Rows of runs that answered the full sample (as many questions as the largest run on that
    dataset), so a run that is still in progress never appears in a derived table."""
    full = summary.groupby(["dataset", "perturbed"])["n"].transform("max")
    return summary[summary["n"] >= full]


def ablations(summary):
    """One row per ablation: what changed and the accuracy of each variant."""
    def acc(**conditions):
        rows = complete_runs(summary)
        for column, value in conditions.items():
            rows = rows[rows[column] == value]
        return rows.set_index(["dataset", "model"])["accuracy"]
    base = dict(perturbed=False, think=False)
    parts = {
        "format: markdown": acc(strategy="cot_fs", fmt="markdown", context="full", **base),
        "format: json": acc(strategy="cot_fs", fmt="json", context="full", **base),
        "format: html": acc(strategy="cot_fs", fmt="html", context="full", **base),
        "format: text": acc(strategy="cot_fs", fmt="text", context="full", **base),
        "PoT, full page": acc(strategy="pot_fs", fmt="markdown", context="full", **base),
        "PoT, retrieved top-5": acc(strategy="pot_fs", fmt="markdown", context="retrieved", **base),
        "zero-shot CoT, no thinking": acc(strategy="cot_zs", fmt="markdown", context="full", **base),
        "zero-shot CoT, thinking": acc(strategy="cot_zs", fmt="markdown", context="full",
                                       perturbed=False, think=True),
    }
    return pd.DataFrame(parts)


def vpsc_diagnostics(df):
    """How often VPSC's grounding check fired and whether it changed the vote (main setting).
    A question is flagged when at least one executed program used a number not found in the report."""
    main = main_setting(df)
    rows = []
    full = main.groupby("dataset")["uid"].nunique()
    for (dataset, model), v in main[main["strategy"] == "vpsc"].groupby(["dataset", "model"]):
        if len(v) < full[dataset]:   # still running
            continue
        ablation = main[(main["dataset"] == dataset) & (main["model"] == model)
                        & (main["strategy"] == "pot_sc")].set_index("uid")
        programs = executed = ungrounded = flagged = flagged_wrong = fallback = changed = 0
        for r in v.itertuples():
            votes, grounded = r.extra["votes"], r.extra["grounded"]
            programs += len(votes)
            executed += r.extra["n_executed"]
            n_bad = sum(1 for a, g in zip(votes, grounded) if a is not None and not g)
            ungrounded += n_bad
            if n_bad:
                flagged += 1
                flagged_wrong += not r.correct
            if r.extra["n_executed"] and not any(grounded):
                fallback += 1
            if r.uid in ablation.index and str(ablation.loc[r.uid, "answer"]) != str(r.answer):
                changed += 1
        acc_ablation = ablation["correct"].mean() if len(ablation) else float("nan")
        rows.append({"dataset": dataset, "model": model, "questions": len(v),
                     "vpsc_accuracy": v["correct"].mean(), "pot_sc_accuracy": acc_ablation,
                     "programs": programs, "executed": executed, "ungrounded": ungrounded,
                     "flagged_questions": flagged, "flagged_wrong": flagged_wrong,
                     "all_ungrounded": fallback, "answers_changed": changed,
                     "agreement": v["extra"].map(lambda e: e.get("agreement", 0)).mean()})
    return pd.DataFrame(rows)


def optimization_costs():
    """One-time cost of each automated optimization (from the saved artifacts)."""
    rows = []
    for path in sorted(ARTIFACTS.glob("dspy_*.meta.json")):
        m = json.load(open(path))
        rows.append({"artifact": path.name.replace(".meta.json", ""), "model": m["lm_spec"],
                     "validation_accuracy": m["val_accuracy"], "minutes": m["compile_seconds"] / 60,
                     "calls": m["compile_lm_calls"],
                     "tokens": m["compile_prompt_tokens"] + m["compile_completion_tokens"]})
    for path in sorted(ARTIFACTS.glob("textgrad_*.json")):
        m = json.load(open(path))
        rows.append({"artifact": path.stem, "model": m["task_model"],
                     "validation_accuracy": m["val_accuracy"], "minutes": m["seconds"] / 60,
                     "calls": m["usage"]["task_calls"] + m["usage"]["optimizer_calls"],
                     "tokens": m["usage"]["prompt_tokens"] + m["usage"]["completion_tokens"]})
    return pd.DataFrame(rows)


def main_summary(summary):
    return summary[(summary["fmt"] == "markdown") & (summary["context"] == "full")
                   & (~summary["think"]) & (~summary["perturbed"])]


def complete_records(df):
    """Answers of runs that covered the full sample (runs still in progress are left out)."""
    size = df.groupby("run")["uid"].transform("count")
    full = size.groupby([df["dataset"], df["perturbed"]]).transform("max")
    return df[size >= full]


def make_figures(df, summary, pert, ablation):
    figures.style()
    df = complete_records(df)
    summary = complete_runs(summary)
    main = main_summary(summary)
    figures.accuracy_heatmap(main, FIGURES_DIR / "accuracy_heatmap.png")
    for dataset in main["dataset"].unique():
        figures.pareto(main, dataset, FIGURES_DIR / f"pareto_{dataset}.png")
        figures.by_steps(main_setting(df), dataset, FIGURES_DIR / f"steps_{dataset}.png")
        figures.error_heatmap(main_setting(df), CATEGORIES, dataset, FIGURES_DIR / f"errors_{dataset}.png")
    figures.perturbation_dumbbell(pert, FIGURES_DIR / "perturbation.png")
    figures.ablation_panels(ablation, FIGURES_DIR / "ablations.png")
    figures.optimization_dots(main, FIGURES_DIR / "optimization.png")


def fmt_table(df, floatfmt=".3f"):
    return df.to_markdown(index=not isinstance(df.index, pd.RangeIndex), floatfmt=floatfmt)


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = load_runs()
    summary = summarize(df)        # every run, with its n (the app marks runs still in progress)
    done = complete_records(df)    # derived tables use finished runs only
    sig = significance(done)
    by_steps, by_evidence = stratified(done)
    errors = error_table(done)
    pert = perturbation(df)
    ablation = ablations(summary)
    costs = optimization_costs()
    vpsc = vpsc_diagnostics(df)
    summary.to_csv(RESULTS / "summary.csv", index=False)
    by_steps.to_csv(RESULTS / "accuracy_by_steps.csv")
    by_evidence.to_csv(RESULTS / "accuracy_by_evidence.csv")
    vpsc.to_csv(RESULTS / "vpsc.csv", index=False)
    sig.to_csv(RESULTS / "significance.csv", index=False)
    errors.to_csv(RESULTS / "errors.csv")
    pert.to_csv(RESULTS / "perturbation.csv", index=False)
    ablation.to_csv(RESULTS / "ablations.csv")
    costs.to_csv(RESULTS / "optimization_costs.csv", index=False)
    for old_figure in FIGURES_DIR.glob("*.png"):
        old_figure.unlink()
    make_figures(df, summary, pert, ablation)

    columns = SETTING + ["strategy", "n", "accuracy", "ci_low", "ci_high", "accuracy_1pct",
                         "exact_match", "f1", "format_failure", "code_failure", "calls",
                         "total_tokens", "tokens_per_correct", "latency_s"]
    sections = [("Summary of all runs", fmt_table(summary[columns].reset_index(drop=True))),
                ("McNemar tests against few-shot CoT (Holm-adjusted)", fmt_table(sig) if not sig.empty else "-"),
                ("Accuracy by number of reasoning steps (main setting)", fmt_table(by_steps)),
                ("Accuracy by evidence source (main setting)", fmt_table(by_evidence)),
                ("Error taxonomy: counts of wrong answers (main setting)", fmt_table(errors, ".0f")),
                ("Numerical perturbation test", fmt_table(pert) if not pert.empty else "-"),
                ("Ablations: table format, retrieval, thinking", fmt_table(ablation)),
                ("VPSC grounding diagnostics", fmt_table(vpsc) if not vpsc.empty else "-"),
                ("One-time cost of automated optimization", fmt_table(costs) if not costs.empty else "-")]
    report = "# FinReason results\n\n" + "\n\n".join(f"## {t}\n\n{body}" for t, body in sections)
    (RESULTS / "report.md").write_text(report + "\n")
    print(report)


if __name__ == "__main__":
    main()
