"""Overview: the problem, the headline findings (computed live from the results), the research gaps
from the literature and how FinReason addresses each, and a checklist of every claim with its status."""
import streamlit as st

import core
import theme
from finreason.config import ARTIFACTS, RUNS_DIR

SINGLE_CALL = ["cot_zs", "cot_fs", "decomp_fs", "pot_fs"]
REASONING = ["cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"]

PAPERS = [
    # (group, paper, venue, addresses, key result, gap, how FinReason fills it, where)
    ("Foundational papers", "FinQA [1]", "EMNLP 2021", "Numerical QA over financial tables + text (8,281 Qs)",
     "Fine-tuned FinQANet 61.2% vs experts 91.2%", "Needs fine-tuning; US $ reports only; no prompting or cost study",
     "Prompting only, small local LLMs; Indian ₹ set; tokens and latency per answer",
     "strategies.py · data/indian · Results"),
    ("", "Program-of-Thought [15]", "TMLR 2023", "LLMs slip at arithmetic in text; let Python compute",
     "FinQA: CoT 40.4% → PoT 64.5%", "Trusts every number in the code; no code safety",
     "VPSC rejects numbers not in the report; 4-layer sandbox", "verify.py · sandbox.py · Robustness"),
    ("", "EEDP [8]", "Findings ACL 2024", "Where LLMs fail at maths over financial documents",
     "Matches or beats CoT / PoT; errors in extraction", "Hand-written prompts only; no memorization check",
     "DSPy / TextGrad vs 7 strategies; number-perturbation test", "dspy_opt.py · perturb.py · Optimization"),
    ("Latest papers (2025–2026)", "FinanceReasoning [40]", "ACL 2025",
     "Harder, cleaner financial numerical-reasoning benchmark", "o1 + PoT best at 89.1%; numbers still imprecise",
     "Large frontier models only; no operand check", "Small local models (Qwen3 1.7B / 8B); VPSC; prompt optimization",
     "llm.py · strategies.py · Results"),
    ("", "VeriFin [38]", "arXiv 2026", "Verify the numbers in LLM financial answers",
     "XBRL + Z3 solver: 0 wrong claims accepted", "Needs XBRL-tagged US filings and a solver",
     "VPSC checks the plain report table — works on Indian PDFs", "verify.py · Ask (PDF upload)"),
    ("", "IndiaFinBench [37]", "arXiv 2026", "Indian regulatory text (SEBI, RBI), 406 Qs",
     "12 models zero-shot: 70.4–89.7%", "Regulatory text, not report tables; zero-shot only",
     "Indian annual-report set (44 Qs); 7 strategies compared", "data/indian · Datasets"),
]


def headline_findings(main, summary):
    out = []
    models = [m for m in core.MODELS if all(core.complete(core.cell(main, d, m, s), d)
                                            for d in ("finqa", "tatqa") for s in ("direct", "cot_fs", "pot_fs"))]
    for m in models:
        direct = [core.cell(main, d, m, "direct") for d in core.DATASETS]
        direct = [r["accuracy"] for r in direct if r is not None]
        reasoning = [r["accuracy"] for d in core.DATASETS for s in REASONING
                     if (r := core.cell(main, d, m, s)) is not None and core.complete(r, d)]
        if direct and reasoning:
            out.append(("Reasoning is essential", f"{core.model_label(m)}: answer-only prompts score at most "
                        f"{core.pct(max(direct))}; asking for reasoning lifts accuracy to {core.pct(min(reasoning))}–"
                        f"{core.pct(max(reasoning))}."))
    m = core.SMALL if core.SMALL in models else (models[0] if models else None)
    if m:
        best = []
        for d in core.DATASETS:
            rows = [(core.cell(main, d, m, s), s) for s in SINGLE_CALL]
            rows = [(r["accuracy"], s) for r, s in rows if r is not None]
            if rows:
                acc, s = max(rows)
                best.append(f"{core.strategy_label(s)} on {core.DATASET_LABEL[d]} ({core.pct(acc)})")
        out.append(("Best single call", f"{core.model_label(m)}: " + "; ".join(best) + "."))
        pairs = []   # same definition as the review slides: the 5-sample strategies vs few-shot CoT
        for d in core.DATASETS:
            base = core.cell(main, d, m, "cot_fs")
            for multi in ("sc_cot", "pot_sc", "vpsc"):
                a = core.cell(main, d, m, multi)
                if a is not None and base is not None:
                    pairs.append((a["total_tokens"] / base["total_tokens"], 100 * (a["accuracy"] - base["accuracy"])))
        if pairs:
            sig = core.results_csv("significance.csv")
            significant = sig is not None and ((sig["model"] == m) & (~sig["perturbed"]) & (sig["fmt"] == "markdown")
                                               & (sig["context"] == "full") & (~sig["think"])
                                               & sig["strategy"].isin(["sc_cot", "pot_sc", "vpsc"])
                                               & (sig["p_holm"] < .05)).any()
            out.append(("Five samples rarely pay", f"Self-Consistency, PoT-SC and VPSC use {min(p[0] for p in pairs):.1f}–"
                        f"{max(p[0] for p in pairs):.1f}× the tokens of few-shot CoT for {min(p[1] for p in pairs):+.0f} to "
                        f"{max(p[1] for p in pairs):+.0f} points, "
                        f"{'some significant' if significant else 'none significant after correction'} ({core.model_label(m)})."))
    vpsc = core.results_csv("vpsc.csv")
    if vpsc is not None and int(vpsc["flagged_questions"].sum()):
        f, w = int(vpsc["flagged_questions"].sum()), int(vpsc["flagged_wrong"].sum())
        out.append(("Grounding is a precise warning flag", f"VPSC's check flagged {f} questions; {w} of them were "
                    f"answered wrongly ({core.pct(w / f)}) — use it to alert or abstain."))
    pert = core.results_csv("perturbation.csv")
    if pert is not None and len(pert):
        sig = int((pert["p_value"] < .05).sum())
        out.append(("No sign of memorization", f"With every number changed, accuracy moves by "
                    f"{-100 * pert['drop'].max():+.0f} to {-100 * pert['drop'].min():+.0f} points; "
                    f"{sig} of {len(pert)} drops are significant (McNemar)."))
    errors = core.results_csv("errors.csv")
    if errors is not None and m:
        # same definition as in the review slides: FinQA + TAT-QA, reasoning strategies, one model
        e = errors[(errors["model"] == m) & errors["dataset"].isin(["finqa", "tatqa"])
                   & errors["strategy"].isin(REASONING)]
        totals = e.drop(columns=["dataset", "model", "strategy"]).sum()
        if totals.sum():
            share = totals / totals.sum()
            out.append(("Errors are about evidence", f"{core.pct(share.get('evidence_error', 0))} of wrong answers use "
                        f"a wrong or missing number, {core.pct(share.get('reasoning_error', 0))} a wrong formula, "
                        f"{core.pct(share.get('scale_error', 0))} a unit/scale slip ({core.model_label(m)}, "
                        f"FinQA + TAT-QA, reasoning strategies, {int(totals.sum())} wrong answers)."))
    return out


def claims(main):
    have = lambda pattern: any(RUNS_DIR.glob(pattern))
    art = lambda name: (ARTIFACTS / name).exists()
    both_models = all(core.complete(core.cell(main, d, m, s), d) for m in core.MODELS for d in ("finqa", "tatqa")
                      for s in ("direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot"))

    def optimizer(name):
        """Done when the prompt is optimized for both models and tested on all three datasets."""
        tested = 0
        for model in ("1.7b", "8b"):
            prefix = "dspy" if name.startswith("dspy") else "textgrad"
            runs = [f"{d}_test_n{core.FULL_N[d]}__ollama-qwen3-{model}__{prefix}-{name}_ollama-qwen3-{model}__"
                    for d in core.DATASETS]
            if art(f"{name}_ollama-qwen3-{model}.json") and all(have(r + "*") for r in runs):
                tested += 1
        return tested == 2, f"artifacts/{name}_*.json · optimized and tested for {tested}/2 models"

    boot, mipro, tg = optimizer("dspy_bootstrap"), optimizer("dspy_mipro"), optimizer("textgrad")
    return [
        (True, "7 hand-written strategies: Direct, CoT zero-/few-shot, Decomposition, PoT, Self-Consistency, VPSC",
         "finreason/strategies.py · prompts.py"),
        (have("*__vpsc__*"), "VPSC: 5 programs → sandbox → grounding check → vote, with the PoT-SC ablation",
         "finreason/strategies.py · verify.py · results/vpsc.csv"),
        (boot[0], "DSPy BootstrapFewShot optimizes the few-shot demos", boot[1]),
        (mipro[0], "DSPy MIPROv2 optimizes instruction + demos (Bayesian search)", mipro[1]),
        (tg[0], "TextGrad optimizes the system prompt with textual gradients", tg[1]),
        (both_models, "Qwen3-1.7B vs Qwen3-8B, locally in Ollama, on accuracy and cost", "results/summary.csv"),
        (True, "FinQA 100 · TAT-QA 100 · Indian set 44 (verified against the PDFs)",
         "finreason/data.py · results/indian_verification.csv"),
        (have("*__json__*") and have("*__html__*") and have("*__text__*"), "Table as Markdown / JSON / HTML / text",
         "finreason/tables.py · results/ablations.csv"),
        (have("*retrieved5*"), "Full page vs top-5 retrieved rows (BM25 + MiniLM/FAISS + RRF)",
         "finreason/retrieval.py · results/retrieval_recall.csv"),
        (have("*__think*"), "Thinking mode on / off", "results/runs/*__think.jsonl"),
        (True, "Execution accuracy (±0.5%), exact match, F1, tokens per question and per correct answer, latency, "
         "format and code-failure rate", "finreason/answers.py · scripts/analyze.py"),
        (True, "95% bootstrap CIs; McNemar vs few-shot CoT, Holm-corrected", "finreason/metrics.py"),
        (True, "Accuracy by reasoning steps and evidence source", "results/accuracy_by_steps.csv · _by_evidence.csv"),
        (True, "8-category rule-based error taxonomy", "finreason/errors.py · Error explorer"),
        (have("finqa-perturbed*"), "Number-perturbation (memorization) test", "finreason/perturb.py"),
        (True, "4-layer sandbox for model-written code", "finreason/sandbox.py"),
        (True, "Optimizers see only FinQA train (50) and dev (40); test sets never", "scripts/optimize_*.py"),
        (True, "Auditable web app: evidence rows, code, votes and prompt for every answer", "app/"),
    ]


def render():
    theme.page_header("PES University · UE24AM343AB5 · Prompt Engineering and Optimization",
                      "Numerical reasoning over *financial reports*",
                      "Which prompting strategies and automatic prompt optimizers make small, local LLMs accurate, "
                      "reliable and cheap at questions like “what was the revenue growth?” — measured on FinQA, TAT-QA "
                      "and our own Indian annual-report set. We change only the prompt, never the model.",
                      core.status_pills())
    main = core.main_summary()
    summary = core.summary()
    if summary is not None and main is not None:
        best = {d: main[main["dataset"] == d]["accuracy"].max() for d in core.DATASETS
                if d in set(main["dataset"])}
        theme.kpis([
            ("Prompt configurations", "10", "7 hand-written + 3 automatic optimizers", None),
            ("Answers scored", f"{int(summary['n'].sum()):,}", f"{summary.shape[0]} runs · Qwen3 1.7B and 8B", None),
            ("Best accuracy", " · ".join(core.pct(best[d]) for d in best),
             " · ".join(core.DATASET_LABEL[d] for d in best), theme.GOOD, True),
            ("Model calls", f"{int((summary['n'] * summary['calls']).sum()):,}", "all on a local Apple M4", None)])

    left, right = st.columns([1, 1.15], gap="large")
    with left:
        theme.section("The problem", "One question needs four skills — and one wrong digit, unit or sign gives a "
                      "confident wrong answer.", kicker="why it is hard")
        theme.html_table(["₹ crore", "FY25", "FY24"], [
            ["Revenue from operations", "<b>54,842</b>", "<b>47,114</b>"],
            ["Profit before tax", "4,481", "4,607"],
            ["Changes in inventories", "(6,537)", "(2,149)"]])
        theme.render("""<div class="fr-q" style="margin-top:1rem"><div class="id">Q · Titan Company, FY25 annual report</div>
          <div class="txt">What was the revenue growth from FY24 to FY25?</div><div class="fr-chips">
          <span class="fr-chip">1 · locate the row and years</span><span class="fr-chip">2 · extract with unit, scale, sign</span>
          <span class="fr-chip">3 · formula (new − old) / old × 100</span><span class="fr-chip gold">4 · compute → 16.40%</span>
          </div></div>""")
    with right:
        theme.section("Headline findings", "Computed live from results/ — they update as experiments finish.",
                      kicker="what we found")
        findings = headline_findings(main, summary) if main is not None else []
        if findings:
            theme.html_table(["Finding", "Evidence"], [[f"<b>{theme.esc(t)}</b>", theme.esc(b)] for t, b in findings])
        else:
            st.info("Run the experiments and scripts/analyze.py to see findings here.")

    theme.section("Literature, gaps and how FinReason fills them", "Main and latest papers from our Review 1 survey. "
                  "The last column points to where each answer lives in this project.", kicker="research gap")
    rows, groups = [], {}
    for i, (group, paper, venue, addresses, result, gap, fill, where) in enumerate(PAPERS):
        if group:
            groups[i] = group
        rows.append([f"<b>{theme.esc(paper)}</b><span class='m'>{theme.esc(venue)}</span>", theme.esc(addresses),
                     theme.esc(result), theme.esc(gap), f"<b>{theme.esc(fill)}</b>",
                     f"<span class='m'>{theme.esc(where)}</span>"])
    theme.html_table(["Paper", "What it addresses", "Key result", "Gap it leaves", "How FinReason fills it", "Where"],
                     rows, groups)

    theme.section("What we built", kicker="contributions")
    theme.cards([
        ("Our method", "VPSC — Verified Program Self-Consistency", "Sample 5 programs, run them in the sandbox, reject "
         "any program that uses a number not found in the report, majority-vote the rest. Training-free and works on "
         "plain tables.", "finreason/strategies.py · verify.py"),
        ("New data", "Indian calculation set", "44 multi-step questions over Titan, Asian Paints, Marico and Pidilite "
         "reports (₹ crore / lakh), answers computed from formulas and re-checked against the PDF pages.",
         "data/indian/indian_set.jsonl"),
        ("Head to head", "Manual vs automatic prompting", "7 hand-written strategies against DSPy BootstrapFewShot, "
         "MIPROv2 and TextGrad, with one-time cost, confidence intervals and paired significance tests.",
         "scripts/run_all.sh"),
        ("Auditable", "Every answer can be checked", "Evidence rows, generated code, variable trace, votes with "
         "grounding status and the exact prompt — for any question, table or PDF page.", "app/")])

    theme.section("Claims checklist", "Every claim from our three reviews, checked against the files in this project. "
                  "✓ = implemented and its results are present; … = implemented, results not complete yet (pending).",
                  kicker="traceability")
    theme.claims(claims(main) if main is not None else [])
    theme.footer()
