"""Ask: run one question through the full pipeline and audit every step - the evidence rows the
model used, the generated code and its variable trace, the votes with their grounding status, and
the exact prompt."""
import json
import time

import pandas as pd
import streamlit as st

import core
import theme
from finreason.answers import score
from finreason.prompts import build_messages
from finreason.retrieval import build_context
from finreason.strategies import get_strategy
from finreason.verify import grounding_check
from views.common import (choose_example, evidence_rows, offline_notice, run_with_timer, settings,
                          styled_table)


def exact_messages(strategy, context, example, fmt):
    """The chat messages the strategy sends (for DSPy: None, its prompt is built by DSPy)."""
    if strategy.startswith("textgrad:"):
        prompt = json.load(open(core.ROOT / strategy.split(":", 1)[1]))["system_prompt"]
        return build_messages("cot", context, example.question, fewshot=False, fmt=fmt, system=prompt)
    if strategy.startswith("dspy:"):
        return None
    style = core.STYLE_OF[strategy]
    return build_messages(style, context, example.question, fewshot=core.FEWSHOT.get(strategy, True), fmt=fmt)


def flag_evidence():
    """How often a flagged question was answered wrongly in our experiments (from results/vpsc.csv)."""
    vpsc = core.results_csv("vpsc.csv")
    if vpsc is None or not int(vpsc["flagged_questions"].sum()):
        return ""
    flagged, wrong = int(vpsc["flagged_questions"].sum()), int(vpsc["flagged_wrong"].sum())
    return f"In our experiments {wrong} of {flagged} flagged questions were answered wrongly. "


def grounding_flag(strategy, pred, context):
    """Warning flag from the grounding check (VPSC's verifier, also applied to single programs)."""
    if "grounded" in pred.extra:
        votes, grounded = pred.extra["votes"], pred.extra["grounded"]
        executed = [g for a, g in zip(votes, grounded) if a is not None]
        bad = len(executed) - sum(executed)
        if not executed:
            return False, "No program ran successfully, so the answer could not be verified."
        if bad == 0:
            return True, f"All {len(executed)} executed programs use only numbers found in the report."
        if not any(executed):
            return False, ("No program passed the grounding check: every program used a number that is not "
                           "in the report. Treat this answer as unreliable.")
        return False, (f"{bad} of {len(executed)} programs used numbers not found in the report and were "
                       f"rejected before the vote. {flag_evidence()}Check this answer against the evidence.")
    if pred.code and not pred.error:
        ok, missing = grounding_check(pred.code, context)
        if ok:
            return True, "Every number in the program appears in the report."
        shown = ", ".join(f"{v:g}" for v in missing[:4])
        return False, f"The program uses numbers not found in the report ({shown}). Check the evidence."
    return None


def run_pipeline(example, strategy, model, fmt, mode, k):
    if strategy.startswith("dspy:"):   # a compiled DSPy program runs with the model it was compiled for
        model = core.dspy_model(strategy) or model
    llm = core.get_llm(model)
    retriever = core.get_retriever() if mode == "retrieved" else None
    t0 = time.perf_counter()
    context, retrieved = build_context(example, fmt=fmt, mode=mode, retriever=retriever, k=k)
    context_s = time.perf_counter() - t0
    pred, wall = run_with_timer(lambda: get_strategy(strategy)(llm, example, context, fmt),
                                f"{core.strategy_label(strategy)} is reasoning",
                                f"{core.model_label(model)} · local inference via Ollama")
    correct = None
    if example.gold is not None:
        correct = score(pred.answer, example.gold, example.question, example.scale)[0]
    return dict(example=example, strategy=strategy, model=model, fmt=fmt, mode=mode, k=k, context=context,
                retrieved=retrieved, context_s=context_s, pred=pred, wall=wall, correct=correct,
                flag=grounding_flag(strategy, pred, context))


def stages(r):
    pred = r["pred"]
    grounded = pred.extra.get("grounded")
    votes = pred.extra.get("votes")
    flag = r["flag"]
    sandbox_state = ("bad" if pred.error else "good") if pred.code else "off"
    context = "full page" if r["mode"] == "full" else f"top-{r['k']} units"
    return [
        ("Context", f"{context} · {r['fmt']}", "on"),
        ("Prompt", core.strategy_label(r["strategy"]), "on"),
        ("Model", f"{core.model_label(r['model'])} · {pred.n_calls} call{'s' * (pred.n_calls != 1)}", "on"),
        ("Sandbox", ("error" if pred.error else "executed") if pred.code else "not used", sandbox_state),
        ("Grounding", (f"{sum(grounded)}/{len(grounded)} grounded" if grounded is not None
                       else ("checked" if flag else "not used")),
         "off" if flag is None else ("good" if flag[0] else "warn")),
        ("Vote", f"{len(votes)} samples" if votes else "single answer", "on" if votes else "off"),
        ("Score", {True: "correct", False: "wrong", None: "no gold answer"}[r["correct"]],
         {True: "good", False: "bad", None: "off"}[r["correct"]]),
    ]


def show_result(r):
    example, pred = r["example"], r["pred"]
    theme.stepper(stages(r))
    left, right = st.columns([1, 1.5], gap="large")
    with left:
        chips = []
        if r["correct"] is not None:
            chips.append(theme.chip(f"gold {core.fmt_number(example.gold)}", "good" if r["correct"] else "bad",
                                    "✓" if r["correct"] else "✕"))
            chips.append(theme.chip("correct" if r["correct"] else "wrong", "good" if r["correct"] else "bad"))
        chips.append(theme.chip(core.strategy_label(r["strategy"]), "gold"))
        if pred.how:
            chips.append(theme.chip(f"read from: {pred.how.replace('_', ' ')}"))
        theme.answer_card(core.fmt_number(pred.answer), core.exact_number(pred.answer), "".join(chips),
                          pred.extra.get("agreement"), pred.n_calls, pred.prompt_tokens + pred.completion_tokens,
                          pred.latency, r["flag"])
        if pred.error:
            st.error(f"Sandbox: {pred.error}", icon="⛔")
        st.caption(f"Context built in {r['context_s']:.2f}s · wall time {r['wall']:.1f}s"
                   + (" · answered from the response cache" if pred.latency > r["wall"] + 1 else ""))
    with right:
        tabs = st.tabs(["Evidence", "Code & trace", "Reasoning", "Votes", "Prompt"])
        with tabs[0]:
            if example.table:
                used, chosen = evidence_rows(example, pred, r["retrieved"])
                theme.legend([("rows whose numbers the model used", theme.EVIDENCE),
                              ("rows chosen by retrieval", theme.RETRIEVED)])
                st.dataframe(styled_table(example, used, chosen), width="stretch")
            if r["retrieved"]:
                st.caption("Retrieved evidence units (BM25 + MiniLM, fused with Reciprocal Rank Fusion)")
                st.dataframe(pd.DataFrame(r["retrieved"], columns=["unit", "text", "RRF score"]),
                             width="stretch", hide_index=True)
            if example.texts:
                with st.expander("Text on the page"):
                    st.write("\n\n".join(t for t in example.texts[:25]))
        with tabs[1]:
            if pred.code:
                if pred.extra.get("first_error"):
                    st.warning(f"The first program failed ({pred.extra['first_error']}); the error was shown to "
                               "the model once and this is the repaired program.", icon="🔁")
                st.code(pred.code, language="python")
                if pred.trace:
                    st.caption("Variables computed by the program in the sandbox")
                    trace = pd.DataFrame([(k, core.fmt_number(v) if not isinstance(v, bool) else str(v))
                                          for k, v in pred.trace.items()], columns=["variable", "value"])
                    st.dataframe(trace, width="stretch", hide_index=True)
            else:
                st.info("This strategy answers in text. Choose Program-of-Thought, PoT Self-Consistency or "
                        "VPSC to see the generated code.")
        with tabs[2]:
            st.code(pred.output or "(empty output)", language=None, wrap_lines=True)
        with tabs[3]:
            if "votes" in pred.extra:
                votes = pd.DataFrame({"sample": [f"#{i + 1}" + (" · greedy" if i == 0 else " · T=0.7")
                                                 for i in range(len(pred.extra["votes"]))],
                                      "answer": [core.fmt_number(v) for v in pred.extra["votes"]]})
                if "grounded" in pred.extra:
                    votes["grounded in report"] = ["✓ yes" if g else ("✕ no" if v is not None else "– did not run")
                                                   for g, v in zip(pred.extra["grounded"], pred.extra["votes"])]
                    votes["numbers not in report"] = [", ".join(f"{v:g}" for v in m) or "–"
                                                      for m in pred.extra["ungrounded_numbers"]]
                st.dataframe(votes, width="stretch", hide_index=True)
                st.caption("Ties go to the answer seen first. VPSC votes only over grounded programs "
                           "(over all executed programs if none is grounded).")
            else:
                st.info("Votes are shown for Self-Consistency, PoT Self-Consistency and VPSC.")
        with tabs[4]:
            messages = exact_messages(r["strategy"], r["context"], example, r["fmt"])
            if messages is None:
                meta = core.artifacts().get(r["strategy"].split("/")[-1].replace(".json", ""), {})
                program = meta.get("program", {})
                st.caption("DSPy builds this prompt from the compiled program: the optimized instruction, "
                           "the selected demonstrations and the input fields.")
                st.code(program.get("instruction", ""), language=None, wrap_lines=True)
                st.caption(f"{len(program.get('demos', []))} demonstrations selected by the optimizer")
            else:
                st.caption(f"{len(messages)} messages · " + ("3 worked examples precede the question"
                                                              if len(messages) > 2 else "no worked examples"))
                for m in messages:
                    with st.expander(f"{m['role']} · {len(m['content']):,} characters",
                                     expanded=m is messages[-1]):
                        st.code(m["content"], language=None, wrap_lines=True)


def render():
    theme.page_header("Ask · audit one answer", "Ask a *financial* question",
                      "Pick a question, a model and a prompting strategy. The pipeline builds the context, prompts "
                      "a local Qwen3 model, runs any generated code in the sandbox, checks that every number is "
                      "grounded in the report, votes, and scores the answer.", core.status_pills())
    with st.container(border=True):
        model, fmt, mode, k = settings("ask")
        example = choose_example("ask")
        options = core.strategy_options()
        c1, c2 = st.columns([1.3, 2], vertical_alignment="bottom")
        strategy = c1.selectbox("Prompting strategy", options, index=options.index("vpsc"),
                                format_func=core.short_label, key="ask_strategy")
        note = core.describe(strategy)
        if strategy.startswith("dspy:") and core.dspy_model(strategy) not in (None, model):
            note += f" Runs with {core.model_name(core.dspy_model(strategy))}, the model it was compiled for."
        c2.markdown(f"<div style='padding:.55rem 0;color:#9c9a92;font-size:.9rem'>{theme.esc(note)}"
                    "</div>", unsafe_allow_html=True)
        if example is not None:
            theme.question(f"{example.uid} · {core.dataset_label(example.dataset)}",
                           example.question,
                           theme.chip(f"gold answer {core.fmt_number(example.gold)}", "gold") if example.gold is not None
                           else theme.chip("no gold answer — the answer will not be scored"))
            with st.expander("Report table given to the model"):
                if example.table:
                    st.dataframe(styled_table(example), width="stretch")
                else:
                    st.caption("No table.")
        clicked = st.button("Run the pipeline", type="primary", disabled=example is None, icon=":material/play_arrow:")
    if clicked and example is not None and not offline_notice():
        try:
            st.session_state["ask_result"] = run_pipeline(example, strategy, model, fmt, mode, k)
        except Exception as exc:   # e.g. Ollama stopped mid-request or the model is not pulled
            st.session_state.pop("ask_result", None)
            st.error(f"The model call failed: {exc}", icon="⛔")
    result = st.session_state.get("ask_result")
    if result is not None:
        current = example is not None and result["example"].uid == example.uid and \
            result["example"].question == example.question
        if not current:
            st.caption("Showing the previous result — press *Run the pipeline* for the selected question.")
        theme.section("Result", kicker="pipeline trace")
        show_result(result)
