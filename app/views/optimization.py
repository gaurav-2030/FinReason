"""Optimization: what DSPy (BootstrapFewShot, MIPROv2) and TextGrad changed in the prompt, what it
cost once, and whether it beats the hand-written prompts on the test sets."""
import altair as alt
import pandas as pd
import streamlit as st

import core
import theme

OPTIMIZERS = [("dspy_bootstrap", "DSPy BootstrapFewShot", "few-shot demonstrations",
               "Runs the CoT program on 50 FinQA train questions and keeps up to 3 traces our scorer marks "
               "correct as demonstrations."),
              ("dspy_mipro", "DSPy MIPROv2", "instruction + demonstrations",
               "An LLM proposes candidate instructions; Bayesian search over (instruction, demo set) pairs, "
               "scored on 40 FinQA dev questions."),
              ("textgrad", "TextGrad", "system prompt",
               "The 8B model critiques wrong answers (textual gradients) and rewrites the system prompt; a "
               "rewrite is kept only if accuracy on 40 FinQA dev questions does not drop.")]


def slug(model):
    return model.replace(":", "-")


def artifact_for(prefix, model):
    return core.artifacts().get(f"{prefix}_{slug(model)}")


def strategy_name(prefix, model):
    if prefix == "textgrad":
        return f"textgrad:artifacts/textgrad_{slug(model)}.json"
    return f"dspy:artifacts/{prefix}_{slug(model)}.json"


def cost_of(prefix, meta):
    if prefix == "textgrad":
        usage = meta["usage"]
        return (meta["seconds"] / 60, usage["task_calls"] + usage["optimizer_calls"],
                usage["prompt_tokens"] + usage["completion_tokens"])
    return (meta["compile_seconds"] / 60, meta["compile_lm_calls"],
            meta["compile_prompt_tokens"] + meta["compile_completion_tokens"])


def test_accuracy_chart(main, model):
    rows = []
    names = [("cot_zs", "CoT zero-shot (hand-written)"), ("cot_fs", "CoT few-shot (hand-written)")]
    names += [(strategy_name(p, model), label) for p, label, _, _ in OPTIMIZERS]
    for dataset in core.DATASETS:
        for strategy, label in names:
            row = core.cell(main[main["dataset"] == dataset], dataset, model, strategy)
            if core.complete(row, dataset):
                rows.append({"Dataset": core.DATASET_LABEL[dataset], "Prompt": label, "acc": 100 * row["accuracy"],
                             "lo": 100 * row["ci_low"], "hi": 100 * row["ci_high"],
                             "kind": "hand-written" if "hand" in label else "optimized"})
    if not any(r["kind"] == "optimized" for r in rows):
        return None
    df = pd.DataFrame(rows)
    order = [label for _, label in names]
    y = alt.Y("Prompt:N", sort=order, title=None, axis=alt.Axis(labelLimit=230, minExtent=200))
    colour = alt.Color("kind:N", scale=alt.Scale(domain=["hand-written", "optimized"],
                                                 range=[theme.SERIES[0], theme.SERIES[2]]), title=None)
    bars = alt.Chart(df).mark_bar(cornerRadiusEnd=4, size=14).encode(
        x=alt.X("acc:Q", title="TEST ACCURACY (%)", scale=alt.Scale(domain=[0, 100])), y=y, color=colour,
        tooltip=["Dataset", "Prompt", alt.Tooltip("acc:Q", title="accuracy %", format=".1f"),
                 alt.Tooltip("lo:Q", title="CI low %", format=".1f"), alt.Tooltip("hi:Q", title="CI high %", format=".1f")])
    ci = alt.Chart(df).mark_rule(color=theme.INK_2, opacity=.6).encode(x="lo:Q", x2="hi:Q", y=y)
    text = alt.Chart(df).mark_text(align="left", dx=6, fontSize=10.5, color=theme.INK_2).encode(
        x="hi:Q", y=y, text=alt.Text("acc:Q", format=".0f"))
    chart = alt.layer(bars, ci, text).properties(height=34 * len(order), width=230).facet(
        column=alt.Column("Dataset:N", sort=[core.DATASET_LABEL[d] for d in core.DATASETS], title=None))
    return theme.style_chart(chart)


def textgrad_history(meta):
    hist = pd.DataFrame(meta["history"])
    hist["acc"] = 100 * hist["val_accuracy"]
    hist["decision"] = hist["kept"].map({True: "kept", False: "reverted"})
    base = alt.Chart(hist).encode(x=alt.X("step:O", title="TEXTGRAD STEP", axis=alt.Axis(labelAngle=0)))
    line = base.mark_line(color=theme.SERIES[2], strokeWidth=2).encode(
        y=alt.Y("acc:Q", title="DEV ACCURACY (%)", scale=alt.Scale(zero=False)))
    dots = base.mark_point(size=90, filled=True, stroke="#0b0c0f", strokeWidth=2).encode(
        y="acc:Q", shape=alt.Shape("decision:N", scale=alt.Scale(domain=["kept", "reverted"], range=["circle", "cross"]),
                                   title="Rewrite"),
        color=alt.Color("decision:N", scale=alt.Scale(domain=["kept", "reverted"], range=[theme.GOOD, theme.BAD]),
                        title="Rewrite"),
        tooltip=["step", alt.Tooltip("acc:Q", title="dev accuracy %", format=".1f"), "decision"])
    return theme.style_chart(line + dots, height=230)


def render():
    theme.page_header("Optimization · manual vs automatic prompts", "Automatic *prompt optimization*",
                      "Three optimizers rewrite parts of the prompt using FinQA train (50 questions) and dev "
                      "(40 questions) only — the test sets are never seen. Their one-time cost is reported next to "
                      "any accuracy gain.", core.status_pills())
    theme.cards([("What it changes · " + changes, label, how, "finreason/dspy_opt.py" if "dspy" in p
                  else "finreason/textgrad_opt.py") for p, label, changes, how in OPTIMIZERS])
    main = core.main_summary()
    model = st.segmented_control("Model whose prompt was optimized", core.MODELS, default=core.SMALL, required=True,
                                 format_func=core.model_name, key="opt_model")

    theme.section("One-time optimization cost", "Measured live (no response cache): wall-clock minutes, model "
                  "calls and tokens used while optimizing, and accuracy on the 40 dev questions.", kicker="cost")
    tiles = []
    busy = core.experiments_running()
    for prefix, label, _, _ in OPTIMIZERS:
        meta = artifact_for(prefix, model)
        if meta is None:
            tiles.append((label, "running" if busy else "not run",
                          "in the experiment queue" if busy else "pending · not part of these results",
                          theme.WARN, True))
            continue
        minutes, calls, tokens = cost_of(prefix, meta)
        val = meta["val_accuracy"]
        tiles.append((label, core.pct(val), f"dev accuracy · {minutes:.0f} min · {calls:,} calls · {tokens:,} tokens",
                      theme.SERIES[2]))
    theme.kpis(tiles)

    theme.section("Test accuracy: optimized vs hand-written", "Each optimized prompt is evaluated exactly like the "
                  "other strategies (same questions and scorer). Lines are 95% bootstrap CIs.", kicker="does it pay?")
    chart = test_accuracy_chart(main, model) if main is not None else None
    if chart is None:
        st.info(f"The optimized prompts for {core.model_label(model)} have not been created and tested yet "
                "(pending); this chart fills in automatically once they are run and the results are refreshed.")
    else:
        st.altair_chart(chart, width="content", theme=None)

    theme.section("What each optimizer chose", kicker="inspect the artifacts")
    for prefix, label, _, _ in OPTIMIZERS:
        meta = artifact_for(prefix, model)
        with st.expander(label + ("" if meta else " — pending"), expanded=False):
            if meta is None:
                st.caption("Not created yet: this optimizer has not been run for this model, so it is not part "
                           "of the results.")
                continue
            if prefix == "textgrad":
                c1, c2 = st.columns([1, 1.2], gap="large")
                with c1:
                    st.altair_chart(textgrad_history(meta), width="stretch", theme=None)
                    st.caption(f"Task model {core.model_label(meta['task_model'])}, feedback from "
                               f"{core.model_label(meta['optimizer_model'])}; {meta['train_size']} train / "
                               f"{meta['val_size']} dev questions.")
                with c2:
                    st.caption("Optimized system prompt")
                    st.code(meta["system_prompt"], language=None, wrap_lines=True)
                    st.caption("Original system prompt")
                    st.code(meta["history"][0]["prompt"], language=None, wrap_lines=True)
                for h in meta["history"][1:]:
                    st.caption(f"Step {h['step']} · {h.get('n_wrong_in_batch', 0)} wrong in batch · dev accuracy "
                               f"{core.pct(h['val_accuracy'], 1)} · {'kept' if h['kept'] else 'reverted'}")
                    st.code(h["prompt"], language=None, wrap_lines=True)
            else:
                program = meta["program"]
                st.caption("Instruction")
                st.code(program["instruction"], language=None, wrap_lines=True)
                st.caption(f"{len(program['demos'])} demonstrations (questions the model solved correctly)")
                for i, demo in enumerate(program["demos"], 1):
                    st.markdown(f"**Demo {i}.** {demo.get('question')}")
                    if demo.get("reasoning"):
                        st.code(f"{demo['reasoning']}\nAnswer: {demo.get('answer')}", language=None, wrap_lines=True)
