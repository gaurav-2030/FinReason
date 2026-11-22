"""Error explorer: every wrong answer of the main comparison, labelled by the rule-based taxonomy,
with the model's reasoning and code side by side."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import theme
from finreason.errors import CATEGORIES

MEANING = {
    "no_answer": "No parsable answer in the output.",
    "execution_error": "The program failed even after one repair attempt.",
    "sign_error": "Right magnitude, wrong sign (increase vs decrease).",
    "scale_error": "Off by a power of ten: thousand, lakh, million, crore or billion.",
    "rounding_near_miss": "Within 5% of the gold value but outside the 0.5% tolerance.",
    "no_work_shown": "Wrong, and no intermediate numbers to diagnose.",
    "evidence_error": "At least one gold operand never appears in the work: wrong or missing number.",
    "reasoning_error": "All gold operands appear, but the formula or arithmetic is wrong.",
}


def nice(category):
    return str(category).replace("_", " ")


def render():
    theme.page_header("Error explorer · failure forensics", "Why answers are *wrong*",
                      "Every wrong answer is assigned exactly one category by a rule-based taxonomy "
                      "(finreason/errors.py). Pick a run, filter by category and open any case.", core.status_pills())
    df = core.main_records()
    if df.empty:
        st.warning("No runs yet.")
        return
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns(4)
        dataset = c1.selectbox("Dataset", [d for d in core.DATASETS if d in set(df["dataset"])],
                               format_func=core.dataset_label, key="err_dataset")
        sub = df[df["dataset"] == dataset]
        model = c2.selectbox("Model", [m for m in core.MODELS if m in set(sub["model"])], format_func=core.model_name,
                             key="err_model")
        sub = sub[sub["model"] == model]
        strategies = sorted(sub["strategy"].unique(), key=core.strategy_rank)
        strategy = c3.selectbox("Strategy", strategies, format_func=core.short_label, key="err_strategy",
                                index=strategies.index("pot_fs") if "pot_fs" in strategies else 0)
        run = sub[sub["strategy"] == strategy]
        wrong = run[~run["correct"]]
        present = [c for c in CATEGORIES if c in set(wrong["error_category"].dropna())]
        category = c4.selectbox("Error category", ["all"] + present, format_func=lambda c: "all categories"
                                if c == "all" else nice(c), key="err_category")
    counts = wrong["error_category"].value_counts()
    theme.kpis([("Accuracy", core.pct(run["correct"].mean()), f"{len(run)} questions", theme.GOOD),
                ("Wrong answers", str(len(wrong)), core.short_label(strategy), theme.BAD),
                ("Most common error", nice(counts.index[0]) if len(counts) else "–",
                 f"{int(counts.iloc[0])} of {len(wrong)} wrong answers" if len(counts) else "", theme.WARN, True)])

    left, right = st.columns([1.15, 1], gap="large")
    with left:
        theme.section("Outcome breakdown", kicker="this run")
        frame = pd.DataFrame({"category": [nice(c) for c in CATEGORIES],
                              "questions": [int(counts.get(c, 0)) for c in CATEGORIES]})
        chart = alt.Chart(frame).mark_bar(cornerRadiusEnd=4, size=14, color=theme.SERIES[1]).encode(
            x=alt.X("questions:Q", title="WRONG ANSWERS", axis=alt.Axis(tickMinStep=1)),
            y=alt.Y("category:N", sort=[nice(c) for c in CATEGORIES], title=None,
                    axis=alt.Axis(labelLimit=200, minExtent=135)),
            tooltip=["category", "questions"])
        st.altair_chart(theme.style_chart(chart, height=260), width="stretch", theme=None)
    with right:
        theme.section("What the categories mean", kicker="taxonomy · checked in this order")
        theme.html_table(["Category", "Rule"], [[f"<b>{theme.esc(nice(c))}</b>", theme.esc(MEANING[c])]
                                                for c in CATEGORIES])

    theme.section("Across strategies", f"Wrong answers per category, {core.DATASET_LABEL[dataset]} · "
                  f"{core.model_label(model)}", kicker="where each strategy fails")
    allwrong = sub[~sub["correct"]]
    pivot = allwrong.pivot_table(index="strategy", columns="error_category", values="uid", aggfunc="count",
                                 fill_value=0).reindex(columns=CATEGORIES, fill_value=0)
    pivot = pivot.loc[sorted(pivot.index, key=core.strategy_rank)]
    pivot.index = [core.short_label(s) for s in pivot.index]
    pivot.columns = [nice(c) for c in pivot.columns]
    st.dataframe(pivot, width="stretch", column_config={c: st.column_config.ProgressColumn(
        c, format="%d", min_value=0, max_value=int(pivot.values.max()) or 1, width="small") for c in pivot.columns})

    if category != "all":
        wrong = wrong[wrong["error_category"] == category]
    theme.section(f"{len(wrong)} wrong answers", "Select a row to open the case.", kicker="cases")
    if wrong.empty:
        st.info("No wrong answers in this selection.")
        return
    table = pd.DataFrame({"uid": wrong["uid"].values, "question": wrong["question"].values,
                          "gold": [core.fmt_number(g) for g in wrong["gold"]],
                          "answer": [core.fmt_number(None if pd.isna(a) else a) if not isinstance(a, str) else a
                                     for a in wrong["answer"]],
                          "category": [nice(c) for c in wrong["error_category"]]})
    pick = st.dataframe(table, width="stretch", hide_index=True, on_select="rerun", selection_mode="single-row",
                        key=f"err_table_{dataset}_{model}_{strategy}_{category}")
    rows = pick.selection.rows if pick and pick.selection else []
    record = wrong.iloc[rows[0] if rows else 0]
    answer = record["answer"]
    answer = None if not isinstance(answer, str) and pd.isna(answer) else answer
    theme.question(record["uid"], record["question"],
                   theme.chip(f"gold {core.fmt_number(record['gold'])}", "good", "✓")
                   + theme.chip(f"answer {core.fmt_number(answer)}", "bad", "✕")
                   + theme.chip(nice(record["error_category"]), "warn"))
    code = record.get("code")
    if isinstance(code, str) and code.strip():
        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.caption("Program")
            st.code(code, language="python")
            if isinstance(record.get("sandbox_error"), str) and record["sandbox_error"]:
                st.error(f"Sandbox: {record['sandbox_error']}")
        with c2:
            st.caption("Model output")
            st.code(record["output"] or "", language=None, wrap_lines=True)
    else:
        st.caption("Model output")
        st.code(record["output"] or "", language=None, wrap_lines=True)
