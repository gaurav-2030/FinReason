"""Results: accuracy with 95% bootstrap CIs, accuracy vs cost, small vs large model, accuracy by
reasoning steps and evidence source, McNemar tests and every metric of the main comparison."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import theme

MODEL_SCALE = alt.Scale(domain=list(theme.MODEL_COLORS), range=list(theme.MODEL_COLORS.values()))


def prepared(main, dataset, models):
    view = main[(main["dataset"] == dataset) & main["model"].isin(models)].copy()
    view["Strategy"] = view["strategy"].map(core.strategy_label)
    view["Model"] = view["model"].map(core.model_label)
    view["rank"] = view["strategy"].map(core.strategy_rank)
    for col in ["accuracy", "ci_low", "ci_high"]:
        view[col + "_pct"] = 100 * view[col]
    return view.sort_values(["rank", "Model"])


def accuracy_chart(view):
    order = list(dict.fromkeys(view["Strategy"]))
    base = alt.Chart(view).encode(
        y=alt.Y("Strategy:N", sort=order, title=None, axis=alt.Axis(labelLimit=220, minExtent=150)),
        yOffset=alt.YOffset("Model:N"),
        color=alt.Color("Model:N", scale=MODEL_SCALE, title="Model"))
    rules = base.mark_rule(strokeWidth=2, strokeCap="round", opacity=.55).encode(
        x=alt.X("ci_low_pct:Q", title="EXECUTION ACCURACY (%) · 95% BOOTSTRAP CI", scale=alt.Scale(domain=[0, 100])),
        x2="ci_high_pct:Q")
    dots = base.mark_circle(size=110, opacity=1, stroke="#0b0c0f", strokeWidth=2).encode(
        x="accuracy_pct:Q",
        tooltip=["Strategy", "Model", alt.Tooltip("accuracy_pct:Q", title="accuracy %", format=".1f"),
                 alt.Tooltip("ci_low_pct:Q", title="CI low %", format=".1f"),
                 alt.Tooltip("ci_high_pct:Q", title="CI high %", format=".1f"), alt.Tooltip("n:Q", title="questions")])
    labels = base.mark_text(align="left", dx=9, fontSize=10.5).encode(
        x="ci_high_pct:Q", text=alt.Text("accuracy_pct:Q", format=".0f"), color=alt.value(theme.INK_2))
    height = max(240, 30 * len(order) * max(1, view["Model"].nunique()) ** .6)
    return theme.style_chart(rules + dots + labels, height=height)


def pareto_points(view):
    """Strategies no other strategy beats on both accuracy and tokens (per model)."""
    keep = []
    for _, g in view.groupby("Model"):
        for i, r in g.iterrows():
            dominated = ((g["accuracy"] >= r["accuracy"]) & (g["total_tokens"] <= r["total_tokens"])
                         & ((g["accuracy"] > r["accuracy"]) | (g["total_tokens"] < r["total_tokens"]))).any()
            if not dominated:
                keep.append(i)
    return view.loc[keep].sort_values("total_tokens")


def cost_chart(view):
    frontier = pareto_points(view)
    x = alt.X("total_tokens:Q", scale=alt.Scale(type="log", nice=False), title="MEAN TOKENS PER QUESTION (LOG SCALE)")
    y = alt.Y("accuracy_pct:Q", title="EXECUTION ACCURACY (%)", scale=alt.Scale(domain=[0, 100]))
    color = alt.Color("Model:N", scale=MODEL_SCALE, title="Model")
    line = alt.Chart(frontier).mark_line(strokeDash=[4, 4], strokeWidth=1.5, opacity=.7).encode(
        x=x, y=y, color=color, order="total_tokens:Q")
    points = alt.Chart(view).mark_circle(size=120, opacity=.95, stroke="#0b0c0f", strokeWidth=2).encode(
        x=x, y=y, color=color,
        tooltip=["Strategy", "Model", alt.Tooltip("accuracy_pct:Q", title="accuracy %", format=".1f"),
                 alt.Tooltip("total_tokens:Q", title="tokens / question", format=",.0f"),
                 alt.Tooltip("tokens_per_correct:Q", title="tokens / correct answer", format=",.0f"),
                 alt.Tooltip("latency_s:Q", title="seconds / question", format=".1f")])
    labels = alt.Chart(frontier).mark_text(align="left", dx=9, dy=-9, fontSize=10.5, color=theme.INK_2).encode(
        x=x, y=y, text="Strategy:N")
    return theme.style_chart(line + points + labels, height=380)


def model_chart(main, dataset):
    both = main[main["dataset"] == dataset].copy()
    both = both[~both["strategy"].str.contains(":")]   # optimized prompts are model-specific
    pivot = both.pivot_table(index="strategy", columns="model", values="accuracy")
    if core.SMALL not in pivot or core.LARGE not in pivot:
        return None
    pivot = pivot.dropna()
    if pivot.empty:
        return None
    long = pivot.reset_index().melt(id_vars="strategy", var_name="model", value_name="accuracy")
    long["Strategy"] = long["strategy"].map(core.strategy_label)
    long["Model"] = long["model"].map(core.model_label)
    long["acc"] = 100 * long["accuracy"]
    order = sorted(pivot.index, key=core.strategy_rank)
    order = [core.strategy_label(s) for s in order]
    y = alt.Y("Strategy:N", sort=order, title=None, axis=alt.Axis(labelLimit=220, minExtent=150))
    rule = alt.Chart(long).mark_line(color="#3a3d45", strokeWidth=2).encode(x="acc:Q", y=y, detail="Strategy:N")
    dots = alt.Chart(long).mark_circle(size=120, opacity=1, stroke="#0b0c0f", strokeWidth=2).encode(
        x=alt.X("acc:Q", title="EXECUTION ACCURACY (%)", scale=alt.Scale(domain=[0, 100])), y=y,
        color=alt.Color("Model:N", scale=MODEL_SCALE, title="Model"),
        tooltip=["Strategy", "Model", alt.Tooltip("acc:Q", title="accuracy %", format=".1f")])
    return theme.style_chart(rule + dots, height=max(220, 34 * len(order)))


def breakdown(name, dataset, models):
    df = core.results_csv(name)
    if df is None:
        return None
    df = df[(df["dataset"] == dataset) & df["model"].isin(models)].copy()
    if df.empty:
        return None
    df["rank"] = df["strategy"].map(core.strategy_rank)
    df = df.sort_values(["model", "rank"])
    df.insert(0, "Strategy", df["strategy"].map(core.strategy_label))
    df.insert(1, "Model", df["model"].map(core.model_label))
    value_cols = [c for c in df.columns if c not in ("dataset", "model", "strategy", "rank", "Strategy", "Model")]
    df[value_cols] = 100 * df[value_cols]
    return df[["Strategy", "Model"] + value_cols], value_cols


def render():
    theme.page_header("Results · re-scored from the saved runs", "Experiment *results*",
                      "Every number below is recomputed from results/runs/*.jsonl by scripts/analyze.py with one "
                      "scorer: correct when within 0.5% of the gold answer. Bars show 95% bootstrap confidence "
                      "intervals; significance is a paired McNemar test against few-shot CoT, Holm-corrected.",
                      core.status_pills())
    main = core.main_summary()
    if main is None or main.empty:
        st.warning("No results yet. Run `bash scripts/run_all.sh main` and then `python scripts/analyze.py`.")
        return
    datasets = [d for d in core.DATASETS if d in set(main["dataset"])]
    models = [m for m in core.MODELS if m in set(main["model"])]
    c1, c2, c3 = st.columns([1.4, 1.2, .8], vertical_alignment="bottom")
    dataset = c1.segmented_control("Dataset", datasets, default=datasets[0], required=True,
                                   format_func=core.dataset_label, key="res_dataset")
    chosen = c2.pills("Models", models, default=models, selection_mode="multi", format_func=core.model_name,
                      key="res_models") or models
    if c3.button("Refresh results", icon=":material/refresh:", width="stretch",
                 help="Re-score every saved answer and redraw the figures (takes about a minute)."):
        with st.spinner("Re-scoring every answer and redrawing the figures…"):
            core.refresh_results()
        st.rerun()
    running = [r for r in core.partial_runs() if r[0] == dataset and r[1] in chosen]
    if running:
        st.caption("Incomplete runs (left out until complete): " + ", ".join(
            f"{core.short_label(s)} · {core.model_name(m)} ({done}/{total})" for _, m, s, done, total in running))
    view = prepared(main, dataset, chosen)
    if view.empty:
        st.info("No runs for this selection yet.")
        return

    best = view.sort_values("accuracy", ascending=False).iloc[0]
    tiles = [("Best strategy", best["Strategy"], f"{core.pct(best['accuracy'])} · {best['Model']}", None, True)]
    for model in chosen:
        base = core.cell(main[main["dataset"] == dataset], dataset, model, "cot_fs")
        ours = core.cell(main[main["dataset"] == dataset], dataset, model, "vpsc")
        if base is not None and ours is not None:
            tiles.append((f"VPSC · {core.model_label(model)}", core.pct(ours["accuracy"]),
                          f"{100 * (ours['accuracy'] - base['accuracy']):+.0f} pts vs CoT few-shot", theme.SERIES[2]))
    direct = view[view["strategy"] == "direct"]
    if len(direct):
        tiles.append(("Direct answer (no reasoning)", core.pct(direct["accuracy"].max()),
                      "best model · answer line only", theme.BAD))
    summary = core.summary()
    tiles.append(("Answers scored", f"{int(summary['n'].sum()):,}", f"{int((summary['n'] * summary['calls']).sum()):,} "
                  "local model calls", None))
    theme.kpis(tiles[:4])

    tabs = st.tabs(["Accuracy", "Accuracy vs cost", "1.7B vs 8B", "By steps & evidence", "Significance",
                    "All metrics", "Report figures"])
    with tabs[0]:
        st.altair_chart(accuracy_chart(view), width="stretch", theme=None)
        st.caption("Dot = accuracy, line = 95% bootstrap confidence interval (2,000 resamples). "
                   f"{core.DATASET_LABEL[dataset]}: {core.FULL_N[dataset]} questions per run.")
    with tabs[1]:
        st.altair_chart(cost_chart(view), width="stretch", theme=None)
        st.caption("Up and to the left is better. The dashed line joins the strategies no other strategy beats on "
                   "both accuracy and tokens (the Pareto frontier); only those are labelled — hover for the rest.")
    with tabs[2]:
        chart = model_chart(main, dataset)
        if chart is None:
            st.info("The Qwen3-8B runs for this dataset are not complete yet (pending). They appear here "
                    "automatically once they are run and the results are refreshed.")
        else:
            theme.legend([(k, v) for k, v in theme.MODEL_COLORS.items()])
            st.altair_chart(chart, width="stretch", theme=None)
            st.caption("Same questions, same prompts: only the model size changes.")
    with tabs[3]:
        for name, title, note in [("accuracy_by_steps.csv", "Accuracy by number of reasoning steps",
                                   "Steps = arithmetic operations in the gold program (FinQA) or derivation."),
                                  ("accuracy_by_evidence.csv", "Accuracy by evidence source",
                                   "Where the gold evidence is: table only, text only, or both.")]:
            theme.section(title, note)
            out = breakdown(name, dataset, chosen)
            if out is None:
                st.info("Not available yet.")
                continue
            frame, cols = out
            st.dataframe(frame, width="stretch", hide_index=True, column_config={
                c: st.column_config.ProgressColumn(c, format="%.0f%%", min_value=0, max_value=100) for c in cols})
    with tabs[4]:
        sig = core.results_csv("significance.csv")
        if sig is None or sig.empty:
            st.info("No significance tests yet.")
        else:
            sig = sig[(sig["dataset"] == dataset) & (~sig["perturbed"]) & (sig["fmt"] == "markdown")
                      & (sig["context"] == "full") & (~sig["think"]) & sig["model"].isin(chosen)].copy()
            sig["rank"] = sig["strategy"].map(core.strategy_rank)
            sig = sig.sort_values(["model", "rank"])
            sig["significant"] = sig["p_holm"].map(lambda p: "✓ p_holm < 0.05" if p < .05 else "–")
            table = pd.DataFrame({
                "Model": sig["model"].map(core.model_label), "Strategy": sig["strategy"].map(core.strategy_label),
                "n": sig["n"], "Accuracy": 100 * sig["accuracy"], "CoT few-shot": 100 * sig["baseline"],
                "Only this right": sig["wins"], "Only CoT FS right": sig["losses"], "p": sig["p_value"],
                "p (Holm)": sig["p_holm"], "Significant": sig["significant"]})
            st.dataframe(table, width="stretch", hide_index=True, column_config={
                "Accuracy": st.column_config.NumberColumn(format="%.0f%%"),
                "CoT few-shot": st.column_config.NumberColumn(format="%.0f%%"),
                "p": st.column_config.NumberColumn(format="%.3f"),
                "p (Holm)": st.column_config.NumberColumn(format="%.3f")})
            st.caption("Exact McNemar test on the discordant pairs (questions only one of the two systems got "
                       "right); p-values Holm-adjusted within each model and dataset.")
    with tabs[5]:
        cols = {"Strategy": view["Strategy"], "Model": view["Model"], "n": view["n"],
                "Accuracy": 100 * view["accuracy"], "CI low": 100 * view["ci_low"], "CI high": 100 * view["ci_high"],
                "Acc. @1%": 100 * view["accuracy_1pct"], "Exact match": 100 * view["exact_match"],
                "F1": 100 * view["f1"], "Format fail": 100 * view["format_failure"],
                "Code fail": 100 * view["code_failure"], "Calls": view["calls"],
                "Tokens / Q": view["total_tokens"], "Tokens / correct": view["tokens_per_correct"],
                "Seconds / Q": view["latency_s"]}
        percent = st.column_config.NumberColumn(format="%.0f%%")
        st.dataframe(pd.DataFrame(cols), width="stretch", hide_index=True, column_config={
            **{c: percent for c in ["Accuracy", "CI low", "CI high", "Acc. @1%", "Exact match", "F1",
                                    "Format fail", "Code fail"]},
            "Calls": st.column_config.NumberColumn(format="%.1f"),
            "Tokens / Q": st.column_config.NumberColumn(format="%d"),
            "Tokens / correct": st.column_config.NumberColumn(format="%d"),
            "Seconds / Q": st.column_config.NumberColumn(format="%.1f")})
        st.caption("Accuracy @1% uses a 1% tolerance; exact match rounds both values to 2 decimals. Format "
                   "failure = no 'Answer:' line (last number used instead); code failure = the program still "
                   "failed after one repair. Seconds are model time on an Apple M4 (24 GB).")
        st.download_button("Download summary.csv", (core.RESULTS / "summary.csv").read_bytes(), "summary.csv",
                           icon=":material/download:")
    with tabs[6]:
        figs = core.figures()
        if not figs:
            st.info("No figures yet — run scripts/analyze.py.")
        for start in range(0, len(figs), 2):
            cols = st.columns(2, gap="large")
            for col, path in zip(cols, figs[start:start + 2]):
                col.image(str(path), caption=path.stem.replace("_", " "), width="stretch")
