"""Report figures. One visual style everywhere: a validated colour palette, hairline grids,
thin marks, and every series named by a legend or a direct label (never colour alone)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3de"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]   # categorical slots 1-4, in fixed order
MODEL_COLOR = {"ollama:qwen3:1.7b": SERIES[0], "ollama:qwen3:8b": SERIES[1]}
BLUES = LinearSegmentedColormap.from_list("blues", ["#cde2fb", "#6da7ec", "#256abf", "#0d366b"])

STRATEGY_ORDER = ["direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"]
LABELS = {"direct": "Direct", "cot_zs": "CoT zero-shot", "cot_fs": "CoT few-shot",
          "decomp_fs": "Decomposition", "pot_fs": "Program-of-Thought", "sc_cot": "Self-Consistency",
          "pot_sc": "PoT Self-Consistency", "vpsc": "VPSC (ours)"}
DATASET_LABEL = {"finqa": "FinQA", "tatqa": "TAT-QA", "indian": "Indian reports"}


def strategy_label(name):
    """Readable name, also for optimized strategies such as 'dspy:artifacts/dspy_mipro_...json'."""
    if name.startswith("dspy:"):
        return "DSPy MIPROv2" if "mipro" in name else "DSPy BootstrapFewShot"
    if name.startswith("textgrad:"):
        return "TextGrad"
    return LABELS.get(name, name)


def strategy_rank(name):
    if name in STRATEGY_ORDER:
        return STRATEGY_ORDER.index(name)
    return len(STRATEGY_ORDER) + (0 if "bootstrap" in name else 1 if "mipro" in name else 2)


def model_label(spec):
    """'ollama:qwen3:1.7b' -> 'Qwen3-1.7B'; other specs keep their model name."""
    name = spec.split(":", 1)[1]
    family, _, size = name.partition(":")
    return f"Qwen3-{size.upper()}" if family == "qwen3" and size else name


def style():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.linewidth": 0.8, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False,
        "axes.spines.right": False, "xtick.color": INK_2, "ytick.color": INK_2,
        "axes.labelcolor": INK_2, "text.color": INK, "font.size": 9, "axes.titlesize": 11,
        "axes.titleweight": "bold", "axes.titlelocation": "left", "legend.frameon": False,
        "font.family": "DejaVu Sans",
    })


def _save(fig, path):
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def accuracy_heatmap(summary, path):
    """Every strategy (rows) x dataset and model (columns); the cell shows accuracy in %."""
    cols = summary.drop_duplicates(["dataset", "model"]).sort_values(["dataset", "model"])
    col_keys = [(d, m) for d, m in zip(cols["dataset"], cols["model"])]
    rows = sorted(summary["strategy"].unique(), key=strategy_rank)
    grid = np.full((len(rows), len(col_keys)), np.nan)
    for i, s in enumerate(rows):
        for j, (d, m) in enumerate(col_keys):
            hit = summary[(summary["strategy"] == s) & (summary["dataset"] == d) & (summary["model"] == m)]
            if len(hit):
                grid[i, j] = 100 * hit["accuracy"].iloc[0]
    fig, ax = plt.subplots(figsize=(1.35 * len(col_keys) + 2.6, 0.42 * len(rows) + 1.4))
    ax.imshow(np.ma.masked_invalid(grid), cmap=BLUES, vmin=0, vmax=100, aspect="auto")
    ax.grid(False)
    for i in range(len(rows)):
        for j in range(len(col_keys)):
            if not np.isnan(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:.0f}", ha="center", va="center", fontsize=9,
                        color="white" if grid[i, j] > 55 else INK)
    ax.set_xticks(range(len(col_keys)))
    ax.set_xticklabels([f"{DATASET_LABEL[d]}\n{model_label(m)}" for d, m in col_keys])
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([strategy_label(s) for s in rows])
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title("Execution accuracy (%) by strategy, dataset and model")
    _save(fig, path)


def _label_points(ax, data, fontsize=7.5):
    """Label every point without overlaps. Strategies with identical results (e.g. VPSC and PoT-SC)
    share one label; each label takes the first vertical offset whose text box is free."""
    points = {}
    for _, r in data.iterrows():
        key = (r["model"], round(r["total_tokens"]), round(100 * r["accuracy"], 1))
        points.setdefault(key, []).append(strategy_label(r["strategy"]))
    px = ax.figure.dpi / 72                      # pixels per point
    height, char = fontsize * 1.25 * px, fontsize * 0.56 * px
    taken = []                                   # placed label boxes in pixels: (x0, y0, x1, y1)
    for (_, tokens, acc), labels in sorted(points.items(), key=lambda kv: (kv[0][1], -kv[0][2])):
        text = " = ".join(labels)
        x, y = ax.transData.transform((tokens, acc))
        for dy in (-3, 6, -12, 15, -21, 24, -30):
            box = (x + 6 * px, y + dy * px - height / 2, x + 6 * px + char * len(text), y + dy * px + height / 2)
            if not any(box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3] for b in taken):
                break
        taken.append(box)
        ax.annotate(text, (tokens, acc), xytext=(6, dy), textcoords="offset points", va="center",
                    fontsize=fontsize, color=INK_2)


def pareto(summary, dataset, path):
    """Accuracy against mean tokens per question, with each model's cost-efficiency frontier."""
    data = summary[summary["dataset"] == dataset]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for model, g in data.groupby("model"):
        color = MODEL_COLOR.get(model, SERIES[2])
        ax.errorbar(g["total_tokens"], 100 * g["accuracy"],
                    yerr=[100 * (g["accuracy"] - g["ci_low"]), 100 * (g["ci_high"] - g["accuracy"])],
                    fmt="o", ms=7, color=color, ecolor=color, elinewidth=1, alpha=0.9,
                    mec=SURFACE, mew=1.5, label=model_label(model))
        frontier, best = [], -1.0
        for _, r in g.sort_values("total_tokens").iterrows():
            if r["accuracy"] > best:
                frontier.append(r)
                best = r["accuracy"]
        ax.step([r["total_tokens"] for r in frontier], [100 * r["accuracy"] for r in frontier],
                where="post", color=color, lw=2, alpha=0.5)
    ax.set_xscale("log")
    ax.set_ylim(0, 100)
    _label_points(ax, data)
    ticks = [t for t in (500, 1000, 2000, 5000, 10000, 20000, 50000, 100000)
             if data["total_tokens"].min() / 1.5 <= t <= data["total_tokens"].max() * 1.5]
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set_ylim(0, 100)
    ax.set_xlabel("Mean tokens per question (log scale)")
    ax.set_ylabel("Execution accuracy (%)")
    ax.set_title(f"Accuracy vs cost - {DATASET_LABEL[dataset]} (line = cost-efficiency frontier)")
    ax.legend(title="Model", loc="upper left", title_fontsize=8)
    _save(fig, path)


def by_steps(df, dataset, path, strategies=("cot_fs", "pot_fs", "sc_cot", "vpsc")):
    """Accuracy for 1, 2 and 3+ reasoning steps; one panel per model."""
    data = df[df["dataset"] == dataset].copy()
    data["steps"] = data["n_steps"].clip(upper=3)
    models = sorted(m for m in data["model"].unique()
                    if data[(data["model"] == m) & data["strategy"].isin(strategies)].size)
    if not models:
        return
    fig, axes = plt.subplots(1, len(models), figsize=(max(7.2, 4.2 * len(models)), 3.6), sharey=True,
                             squeeze=False)
    for ax, model in zip(axes[0], models):
        lines = {}   # strategies with identical results are drawn once, with a combined label
        for color, s in zip(SERIES, strategies):
            g = data[(data["model"] == model) & (data["strategy"] == s)]
            if g.empty:
                continue
            acc = g.groupby("steps")["correct"].mean() * 100
            key = tuple(round(v, 1) for v in acc.values)
            if key in lines:
                lines[key][2].append(strategy_label(s))
            else:
                lines[key] = (acc, color, [strategy_label(s)])
        for acc, color, labels in lines.values():
            ax.plot(acc.index, acc.values, "-o", color=color, lw=2, ms=6, mec=SURFACE, mew=1.5,
                    label=" = ".join(labels))
        counts = data[data["model"] == model].drop_duplicates("uid")["steps"].value_counts()
        ax.set_xticks([1, 2, 3])
        ax.set_xticklabels([f"{name}\n(n={counts.get(k, 0)})"
                            for k, name in zip([1, 2, 3], ["1 step", "2 steps", "3+ steps"])])
        ax.set_ylim(0, 100)
        ax.set_title(model_label(model))
        ax.legend(loc="lower left", fontsize=7.5)   # each panel names its own lines
    axes[0][0].set_ylabel("Execution accuracy (%)")
    fig.suptitle(f"Accuracy by number of reasoning steps - {DATASET_LABEL[dataset]}",
                 x=0.01, ha="left", fontweight="bold", fontsize=11)
    fig.tight_layout()
    _save(fig, path)


def error_heatmap(df, categories, dataset, path):
    """Share of each strategy's wrong answers that falls in each error category."""
    wrong = df[(df["dataset"] == dataset) & (~df["correct"])]
    if wrong.empty:
        return
    keys = sorted(wrong.groupby(["model", "strategy"]).groups,
                  key=lambda k: (k[0], strategy_rank(k[1])))
    cats = [c for c in categories if c in set(wrong["error_category"])]
    grid = np.zeros((len(keys), len(cats)))
    for i, (m, s) in enumerate(keys):
        g = wrong[(wrong["model"] == m) & (wrong["strategy"] == s)]["error_category"].value_counts(normalize=True)
        grid[i] = [100 * g.get(c, 0) for c in cats]
    fig, ax = plt.subplots(figsize=(1.05 * len(cats) + 3.2, 0.36 * len(keys) + 1.5))
    ax.imshow(np.ma.masked_less(grid, 0.5), cmap=BLUES, vmin=0, vmax=100, aspect="auto")
    ax.grid(False)
    for i in range(len(keys)):
        for j in range(len(cats)):
            if grid[i, j] >= 1:
                ax.text(j, i, f"{grid[i, j]:.0f}", ha="center", va="center", fontsize=8,
                        color="white" if grid[i, j] > 55 else INK)
    ax.set_xticks(range(len(cats)))
    ax.set_xticklabels([c.replace("_", " ") for c in cats], rotation=30, ha="right")
    ax.set_yticks(range(len(keys)))
    ax.set_yticklabels([f"{model_label(m)} · {strategy_label(s)}" for m, s in keys])
    ax.tick_params(length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(f"Where the errors come from (% of wrong answers) - {DATASET_LABEL[dataset]}")
    _save(fig, path)


def perturbation_dumbbell(pert, path):
    """Accuracy on original vs numerically perturbed versions of the same questions."""
    if pert.empty:
        return
    pert = pert.sort_values(["model", "strategy"], key=lambda c: c.map(strategy_rank)
                            if c.name == "strategy" else c)
    labels = [f"{model_label(m)} · {strategy_label(s)}" for m, s in zip(pert["model"], pert["strategy"])]
    y = np.arange(len(pert))
    fig, ax = plt.subplots(figsize=(7, 0.45 * len(pert) + 1.4))
    ax.hlines(y, 100 * pert["perturbed_accuracy"], 100 * pert["original_accuracy"], color=GRID, lw=3)
    ax.scatter(100 * pert["original_accuracy"], y, s=60, color=SERIES[0], ec=SURFACE, lw=1.5,
               label="original numbers", zorder=3)
    ax.scatter(100 * pert["perturbed_accuracy"], y, s=60, color=SERIES[1], ec=SURFACE, lw=1.5,
               label="perturbed numbers", zorder=3)
    for yi, (_, r) in zip(y, pert.iterrows()):
        ax.annotate(f"p = {r['p_value']:.2f}", (100 * max(r["original_accuracy"], r["perturbed_accuracy"]), yi),
                    xytext=(8, -3), textcoords="offset points", fontsize=7.5, color=INK_2)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Execution accuracy (%) on the same FinQA questions")
    ax.set_title("Memorization test: changing the numbers")
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, path)


def ablation_panels(ablation, path):
    """Three small panels: table format, context (full vs retrieved) and thinking mode."""
    groups = [("Table format (CoT few-shot)", [c for c in ablation.columns if c.startswith("format")]),
              ("Context (Program-of-Thought)", [c for c in ablation.columns if c.startswith("PoT")]),
              ("Thinking mode (CoT zero-shot)", [c for c in ablation.columns if "thinking" in c])]
    series = [idx for idx in ablation.index if ablation.loc[idx].notna().sum() > 0]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, (title, cols) in zip(axes, groups):
        width = 0.8 / max(1, len(series))
        for k, idx in enumerate(series):
            for j, c in enumerate(cols):
                x = j + k * width
                value = ablation.loc[idx, c] if c in ablation else np.nan
                if np.isnan(value):
                    ax.text(x, 2, "not run", rotation=90, ha="center", va="bottom", fontsize=7,
                            color=INK_2)
                    continue
                ax.bar(x, 100 * value, width * 0.9, color=SERIES[k % 4],
                       label=f"{DATASET_LABEL[idx[0]]} · {model_label(idx[1])}" if j == 0 else None)
                ax.text(x, 100 * value + 1.5, f"{100 * value:.0f}", ha="center", fontsize=7,
                        color=INK_2)
        ax.set_xticks(np.arange(len(cols)) + width * (len(series) - 1) / 2)
        ax.set_xticklabels([c.split(": ")[-1].replace("zero-shot CoT, ", "").replace("PoT, ", "")
                            for c in cols], fontsize=8)
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, 100)
    axes[0].set_ylabel("Execution accuracy (%)")
    handles = {}   # one entry per named series; matplotlib names unlabelled bars "_container…"
    for ax in axes:
        for h, label in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(label, h)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.legend(list(handles.values()), list(handles.keys()), loc="upper center", fontsize=8,
               ncol=min(4, len(handles)), bbox_to_anchor=(0.5, 1.0), frameon=False)
    _save(fig, path)


def optimization_dots(summary, path):
    """Manual prompts vs automatically optimized prompts vs our method, per dataset."""
    keep = ["cot_zs", "cot_fs", "pot_fs", "vpsc"]
    data = summary[summary["strategy"].isin(keep) | summary["strategy"].str.contains(":")]
    if not data["strategy"].str.contains(":").any():
        return
    datasets = [d for d in ["finqa", "tatqa", "indian"] if d in set(data["dataset"])]
    fig, axes = plt.subplots(1, len(datasets), figsize=(4.4 * len(datasets), 3.8), sharey=True,
                             squeeze=False)
    order = sorted({strategy_label(s): strategy_rank(s) for s in data["strategy"]}.items(),
                   key=lambda kv: kv[1])
    ypos = {label: i for i, (label, _) in enumerate(order)}
    for ax, d in zip(axes[0], datasets):
        for model, g in data[data["dataset"] == d].groupby("model"):
            ax.scatter(100 * g["accuracy"], [ypos[strategy_label(s)] for s in g["strategy"]], s=55,
                       color=MODEL_COLOR.get(model, SERIES[2]), ec=SURFACE, lw=1.5,
                       label=model_label(model), zorder=3)
        ax.set_title(DATASET_LABEL[d], fontsize=10)
        ax.set_xlim(0, 100)
        ax.set_xlabel("Execution accuracy (%)")
    axes[0][0].set_yticks(range(len(order)))
    axes[0][0].set_yticklabels([label for label, _ in order])
    axes[0][-1].legend(fontsize=8, loc="lower right")
    fig.suptitle("Hand-written vs automatically optimized prompts", x=0.01, ha="left",
                 fontweight="bold", fontsize=11)
    fig.tight_layout()
    _save(fig, path)
