"""Robustness: the memorization (number-perturbation) test, the ablations (table format, retrieval,
thinking mode), retrieval recall, and how VPSC's grounding check behaved."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import theme

ABLATION_GROUPS = [
    ("Table serialization · few-shot CoT", ["format: markdown", "format: json", "format: html", "format: text"]),
    ("Evidence retrieval · Program-of-Thought", ["PoT, full page", "PoT, retrieved top-5"]),
    ("Thinking mode · zero-shot CoT", ["zero-shot CoT, no thinking", "zero-shot CoT, thinking"]),
]


def perturbation_chart(pert):
    df = pert.copy()
    df["Strategy"] = df["strategy"].map(core.strategy_label)
    df["Model"] = df["model"].map(core.model_label)
    df["label"] = df["Strategy"] + " · " + df["Model"]
    long = df.melt(id_vars=["label", "p_value", "n"], value_vars=["original_accuracy", "perturbed_accuracy"],
                   var_name="version", value_name="accuracy")
    long["version"] = long["version"].map({"original_accuracy": "original numbers",
                                           "perturbed_accuracy": "numbers changed"})
    long["acc"] = 100 * long["accuracy"]
    y = alt.Y("label:N", title=None, axis=alt.Axis(labelLimit=260, minExtent=215))
    line = alt.Chart(long).mark_line(color="#3a3d45", strokeWidth=2).encode(x="acc:Q", y=y, detail="label:N")
    dots = alt.Chart(long).mark_circle(size=120, opacity=1, stroke="#0b0c0f", strokeWidth=2).encode(
        x=alt.X("acc:Q", title="ACCURACY (%) ON THE SAME FINQA QUESTIONS", scale=alt.Scale(domain=[0, 100])), y=y,
        color=alt.Color("version:N", scale=alt.Scale(domain=["original numbers", "numbers changed"],
                                                     range=[theme.SERIES[0], theme.SERIES[1]]), title=None),
        tooltip=["label", "version", alt.Tooltip("acc:Q", title="accuracy %", format=".1f"),
                 alt.Tooltip("p_value:Q", title="McNemar p", format=".3f"), "n"])
    return theme.style_chart(line + dots, height=max(160, 46 * len(df)))


def render():
    theme.page_header("Robustness · does it really reason?", "Robustness and *ablations*",
                      "A memorization check that changes every number, three ablations of the context the model "
                      "sees, and a look inside VPSC's grounding check.", core.status_pills())

    theme.section("Memorization check: change the numbers", "Every operand of a FinQA question is changed by "
                  "10–30% in the table and text, and the gold answer is recomputed with FinQA's own program. A model "
                  "that memorized the benchmark would drop sharply.", kicker="perturbation test · GSM-Symbolic style")
    pert = core.results_csv("perturbation.csv")
    if pert is None or pert.empty:
        st.info("The perturbation runs have not been analysed yet.")
    else:
        c1, c2 = st.columns([1.15, 1], gap="large")
        with c1:
            st.altair_chart(perturbation_chart(pert), width="stretch", theme=None)
        with c2:
            table = pd.DataFrame({
                "Strategy": pert["strategy"].map(core.strategy_label), "Model": pert["model"].map(core.model_label),
                "Original": 100 * pert["original_accuracy"], "Changed": 100 * pert["perturbed_accuracy"],
                "McNemar p": pert["p_value"],
                "Verdict": pert["p_value"].map(lambda p: "significant drop" if p < .05 else "no significant drop")})
            st.dataframe(table, width="stretch", hide_index=True, column_config={
                "Original": st.column_config.NumberColumn(format="%.0f%%"),
                "Changed": st.column_config.NumberColumn(format="%.0f%%"),
                "McNemar p": st.column_config.NumberColumn(format="%.3f")})
            st.caption(f"{int(pert['n'].iloc[0])} of the 100 FinQA questions could be perturbed safely (every "
                       "operand written in the report, no years or percentages as operands).")

    theme.section("Ablations: what else changes accuracy?", "Each ablation changes one thing and keeps the "
                  "strategy, questions and scorer fixed.", kicker="table format · retrieval · thinking")
    abl = core.results_csv("ablations.csv")
    if abl is None or abl.empty:
        st.info("No ablation results yet.")
    else:
        long = abl.melt(id_vars=["dataset", "model"], var_name="variant", value_name="accuracy").dropna()
        long["Dataset"] = long["dataset"].map(core.DATASET_LABEL)
        long["Model"] = long["model"].map(core.model_label)
        long["acc"] = 100 * long["accuracy"]
        cols = st.columns(3, gap="large")
        for col, (title, variants) in zip(cols, ABLATION_GROUPS):
            sub = long[long["variant"].isin(variants) & long["dataset"].isin(["finqa", "tatqa"])].copy()
            # a variant is shown only for settings where every variant of the group was run
            complete = sub.groupby(["dataset", "model"])["variant"].transform("nunique") == len(variants)
            sub = sub[complete]
            with col:
                st.markdown(f"**{title}**")
                if sub.empty:
                    st.caption("Pending.")
                    continue
                sub["Setting"] = sub["Dataset"] + " · " + sub["Model"]
                sub["Variant"] = sub["variant"].str.replace("format: ", "").str.replace("PoT, ", "").str.replace(
                    "zero-shot CoT, ", "")
                chart = alt.Chart(sub).mark_bar(cornerRadiusEnd=3, size=11).encode(
                    x=alt.X("acc:Q", title="ACCURACY (%)", scale=alt.Scale(domain=[0, 100])),
                    y=alt.Y("Variant:N", title=None, sort=[v.split(": ")[-1].split(", ")[-1] for v in variants],
                            axis=alt.Axis(labelLimit=200, minExtent=110)),
                    yOffset=alt.YOffset("Setting:N"),
                    color=alt.Color("Setting:N", title=None, legend=alt.Legend(orient="bottom", columns=1),
                                    scale=alt.Scale(range=theme.SERIES)),
                    tooltip=["Setting", "Variant", alt.Tooltip("acc:Q", title="accuracy %", format=".1f")])
                st.altair_chart(theme.style_chart(chart, height=max(150, 36 * len(variants) * sub["Setting"].nunique() ** .7)),
                                width="stretch", theme=None)
        summary = core.summary()
        think = summary[(summary["think"]) & (summary["strategy"] == "cot_zs")]
        plain = summary[(~summary["think"]) & (summary["strategy"] == "cot_zs") & (summary["fmt"] == "markdown")
                        & (summary["context"] == "full") & (~summary["perturbed"])]
        if len(think):
            t = think.iloc[0]
            p = plain[(plain["dataset"] == t["dataset"]) & (plain["model"] == t["model"])]
            if len(p):
                p = p.iloc[0]
                st.caption(f"Thinking mode ({core.model_label(t['model'])}, {core.DATASET_LABEL[t['dataset']]}): "
                           f"{core.pct(p['accuracy'])} → {core.pct(t['accuracy'])} accuracy at "
                           f"{t['total_tokens'] / p['total_tokens']:.1f}× the tokens and "
                           f"{t['latency_s'] / p['latency_s']:.0f}× the time per question.")

    theme.section("Retrieval recall", "How often hybrid retrieval puts the gold evidence rows/sentences in the top k "
                  "(full FinQA and TAT-QA test sets, no LLM involved).", kicker="BM25 · MiniLM + FAISS · RRF")
    rec = core.results_csv("retrieval_recall.csv")
    if rec is not None:
        long = rec.melt(id_vars=["dataset", "method", "n"], var_name="k", value_name="recall")
        long["k"] = long["k"].str.replace("recall@", "").astype(int)
        long["Dataset"] = long["dataset"].map(core.DATASET_LABEL)
        long["Method"] = long["method"].map({"bm25": "BM25", "dense": "Dense (MiniLM)", "hybrid": "Hybrid (RRF)"})
        chart = alt.Chart(long).mark_line(point=alt.OverlayMarkDef(size=60, filled=True), strokeWidth=2).encode(
            x=alt.X("k:O", title="K (EVIDENCE UNITS KEPT)", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("recall:Q", title="RECALL OF GOLD EVIDENCE", scale=alt.Scale(domain=[0, 1]),
                    axis=alt.Axis(format="%")),
            color=alt.Color("Method:N", scale=alt.Scale(domain=["BM25", "Dense (MiniLM)", "Hybrid (RRF)"],
                                                        range=theme.SERIES), title=None),
            tooltip=["Dataset", "Method", "k", alt.Tooltip("recall:Q", format=".1%")]
        ).properties(width=360, height=230).facet(column=alt.Column("Dataset:N", title=None))
        st.altair_chart(theme.style_chart(chart), width="content", theme=None)

    theme.section("Inside VPSC: the grounding check", "A program is rejected when it types a number that is not in "
                  "the report (after allowing constants, years and ×100 / ×1000 rescaling). A question is flagged "
                  "when at least one of its programs was rejected.", kicker="our method")
    vpsc = core.results_csv("vpsc.csv")
    if vpsc is None or vpsc.empty:
        st.info("No VPSC runs analysed yet.")
    else:
        table = pd.DataFrame({
            "Dataset": vpsc["dataset"].map(core.DATASET_LABEL), "Model": vpsc["model"].map(core.model_label),
            "VPSC": 100 * vpsc["vpsc_accuracy"], "PoT-SC (no check)": 100 * vpsc["pot_sc_accuracy"],
            "Programs rejected": vpsc["ungrounded"].astype(str) + " / " + vpsc["executed"].astype(str),
            "Flagged questions": vpsc["flagged_questions"], "…of which wrong": vpsc["flagged_wrong"],
            "Answers changed vs PoT-SC": vpsc["answers_changed"], "Mean agreement": 100 * vpsc["agreement"]})
        st.dataframe(table, width="stretch", hide_index=True, column_config={
            "VPSC": st.column_config.NumberColumn(format="%.0f%%"),
            "PoT-SC (no check)": st.column_config.NumberColumn(format="%.0f%%"),
            "Mean agreement": st.column_config.NumberColumn(format="%.0f%%")})
        flagged, wrong = int(vpsc["flagged_questions"].sum()), int(vpsc["flagged_wrong"].sum())
        if flagged:
            st.caption(f"Across all runs the check flagged {flagged} questions and {wrong} of them were answered "
                       f"wrongly ({core.pct(wrong / flagged)} precision) — a reliable warning flag even when it does "
                       "not change the majority vote.")
