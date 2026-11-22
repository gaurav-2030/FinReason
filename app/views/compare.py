"""Compare: run several prompting strategies on the same question and context, in parallel."""
from concurrent.futures import ThreadPoolExecutor

import altair as alt
import pandas as pd
import streamlit as st

import core
import theme
from finreason.answers import score
from finreason.retrieval import build_context
from finreason.strategies import get_strategy
from views.common import choose_example, offline_notice, run_with_timer, settings


def run_all(example, chosen, model, fmt, mode, k):
    llm = core.get_llm(model)
    retriever = core.get_retriever() if mode == "retrieved" else None
    context, _ = build_context(example, fmt=fmt, mode=mode, retriever=retriever, k=k)

    def one(name):
        try:
            return get_strategy(name)(llm, example, context, fmt), ""
        except Exception as exc:   # one failing strategy must not hide the others
            return None, str(exc)
    with ThreadPoolExecutor(min(4, len(chosen))) as pool:
        return list(pool.map(one, chosen))


def render():
    theme.page_header("Compare · head to head", "Compare *strategies*",
                      "The same question and the same context, answered by several prompting strategies at once. "
                      "See which ones get it right, how much they agree, and what each answer costs.",
                      core.status_pills())
    with st.container(border=True):
        model, fmt, mode, k = settings("cmp")
        example = choose_example("cmp")
        if example is not None:
            theme.question(f"{example.uid} · {core.dataset_label(example.dataset)}",
                           example.question,
                           theme.chip(f"gold answer {core.fmt_number(example.gold)}", "gold")
                           if example.gold is not None else "")
        chosen = st.multiselect("Strategies", core.strategy_options(), default=["direct", "cot_fs", "pot_fs", "vpsc"],
                                format_func=core.short_label, key="cmp_strategies")
        clicked = st.button("Run all strategies", type="primary", disabled=example is None or not chosen,
                            icon=":material/compare_arrows:")
    if clicked and example is not None and chosen and not offline_notice():
        outputs, wall = run_with_timer(lambda: run_all(example, chosen, model, fmt, mode, k),
                                       f"Running {len(chosen)} strategies in parallel",
                                       f"{core.model_label(model)} · same question, same context")
        rows = []
        for name, (pred, err) in zip(chosen, outputs):
            if pred is None:
                rows.append({"strategy": core.short_label(name), "answer": "error", "result": f"⛔ {err[:80]}",
                             "calls": 0, "tokens": 0, "seconds": 0.0, "agreement": None})
                continue
            correct = None
            if example.gold is not None:
                correct = score(pred.answer, example.gold, example.question, example.scale)[0]
            rows.append({"strategy": core.short_label(name), "answer": core.fmt_number(pred.answer),
                         "result": {True: "✓ correct", False: "✕ wrong", None: "– no gold"}[correct],
                         "calls": pred.n_calls, "tokens": pred.prompt_tokens + pred.completion_tokens,
                         "seconds": round(pred.latency, 1), "agreement": pred.extra.get("agreement")})
        st.session_state["cmp_result"] = {"uid": example.uid, "question": example.question, "gold": example.gold,
                                          "rows": rows, "model": model, "wall": wall}
    result = st.session_state.get("cmp_result")
    if result is None:
        return
    table = pd.DataFrame(result["rows"])
    theme.section("Results", f"{core.model_label(result['model'])} · {result['uid']} · wall time "
                  f"{result['wall']:.1f}s", kicker="head to head")
    answered = table[~table["answer"].isin(["no answer", "error"])]
    tiles = [("Strategies run", str(len(table)), core.model_label(result["model"]), None)]
    if result["gold"] is not None:
        n_right = int(table["result"].str.startswith("✓").sum())
        tiles.append(("Correct", f"{n_right} / {len(table)}", f"gold answer {core.fmt_number(result['gold'])}",
                      theme.GOOD))
    if len(answered):
        top = answered["answer"].mode().iloc[0]
        tiles.append(("Consensus answer", top, f"{int((answered['answer'] == top).sum())} of {len(table)} agree",
                      None))
        cheapest = answered.sort_values("tokens").iloc[0]
        tiles.append(("Cheapest answer", cheapest["strategy"], f"{cheapest['tokens']:,} tokens", None, True))
    theme.kpis(tiles)
    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.dataframe(table.drop(columns="agreement"), width="stretch", hide_index=True,
                     column_config={"tokens": st.column_config.NumberColumn(format="%d"),
                                    "seconds": st.column_config.NumberColumn("model s", format="%.1f")})
    with right:
        chart = alt.Chart(table).mark_bar(cornerRadiusEnd=4, size=16, color=theme.SERIES[0]).encode(
            x=alt.X("tokens:Q", title="TOKENS FOR THIS QUESTION"),
            y=alt.Y("strategy:N", sort="-x", title=None, axis=alt.Axis(labelLimit=240, minExtent=175)),
            tooltip=["strategy", "answer", "result", alt.Tooltip("tokens:Q", format=","), "calls", "seconds"])
        st.altair_chart(theme.style_chart(chart, height=max(140, 42 * len(table))), width="stretch", theme=None)
        st.caption("Token cost of each strategy on this question (prompt + completion).")
