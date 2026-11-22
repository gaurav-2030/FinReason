"""Method: the pipeline, the strategies with their real prompt text, VPSC, the sandbox, scoring and
statistics, references and the team. Prompt texts and constants are read from the code itself."""
import streamlit as st

import core
import theme
from finreason import config
from finreason.prompts import ANSWER_FORMAT, INSTRUCTIONS, REPAIR_PROMPT, SYSTEM_PROMPT
from finreason.sandbox import ALLOWED_MODULES, FORBIDDEN_NAMES
from finreason.verify import CONSTANTS, SCALE_FACTORS

PIPELINE = [
    ("01", "Load", "FinQA / TAT-QA / Indian set → one Example object", "data.py"),
    ("02", "Context", "Serialize the table; full page or top-k hybrid retrieval", "tables.py · retrieval.py"),
    ("03", "Prompt", "Strategy template + worked examples, same system prompt for all", "prompts.py"),
    ("04", "LLM call", "Qwen3 via Ollama (or an API); cache, tokens, latency", "llm.py"),
    ("05", "Execute / parse", "PoT code → sandbox; otherwise read the 'Answer:' line", "sandbox.py · answers.py"),
    ("06", "Score", "Within 0.5% of gold, or equal at the gold's precision; EM, F1", "answers.py"),
    ("07", "Diagnose", "Rule-based taxonomy of every wrong answer", "errors.py"),
    ("08", "Record & analyse", "JSONL per run → CIs, McNemar, figures, this app", "experiment.py · analyze.py"),
]

STRATEGY_ROWS = [
    ("Direct (baseline)", "direct", "A number", "1", "— (no reasoning)"),
    ("Zero-shot CoT [11]", "cot", "Reasoning + answer", "1", "Multi-step slips"),
    ("Few-shot CoT [10]", "cot", "Reasoning + answer (after 3 worked FinQA train examples)", "1", "Format, units, scale"),
    ("Decomposition [8]", "decomp", "Formula, operands, steps", "1", "Wrong formula / operand"),
    ("Program-of-Thought [15]", "pot", "Code → executed result (1 repair retry)", "1–2", "Arithmetic errors"),
    ("Self-Consistency [12]", "cot", "5 answers → vote (1 greedy + 4 at T = 0.7)", "5", "Unstable reasoning"),
    ("VPSC (ours)", "pot", "5 programs → grounded → vote", "5", "Hallucinated numbers"),
]

REFERENCES = [
    "[1] Z. Chen et al., “FinQA: A dataset of numerical reasoning over financial data,” EMNLP 2021.",
    "[2] F. Zhu et al., “TAT-QA: A question answering benchmark on a hybrid of tabular and textual content in finance,” ACL-IJCNLP 2021.",
    "[5] P. Islam et al., “FinanceBench: A new benchmark for financial question answering,” arXiv:2311.11944, 2023.",
    "[8] P. Srivastava et al., “Evaluating LLMs' mathematical reasoning in financial document question answering,” Findings of ACL 2024.",
    "[10] J. Wei et al., “Chain-of-thought prompting elicits reasoning in large language models,” NeurIPS 2022.",
    "[11] T. Kojima et al., “Large language models are zero-shot reasoners,” NeurIPS 2022.",
    "[12] X. Wang et al., “Self-consistency improves chain of thought reasoning in language models,” ICLR 2023.",
    "[15] W. Chen et al., “Program of thoughts prompting,” TMLR 2023.",
    "[19] O. Khattab et al., “DSPy: Compiling declarative language model calls into self-improving pipelines,” ICLR 2024.",
    "[20] K. Opsahl-Ong et al., “Optimizing instructions and demonstrations for multi-stage language model programs,” EMNLP 2024.",
    "[21] M. Yuksekgonul et al., “Optimizing generative AI by backpropagating language model feedback,” Nature 639, 2025.",
    "[28] I. Mirzadeh et al., “GSM-Symbolic: Understanding the limitations of mathematical reasoning in LLMs,” ICLR 2025.",
    "[29] A. Yang et al., “Qwen3 technical report,” arXiv:2505.09388, 2025.",
    "[36] CompoundingAI, “IndFin-Bench: A benchmark grounded in Indian financial filings,” Hugging Face dataset, 2026.",
    "[37] R. S. Pall, “IndiaFinBench: An evaluation benchmark for LLM performance on Indian financial regulatory text,” arXiv:2604.19298, 2026.",
    "[38] B. Hall, S. Shome, and W. Eiers, “VeriFin: A neurosymbolic framework for verifying LLM-generated financial claims,” arXiv:2608.10213, 2026.",
    "[39] H. Chen et al., “Fighting numerical hallucinations via data-centric compilation for online financial QA,” KDD 2026 (ADS).",
    "[40] Z. Tang et al., “FinanceReasoning: Benchmarking financial numerical reasoning more credible, comprehensive and challenging,” ACL 2025.",
]

TEAM = [("Gaurav Girish", "PES1UG24AM103"), ("Sunay R Hegde", "PES1UG24AM903"),
        ("Dhruvagouda", "PES1UG24AM089"), ("Hanshal Nagesh", "PES1UG24AM110")]


def render():
    theme.page_header("Method · how it works", "One pipeline — *only the prompt changes*",
                      "Same questions, same scorer and same models for every strategy, so any difference comes from "
                      "the prompt alone.", core.status_pills())

    theme.section("The pipeline", "Eight stages from a report page to a scored, diagnosed answer. The experiment "
                  "runner and this app use exactly this flow.", kicker="architecture")
    theme.render("<div class='fr-flow'>" + "".join(
        f"<div class='fr-card'><div class='no'>STAGE {no}</div><h4>{theme.esc(t)}</h4><p>{theme.esc(d)}</p>"
        f"<span class='file'>finreason/{theme.esc(f)}</span></div>" for no, t, d, f in PIPELINE) + "</div>")

    theme.section("Seven prompting strategies", "Every strategy shares the system prompt and the answer rules; the "
                  "prompt text below is read from finreason/prompts.py.", kicker="hand-written prompts")
    theme.html_table(["Strategy", "What the prompt asks for", "Model output", "Calls", "Error it targets"],
                     [[f"<b>{theme.esc(n)}</b>", f"<span class='m' style='font-size:.78rem'>"
                       f"{theme.esc(INSTRUCTIONS[style])}</span>", theme.esc(out), calls, theme.esc(err)]
                      for n, style, out, calls, err in STRATEGY_ROWS])
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.caption("System prompt (all strategies)")
        st.code(SYSTEM_PROMPT, language=None, wrap_lines=True)
        st.caption("PoT repair prompt (sent once if the code fails)")
        st.code(REPAIR_PROMPT, language=None, wrap_lines=True)
    with c2:
        st.caption("Answer rules (all text strategies)")
        st.code(ANSWER_FORMAT, language=None, wrap_lines=True)
    st.caption("Plus 3 automatic optimizers — DSPy BootstrapFewShot [19], MIPROv2 [20] and TextGrad [21] — for "
               "10 prompt configurations in total (see the Optimization page).")

    theme.section("VPSC — Verified Program Self-Consistency", "Our method targets the most common error: using a "
                  "number that is not in the report.", kicker="our method")
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        theme.html_table(["Step", "What happens"], [
            ["<b>1 · Sample</b>", f"{config.SC_SAMPLES} programs with the few-shot PoT prompt: 1 greedy + "
             f"{config.SC_SAMPLES - 1} at temperature {config.SC_TEMPERATURE}"],
            ["<b>2 · Execute</b>", "Each program runs in the sandbox and must set <code>ans</code>"],
            ["<b>3 · Ground</b>", "Every number literal in the code must appear in the report (rescaled ×"
             + ", ×".join(f"{f:g}" for f in SCALE_FACTORS[1:]) + " allowed)"],
            ["<b>4 · Vote</b>", "Majority vote over executed and grounded programs; ties go to the first answer"],
            ["<b>5 · Fallback</b>", "If no program is grounded, vote over all executed programs — and flag it"],
            ["<b>Ablation</b>", "PoT-SC: the same 5 programs (same cache keys) without step 3, so any difference "
             "is due to verification alone"]])
    with right:
        st.caption("Constants a program may use without finding them in the report")
        st.code(", ".join(f"{c:,}" for c in sorted(CONSTANTS)) + ", and years 1900–2100", language=None, wrap_lines=True)
        st.caption("Rejected by the check (54,482 is not in the report)")
        st.code("revenue_fy25 = 54482   # misread: the report says 54,842\nrevenue_fy24 = 47114\n"
                "ans = (revenue_fy25 - revenue_fy24) / revenue_fy24 * 100", language="python")

    theme.section("Sandbox: running model code safely", "Model-written code is untrusted — four independent layers "
                  "keep it harmless.", kicker="finreason/sandbox.py")
    theme.cards([("Layer 1", "Static AST check", f"Only import {', '.join(sorted(ALLOWED_MODULES))}; no dunder "
                  f"attributes; {len(FORBIDDEN_NAMES)} forbidden names such as open, eval, exec, os.", ""),
                 ("Layer 2", "Isolated process", "A fresh python -I process per program (no site packages, no "
                  "environment); code passed on stdin.", ""),
                 ("Layer 3", "Restricted builtins", "A whitelist (abs, round, sum, min, max …); print disabled; "
                  "imports other than math raise.", ""),
                 ("Layer 4", "Resource limits", "CPU rlimit plus a 5-second wall-clock timeout; only ans and "
                  "numeric variables come back, as JSON.", "")])

    theme.section("Scoring and statistics", kicker="one scorer everywhere")
    theme.html_table(["Rule", "Detail"], [
        ["<b>Correct</b>", f"Within {100 * config.REL_TOLERANCE:g}% of the gold answer, or equal to it at the gold's "
         "own precision"],
        ["<b>Percentages</b>", "12.5 and 0.125 are both accepted (FinQA stores fractions, TAT-QA percents)"],
        ["<b>Parsing</b>", "₹, $, 1,00,000 grouping, (brackets) = negative, crore / lakh / million"],
        ["<b>Also reported</b>", "Accuracy at 1% tolerance, exact match (2 decimals), token F1, tokens per question "
         "and per correct answer, latency, format- and code-failure rates"],
        ["<b>Statistics</b>", "95% percentile bootstrap CIs (2,000 resamples); exact McNemar test against few-shot "
         "CoT, Holm-corrected"],
        ["<b>Same scorer in</b>", "Experiments, the DSPy metric, TextGrad's loss, the analysis and this app"]])

    theme.section("References", kicker="numbering as in our review slides")
    theme.render("<div class='fr-card'>" + "".join(f"<p style='margin:.25rem 0'>{theme.esc(r)}</p>"
                                                   for r in REFERENCES) + "</div>")

    theme.section("Team", kicker="B.Tech CSE (AI & ML), semester 5, PES University")
    theme.cards([("", name, usn, "") for name, usn in TEAM])
    theme.footer()
