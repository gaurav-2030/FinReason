"""Charts for the review documents. Every chart is computed from the experiment results (via data.py)
or from published numbers quoted in the literature survey. Charts whose experiments have not run
yet return None, and the documents say so instead of showing an empty chart."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

import data  # noqa: E402
from common import BUILD  # noqa: E402

SURFACE, INK, INK2, GRID = "#ffffff", "#0b0b0b", "#52514e", "#e4e3de"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4",
                                                         "#008300", "#4a3aa7", "#e34948")
GREY = "#b4b2aa"
MODEL_COLOR = {data.SMALL: BLUE, data.LARGE: ORANGE}
FIG = BUILD / "fig"


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
        "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False, "xtick.color": INK2,
        "ytick.color": INK2, "axes.labelcolor": INK2, "text.color": INK, "font.size": 10, "axes.titlesize": 11.5,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False,
        "font.family": ["Arial", "DejaVu Sans"],
    })


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    path = FIG / f"{name}.png"
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)
    return path


def label(s):
    return data.strategy_label(s)


# ------------------------------------------------------------------------------------------
# Review 1
# ------------------------------------------------------------------------------------------
def lit_gap():
    """Published FinQA test results: the gap that motivates the project."""
    with plt.rc_context({"font.size": 12.5, "axes.titlesize": 13.5}):
        return _lit_gap()


def _lit_gap():
    rows = [("Human financial experts [1]", 91.16, GREY), ("PoT + self-consistency, Codex [15]", 68.1, BLUE),
            ("Program-of-Thought, Codex [15]", 64.5, BLUE), ("FinQANet, fine-tuned RoBERTa-large [1]", 61.24, BLUE),
            ("Chain-of-Thought + SC, Codex [15]", 44.4, BLUE), ("Chain-of-Thought, Codex [15]", 40.4, BLUE)]
    fig, ax = plt.subplots(figsize=(6.3, 3.3))
    y = np.arange(len(rows))[::-1]
    ax.barh(y, [r[1] for r in rows], color=[r[2] for r in rows], height=0.55)
    for yi, r in zip(y, rows):
        ax.text(r[1] + 1, yi, f"{r[1]:.1f}", va="center", fontsize=9.5, color=INK)
    ax.set_yticks(y, [r[0] for r in rows])
    ax.set_xlim(0, 100)
    ax.set_xlabel("Execution accuracy on the FinQA test set (%)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Published FinQA test results")
    return save(fig, "lit_gap")


# ------------------------------------------------------------------------------------------
# Review 2
# ------------------------------------------------------------------------------------------
def data_composition():
    st = data.dataset_stats().set_index("set")
    sets = [("finqa test sample n=100", "FinQA (n=100)"), ("tatqa test sample n=100", "TAT-QA (n=100)"),
            ("indian test (full)", "Indian set (n=44)")]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 2.5))
    for ax, cols, title, colors in [
        (axes[0], ["1 step", "2 steps", "3+ steps"], "Reasoning steps needed", [BLUE, ORANGE, AQUA]),
        (axes[1], ["table", "text", "table-text"], "Where the evidence is", [BLUE, ORANGE, AQUA])]:
        for i, (key, name) in enumerate(sets):
            vals = np.array([float(st.loc[key, c]) for c in cols])
            share = vals / vals.sum() * 100
            left = 0
            for j, (v, c) in enumerate(zip(share, colors)):
                ax.barh(i, v, left=left, color=c, height=0.6, edgecolor="white", linewidth=1.5)
                if v >= 7:
                    ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", color="white", fontsize=9, fontweight="bold")
                left += v
        ax.set_yticks(range(len(sets)), [s[1] for s in sets])
        ax.invert_yaxis()
        ax.set_xlim(0, 100)
        ax.grid(False)
        ax.set_xticks([])
        ax.spines["bottom"].set_visible(False)
        ax.set_title(title)
        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors]
        ax.legend(handles, cols, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=9)
    fig.tight_layout()
    return save(fig, "data_composition")


def retrieval_recall():
    rr = data.retrieval_recall()
    if rr is None:
        return None
    ks = [1, 3, 5, 8, 10]
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.0), sharey=True)
    for ax, d in zip(axes, ["finqa", "tatqa"]):
        sub = rr[rr.dataset == d]
        for m, c, mk in [("bm25", ORANGE, "s"), ("dense", AQUA, "^"), ("hybrid", BLUE, "o")]:
            r = sub[sub.method == m].iloc[0]
            vals = [100 * r[f"recall@{k}"] for k in ks]
            ax.plot(ks, vals, color=c, lw=2, marker=mk, ms=6, label={"bm25": "BM25", "dense": "Dense (MiniLM + FAISS)", "hybrid": "Hybrid (RRF)"}[m])
        ax.set_title(f"{data.DLABEL[d]} test set (n = {int(sub.n.iloc[0])})")
        ax.set_xlabel("k (evidence units kept)")
        ax.set_xticks(ks)
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("Recall of gold evidence (%)")
    axes[1].legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    return save(fig, "retrieval_recall")


def indian_types():
    import json
    from common import ROOT
    rs = [json.loads(l) for l in open(ROOT / "data/indian/indian_set.jsonl")]
    names = {"percent": "percent", "": "ratio / ₹ amount", "crore": "₹ crore", "lakh": "₹ lakh", "billion": "₹ billion", "million": "₹ million"}
    s = pd.Series([names.get(r.get("scale", ""), r.get("scale")) for r in rs])
    s[[isinstance(r["gold"], str) for r in rs]] = "yes / no"
    counts = s.value_counts()
    comp = pd.Series([r["company"].replace(" Limited", "").replace(" Company", "") for r in rs]).value_counts()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 2.5))
    for ax, c, title in [(axes[0], comp, "Questions per company"), (axes[1], counts, "Answer type / unit")]:
        y = np.arange(len(c))
        ax.barh(y, c.values, color=BLUE, height=0.6)
        for yi, v in zip(y, c.values):
            ax.text(v + 0.3, yi, str(v), va="center", fontsize=9)
        ax.set_yticks(y, c.index)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.set_title(title)
    fig.tight_layout()
    return save(fig, "indian_types")


# ------------------------------------------------------------------------------------------
# Review 3
# ------------------------------------------------------------------------------------------
def main_bars(model):
    ms = data.main_summary()
    ms = ms[ms.model == model]
    if ms.empty:
        return None
    order = [s for s in data.MAIN_ORDER if s in set(ms.strategy)]
    dsets = [d for d in data.DATASETS if d in set(ms.dataset)]
    fig, axes = plt.subplots(1, len(dsets), figsize=(3.4 * len(dsets) + 1.2, 3.5), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, d in zip(axes, dsets):
        y = np.arange(len(order))[::-1]
        for yi, s in zip(y, order):
            r = data.cell(d, model, s)
            if r is None:
                ax.text(2, yi, "pending", va="center", fontsize=8.5, color=INK2, style="italic")
                continue
            c = ORANGE if s == "vpsc" else BLUE
            acc = 100 * r.accuracy
            ax.barh(yi, acc, color=c, height=0.62)
            ax.errorbar(acc, yi, xerr=[[acc - 100 * r.ci_low], [100 * r.ci_high - acc]], fmt="none", ecolor=INK, elinewidth=0.9, capsize=2.5)
            partial = "" if data.complete(r, d) else f" (n={int(r.n)})"
            ax.text(100 * r.ci_high + 2, yi, f"{acc:.0f}{partial}", va="center", fontsize=8.8)
        ax.set_yticks(y, [label(s) for s in order])
        ax.set_xlim(0, 105)
        ax.grid(axis="y", visible=False)
        ax.set_title(data.DLABEL[d])
        ax.set_xlabel("Execution accuracy (%)")
    fig.suptitle(f"{data.model_label(model)}: accuracy by strategy (bars: 95% bootstrap CI)", x=0.01, ha="left", fontweight="bold", fontsize=11.5)
    fig.tight_layout()
    return save(fig, f"main_bars_{data.model_label(model)}")


def _place_labels(ax, pts, min_gap=6.0):
    """pts: list of (x, y, text). Points close on the (log) x axis form a cluster; inside a cluster the
    labels are spaced at least min_gap accuracy points apart and joined to their dot by a thin line."""
    pts = sorted(pts, key=lambda p: p[0])
    clusters, cur = [], []
    for p in pts:
        if cur and np.log10(p[0]) - np.log10(cur[0][0]) > 0.12:
            clusters.append(cur)
            cur = []
        cur.append(p)
    if cur:
        clusters.append(cur)
    for cl in clusters:
        cl = sorted(cl, key=lambda p: -p[1])
        ys = []
        for p in cl:
            y = p[1] if not ys else min(p[1], ys[-1] - min_gap)
            ys.append(y)
        shift = max(0, -min(ys) + 2)
        x_text = max(p[0] for p in cl) * 1.07
        for p, y in zip(cl, ys):
            y += shift
            ax.annotate(p[2], (p[0], p[1]), xytext=(x_text, y), textcoords="data", fontsize=8.3, color=INK2, va="center",
                        arrowprops=dict(arrowstyle="-", color="#c9c7bf", lw=0.6, shrinkA=0, shrinkB=3))


def pareto(dataset):
    ms = data.main_summary()
    ms = ms[ms.dataset == dataset]
    if ms.empty:
        return None
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for model in data.models():
        sub = ms[(ms.model == model) & (~ms.strategy.str.contains(":"))]
        if sub.empty:
            continue
        ax.errorbar(sub.total_tokens, 100 * sub.accuracy, yerr=[100 * (sub.accuracy - sub.ci_low), 100 * (sub.ci_high - sub.accuracy)],
                    fmt="o", color=MODEL_COLOR.get(model, GREEN), ms=6, elinewidth=0.8, capsize=0, label=data.model_label(model),
                    markeredgecolor="white", markeredgewidth=1)
        pts = []
        for r in sub.itertuples():
            same = [p for p in pts if abs(np.log(p[0] / r.total_tokens)) < 0.02 and abs(p[1] - 100 * r.accuracy) < 0.5]
            if same:
                i = pts.index(same[0])
                pts[i] = (same[0][0], same[0][1], same[0][2] + " = " + label(r.strategy))
            else:
                pts.append((r.total_tokens, 100 * r.accuracy, label(r.strategy)))
        _place_labels(ax, pts)
    ax.set_xscale("log")
    ax.xaxis.set_major_locator(matplotlib.ticker.FixedLocator([500, 1000, 2000, 5000, 10000, 20000]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Mean tokens per question (prompt + completion, log scale)")
    ax.set_ylabel("Execution accuracy (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Accuracy vs. cost: {data.DLABEL[dataset]}")
    if len(data.models()) > 1:
        ax.legend(loc="lower right")
    fig.tight_layout()
    return save(fig, f"pareto_{dataset}")


def by_steps(model):
    df = data.main_runs()
    df = df[(df.model == model) & (df.dataset.isin(["finqa", "tatqa", "indian"]))]
    strategies = [s for s in ["direct", "cot_fs", "pot_fs", "vpsc"] if s in set(df.strategy)]
    if not strategies:
        return None
    df = df.assign(bucket=df.n_steps.clip(upper=3))
    dsets = [d for d in data.DATASETS if d in set(df.dataset)]
    fig, axes = plt.subplots(1, len(dsets), figsize=(3.3 * len(dsets) + 0.6, 2.9), sharey=True)
    axes = np.atleast_1d(axes)
    colors = [GREY, BLUE, AQUA, ORANGE]
    for ax, d in zip(axes, dsets):
        sub = df[df.dataset == d]
        w = 0.8 / len(strategies)
        for i, s in enumerate(strategies):
            g = sub[sub.strategy == s].groupby("bucket")["correct"].agg(["mean", "count"])
            xs = [b - 1 + (i - (len(strategies) - 1) / 2) * w for b in g.index]
            ax.bar(xs, 100 * g["mean"], width=w * 0.92, color=colors[i % 4], label=label(s))
        counts = sub[sub.strategy == strategies[-1]].groupby("bucket").size()
        ax.set_xticks([0, 1, 2], [f"1 step\n(n={counts.get(1, 0)})", f"2 steps\n(n={counts.get(2, 0)})", f"3+ steps\n(n={counts.get(3, 0)})"])
        ax.set_title(data.DLABEL[d])
        ax.grid(axis="x", visible=False)
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("Execution accuracy (%)")
    fig.legend(*axes[0].get_legend_handles_labels(), fontsize=8.5, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return save(fig, f"steps_{data.model_label(model)}")


ERR_COLORS = {"no_answer": GREY, "execution_error": RED, "sign_error": MAGENTA, "scale_error": YELLOW,
              "rounding_near_miss": AQUA, "no_work_shown": "#7d7b74", "evidence_error": BLUE, "reasoning_error": ORANGE}
ERR_LABEL = {"no_answer": "no answer", "execution_error": "code failed", "sign_error": "sign", "scale_error": "scale/unit",
             "rounding_near_miss": "near miss (≤5%)", "no_work_shown": "no work shown", "evidence_error": "evidence (wrong/missing operand)",
             "reasoning_error": "reasoning (formula/arithmetic)"}


def errors(model):
    df = data.main_runs()
    # only datasets on which every hand-written strategy finished for this model, so bars are comparable
    dsets = [d for d in ["finqa", "tatqa"] if all(data.cell(d, model, s) is not None for s in data.MANUAL)]
    df = df[(df.model == model) & (~df.correct) & (df.dataset.isin(dsets))]
    order = [s for s in data.MAIN_ORDER if s in set(df.strategy)]
    if not order:
        return None
    tab = df.pivot_table(index="strategy", columns="error_category", values="uid", aggfunc="count", fill_value=0).reindex(order)
    cats = [c for c in ERR_COLORS if c in tab.columns]
    fig, ax = plt.subplots(figsize=(9.6, 3.4))
    y = np.arange(len(order))[::-1]
    left = np.zeros(len(order))
    for c in cats:
        v = tab[c].values
        ax.barh(y, v, left=left, color=ERR_COLORS[c], height=0.62, edgecolor="white", linewidth=1.2, label=ERR_LABEL[c])
        for yi, l, vi in zip(y, left, v):
            if vi >= 8:
                ax.text(l + vi / 2, yi, str(int(vi)), ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        left += v
    ax.set_yticks(y, [label(s) for s in order])
    ax.set_xlabel(f"Wrong answers ({' + '.join(data.DLABEL[d] for d in dsets)}, "
                  f"{sum(data.FULL_N[d] for d in dsets)} questions per strategy)")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=4, fontsize=8.3, loc="upper center", bbox_to_anchor=(0.45, -0.2))
    ax.set_title(f"{data.model_label(model)}: why answers were wrong (rule-based taxonomy)")
    fig.tight_layout()
    return save(fig, f"errors_{data.model_label(model)}")


def model_compare():
    ms = data.main_summary()
    if data.LARGE not in data.models():
        return None
    strategies = [s for s in data.MAIN_ORDER if s in set(ms[ms.model == data.LARGE].strategy)]
    dsets = [d for d in data.DATASETS if d in set(ms.dataset)]
    fig, axes = plt.subplots(1, len(dsets), figsize=(3.4 * len(dsets) + 1.2, 3.4), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, d in zip(axes, dsets):
        y = np.arange(len(strategies))[::-1]
        for yi, s in zip(y, strategies):
            a, b = data.cell(d, data.SMALL, s), data.cell(d, data.LARGE, s)
            if a is not None and b is not None:
                ax.plot([100 * a.accuracy, 100 * b.accuracy], [yi, yi], color=GRID, lw=2.5, zorder=1)
            for r, m in [(a, data.SMALL), (b, data.LARGE)]:
                if r is not None:
                    ax.scatter(100 * r.accuracy, yi, color=MODEL_COLOR[m], s=42, zorder=2, edgecolor="white", linewidth=1)
        ax.set_yticks(y, [label(s) for s in strategies])
        ax.set_xlim(0, 100)
        ax.grid(axis="y", visible=False)
        ax.set_title(data.DLABEL[d])
        ax.set_xlabel("Execution accuracy (%)")
    handles = [plt.Line2D([], [], marker="o", ls="", color=MODEL_COLOR[m], label=data.model_label(m)) for m in (data.SMALL, data.LARGE)]
    fig.tight_layout(rect=(0, 0, 1, 0.9))   # the legend sits above the panels, clear of every dot
    fig.legend(handles=handles, loc="upper center", ncol=2, fontsize=9, frameon=False, bbox_to_anchor=(0.5, 1.0))
    return save(fig, "model_compare")


def optimization():
    """Hand-written CoT prompts vs automatically optimized prompts, one panel per dataset. Only models
    with at least one tested optimized prompt are shown; every panel uses the same row order."""
    ms = data.main_summary()
    if ms[ms.strategy.str.contains(":")].empty:
        return None
    rows = []          # (model, strategy) in display order, shared by all panels
    for m in data.models():
        opt = list(data.optimized_strategies(m))
        if opt:
            rows += [(m, s) for s in ["cot_zs", "cot_fs"] + opt]
    if not rows:
        return None
    dsets = [d for d in data.DATASETS if any(data.cell(d, m, s) is not None for m, s in rows if ":" in s)]
    fig, axes = plt.subplots(1, len(dsets), figsize=(3.4 * len(dsets) + 2.2, 0.42 * len(rows) + 1.3), sharey=True)
    axes = np.atleast_1d(axes)
    y = -np.arange(len(rows))
    for ax, d in zip(axes, dsets):
        for yi, (m, s) in zip(y, rows):
            r = data.cell(d, m, s)
            if r is None:
                ax.text(2, yi, "not run yet", va="center", fontsize=7.5, color=INK2)
                continue
            ax.barh(yi, 100 * r.accuracy, color=BLUE if ":" not in s else ORANGE, height=0.62)
            ax.errorbar(100 * r.accuracy, yi, xerr=[[100 * (r.accuracy - r.ci_low)], [100 * (r.ci_high - r.accuracy)]],
                        fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
        ax.set_xlim(0, 100)
        ax.grid(axis="y", visible=False)
        ax.set_title(data.DLABEL[d])
        ax.set_xlabel("Execution accuracy (%)")
    axes[0].set_yticks(y, [f"{label(s)} · {data.model_label(m)}" for m, s in rows], fontsize=8.5)
    fig.tight_layout()
    return save(fig, "optimization")


def perturbation():
    p = data.perturbation()
    if p.empty:
        return None
    fig, ax = plt.subplots(figsize=(6.4, 0.5 * len(p) + 1.2))
    p = p.sort_values(["model", "strategy"], key=lambda c: c.map(data.strategy_rank) if c.name == "strategy" else c)
    y = np.arange(len(p))[::-1]
    for yi, r in zip(y, p.itertuples()):
        ax.plot([100 * r.original_accuracy, 100 * r.perturbed_accuracy], [yi, yi], color=GRID, lw=3, zorder=1)
        ax.scatter(100 * r.original_accuracy, yi, color=BLUE, s=48, zorder=2, label="original" if yi == y[0] else None)
        ax.scatter(100 * r.perturbed_accuracy, yi, color=ORANGE, s=48, zorder=2, label="numbers perturbed" if yi == y[0] else None)
    ax.set_yticks(y, [f"{label(r.strategy)} · {data.model_label(r.model)}" for r in p.itertuples()])
    ax.set_xlim(0, 100)
    ax.set_xlabel(f"Execution accuracy (%) on the same {int(p.n.iloc[0])} FinQA questions")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2, fontsize=8.5)
    ax.set_title("Memorization check: original vs. perturbed numbers")
    fig.tight_layout()
    return save(fig, "perturbation")


def ablations(model):
    panels = []
    fm = [(f, data.cell(d, model, "cot_fs", fmt=f)) for d in ["finqa", "tatqa"] for f in ["markdown", "json", "html", "text"]]
    if any(r is not None for f, r in fm if f != "markdown"):
        panels.append(("Table format (few-shot CoT)", [(f"{data.DLABEL[d]} · {f}", data.cell(d, model, "cot_fs", fmt=f))
                                                       for d in ["finqa", "tatqa"] for f in ["markdown", "json", "html", "text"]]))
    rt = [(d, data.cell(d, model, "pot_fs", context="retrieved")) for d in ["finqa", "tatqa"]]
    if any(r is not None for _, r in rt):
        panels.append(("Context (Program-of-Thought)", [(f"{data.DLABEL[d]} · {c}", data.cell(d, model, "pot_fs", context=cx))
                                                         for d in ["finqa", "tatqa"] for c, cx in [("full page", "full"), ("top-5 retrieved", "retrieved")]]))
    th = data.cell("finqa", model, "cot_zs", think=True)
    if th is not None:
        panels.append(("Thinking mode (zero-shot CoT, FinQA)", [("thinking off", data.cell("finqa", model, "cot_zs")), ("thinking on", th)]))
    if not panels:
        return None
    fig, axes = plt.subplots(1, len(panels), figsize=(3.6 * len(panels) + 1, 3.0))
    axes = np.atleast_1d(axes)
    for ax, (title, items) in zip(axes, panels):
        items = [(n, r) for n, r in items if r is not None]
        y = np.arange(len(items))[::-1]
        for yi, (n, r) in zip(y, items):
            ax.barh(yi, 100 * r.accuracy, color=BLUE, height=0.6)
            ax.text(100 * r.accuracy + 1.5, yi, f"{100 * r.accuracy:.0f}", va="center", fontsize=8.5)
        ax.set_yticks(y, [n for n, _ in items], fontsize=8.5)
        ax.set_xlim(0, 100)
        ax.grid(axis="y", visible=False)
        ax.set_title(title, fontsize=10.5)
    fig.tight_layout()
    return save(fig, f"ablations_{data.model_label(model)}")


PRODUCED = {}   # name -> path of every figure made in this build (stale files from older builds are ignored)


def all_figures():
    style()
    out = {"lit_gap": lit_gap(), "data_composition": data_composition(), "retrieval_recall": retrieval_recall(),
           "indian_types": indian_types(), "pareto_finqa": pareto("finqa"), "pareto_tatqa": pareto("tatqa"),
           "pareto_indian": pareto("indian"), "model_compare": model_compare(), "optimization": optimization(),
           "perturbation": perturbation()}
    for m in data.models():
        tag = data.model_label(m)
        out[f"main_bars_{tag}"] = main_bars(m)
        out[f"steps_{tag}"] = by_steps(m)
        out[f"errors_{tag}"] = errors(m)
        out[f"ablations_{tag}"] = ablations(m)
    PRODUCED.clear()
    PRODUCED.update({k: v for k, v in out.items() if v is not None})
    PRODUCED["_built"] = True
    return out
