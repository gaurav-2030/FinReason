"""Review 2 (15 marks): high-level design + data collection. Slides and a written report."""
import csv
import json

import data
import diagrams as D
from common import (ROOT, Deck, REPORT_CSS, SLIDE_CSS, cover, esc, img, page, table, title_slide, ul)
from references import cite, ref_list_html

import sys
sys.path.insert(0, str(ROOT))
from finreason.prompts import ANSWER_FORMAT, INSTRUCTIONS, REPAIR_PROMPT, SYSTEM_PROMPT  # noqa: E402
from finreason.tables import serialize  # noqa: E402

LABEL = "Review 2"
SMALL_TABLE = [["in millions", "2014", "2013"], ["sales", "$ 5720", "$ 6205"], ["operating profit (loss)", "-16 ( 16 )", "271"]]

MODULES = [
    ("data.py", "Load FinQA, TAT-QA (arithmetic) and the Indian set into one <code>Example</code> format; count reasoning steps; fixed seeded sampling", "<code>load_dataset(name, split, n, seed)</code>"),
    ("tables.py", "Serialize a table as Markdown, JSON records, HTML or row-wise text", "<code>serialize(table, fmt)</code>"),
    ("retrieval.py", "Split a page into evidence units (rows, sentences); hybrid BM25 + MiniLM/FAISS ranking fused by RRF; build the prompt context", "<code>build_context(ex, fmt, mode, retriever, k)</code>"),
    ("prompts.py", "System prompt, answer-format rules, strategy instructions, three worked FinQA-train examples in CoT / decomposition / code form", "<code>build_messages(style, context, q, fewshot, fmt)</code>"),
    ("llm.py", "One client for Ollama and API providers; SQLite response cache; token and latency accounting; retries", "<code>LLM(spec).chat(messages, T, sample_id)</code>"),
    ("strategies.py", "Direct, CoT (0/3-shot), decomposition, PoT (+repair), CoT self-consistency, PoT self-consistency, VPSC", "<code>strategy(llm, ex, context, fmt) → Prediction</code>"),
    ("sandbox.py", "Static AST check, isolated <code>python -I</code> process, restricted builtins, CPU limit + timeout", "<code>run_code(code) → SandboxResult</code>"),
    ("verify.py", "Grounding check: every numeric literal in a program must occur in the report (with unit rescaling)", "<code>grounding_check(code, context)</code>"),
    ("answers.py", "Parse numbers (Indian/Western formats, brackets, %, scale words); extract the final answer; score; token F1", "<code>score(pred, gold, q, scale)</code>"),
    ("finqa_program.py", "Interpreter for FinQA gold programs (used for perturbation and error analysis)", "<code>execute(program, table)</code>"),
    ("errors.py", "Rule-based error taxonomy with 8 categories", "<code>classify_error(pred, ex, correct)</code>"),
    ("perturb.py", "Numerically perturbed FinQA questions with recomputed gold answers", "<code>perturb_dataset(examples, seed)</code>"),
    ("metrics.py", "Bootstrap CIs, exact McNemar test, Holm correction", "<code>bootstrap_ci, mcnemar, holm</code>"),
    ("dspy_opt.py / textgrad_opt.py", "DSPy signature, metric, BootstrapFewShot / MIPROv2 compilation; TextGrad system-prompt optimization loop", "<code>compile_program, optimize_system_prompt</code>"),
    ("experiment.py, scripts/", "Evaluate one question → flat JSON record; resumable experiment runner; analysis (tables, tests, figures)", "<code>evaluate_example</code>, <code>run_experiment.py</code>, <code>analyze.py</code>"),
    ("app/ (streamlit_app.py, views/)", "Web app: Overview, Ask, Compare, Results, Optimization, Robustness, Errors, Data, Method", "<code>streamlit run</code>"),
]

DECISIONS = [
    ("One common <code>Example</code> format", "Every stage works on every dataset without special cases."),
    ("One LLM client for all providers", "Identical token/latency accounting; local and API models interchangeable."),
    ("SQLite response cache", "Free, identical re-runs; resumable 30-hour experiment queue."),
    ("Same seeded sample (seed 42) everywhere", "Paired comparisons (McNemar) and reproducibility."),
    ("Model code runs in a separate restricted process", "Generated code is untrusted."),
    ("Re-score everything at analysis time", "Scoring rules can be refined without re-running models."),
    ("Few-shot examples and optimization data from FinQA train/dev only", "Test sets are never seen — no leakage."),
    ("DSPy metric = our scorer", "Optimizers maximize exactly the metric we report."),
    ("TextGrad compared with zero-shot CoT", "The only difference is the optimized system prompt."),
    ("VPSC sample 0 = the greedy PoT call; PoT-SC reuses VPSC's 5 programs", "The ablation isolates verification exactly at zero extra cost."),
    ("Rule-based error taxonomy", "Transparent and reproducible (an LLM judge would add its own errors)."),
]

STRATEGY_ROWS = [
    ["Direct", "Answer line only", "1", "no", "'Answer:' line"],
    ["CoT zero-shot " + cite("zscot"), "Think step by step", "1", "no", "'Answer:' line"],
    ["CoT few-shot " + cite("cot"), "3 worked FinQA-train examples", "1", "yes", "'Answer:' line"],
    ["Decomposition " + cite("eedp"), "Knowledge → Extract → Decompose → Answer", "1", "yes", "'Answer:' line"],
    ["Program-of-Thought " + cite("pot"), "Python with variable <code>ans</code>; one repair on error", "1–2", "yes", "sandbox <code>ans</code>"],
    ["CoT Self-Consistency " + cite("sc"), "5 few-shot CoT samples (1 greedy + 4 at T = 0.7), majority vote", "5", "yes", "vote"],
    ["PoT Self-Consistency (ablation)", "5 programs (1 greedy + 4 at T = 0.7), vote", "5", "yes", "vote"],
    ["<b>VPSC (ours)</b>", "Same 5 programs; vote only over grounded programs", "5", "yes", "verified vote"],
    ["DSPy BootstrapFewShot " + cite("dspy"), "Compiled CoT program, self-generated demos", "1", "auto", "DSPy field"],
    ["DSPy MIPROv2 " + cite("mipro"), "Optimized instruction + demos", "1", "auto", "DSPy field"],
    ["TextGrad " + cite("textgrad"), "Zero-shot CoT with optimized system prompt", "1", "no", "'Answer:' line"],
]

ERROR_ROWS = [
    ["no_answer", "No parsable answer in the output"], ["execution_error", "PoT code failed even after one repair"],
    ["sign_error", "Right magnitude, wrong sign (increase vs decrease)"], ["scale_error", "Off by a unit factor: 10², 10³, 10⁵ (lakh), 10⁶, 10⁷ (crore), 10⁹"],
    ["rounding_near_miss", "Within 5% but outside the 0.5% tolerance"], ["no_work_shown", "Wrong, with ≤ 1 number in the output (nothing to diagnose)"],
    ["evidence_error", "At least one gold operand never appears in the model's work"], ["reasoning_error", "All gold operands appear, but the formula or arithmetic is wrong"],
]


def indian_rows():
    rs = [json.loads(l) for l in open(ROOT / "data/indian/indian_set.jsonl")]
    return rs


def verification_summary():
    rows = list(csv.DictReader(open(ROOT / "results/indian_verification.csv")))
    ok_ops = sum(r["all_operands_on_cited_pages"] == "yes" for r in rows)
    ok_gold = sum(r["gold_matches"] == "yes" for r in rows)
    return len(rows), ok_ops, ok_gold


def stats_table(cls="t"):
    st = data.dataset_stats()
    keep = ["finqa test (full)", "tatqa test (full)", "indian test (full)", "finqa test sample n=100", "tatqa test sample n=100",
            "finqa perturbed (from the n=100 sample)", "finqa train (full)", "finqa dev (full)"]
    names = {"finqa test (full)": "FinQA test (full)", "tatqa test (full)": "TAT-QA test, arithmetic (full)", "indian test (full)": "Indian set (ours)",
             "finqa test sample n=100": "FinQA test sample (n=100)", "tatqa test sample n=100": "TAT-QA test sample (n=100)",
             "finqa perturbed (from the n=100 sample)": "FinQA perturbed (from the sample)", "finqa train (full)": "FinQA train (few-shot / optimization)",
             "finqa dev (full)": "FinQA dev (optimization validation)"}
    st = st.set_index("set")
    rows = [[names[k]] + [st.loc[k, c] for c in ["questions", "1 step", "2 steps", "3+ steps", "table", "text", "table-text", "mean table rows"]] for k in keep]
    return table(["Set", "Questions", "1 step", "2 steps", "3+ steps", "Table", "Text", "Table+text", "Mean table rows"], rows,
                 num_cols=range(1, 9), cls=cls)


def prelim_table(cls="t"):
    rows = []
    for s in data.MAIN_ORDER:
        r = [data.strategy_label(s)]
        for d in data.DATASETS:
            c = data.cell(d, data.SMALL, s)
            r.append("–" if c is None else (f"{100 * c.accuracy:.0f}" + ("" if data.complete(c, d) else f"<sup>*</sup>")))
        rows.append(r)
    return table(["Strategy (Qwen3-1.7B)", "FinQA", "TAT-QA", "Indian"], rows, num_cols=(1, 2, 3), cls=cls,
                 highlight=lambda i, r: "VPSC" in r[0])


def format_examples():
    return {f: serialize(SMALL_TABLE, f) for f in ["markdown", "json", "html", "text"]}


FINQA_RECORD = """{
  "id": "C/2009/page_248.pdf-4",            # company / year / page of the 10-K
  "pre_text": ["certain mortgage loans citigroup has elected ..."],
  "table": [["in millions of dollars", "december 31 2009", "december 31 2008"],
            ["carrying amount reported on the consolidated balance sheet", "$ 3338", "$ 4273"], ...],
  "post_text": [...],
  "qa": {"question": "what was the percentage change in carrying amount ... from 2008 to 2009?",
         "program": "subtract(3338, 4273), divide(#0, 4273)",
         "exe_ans": -0.21882,
         "gold_inds": {"table_1": "..."}}           # supporting facts
}"""

TATQA_RECORD = """{
  "table": {"table": [["", "Total", "Less than 1 year", ...], ...]},
  "paragraphs": [{"order": 1, "text": "..."}, ...],
  "questions": [{
     "question": "What was the difference in the total between operating lease
                  obligations and Other purchase obligations and commitments?",
     "answer_type": "arithmetic",      # we keep only arithmetic questions
     "derivation": "205.6-167.1",       "answer": 38.5,
     "scale": "million",                "answer_from": "table"}]
}"""


def indian_record():
    r = indian_rows()[0]
    return (f'{{"uid": "{r["uid"]}", "company": "{r["company"]}",\n "source": "{r["source"]}", "page": {r["page"]}, "printed_page": {r["printed_page"]},\n'
            f' "question": "{r["question"][:70]}...",\n "table": [["Particulars (₹ in crore)", "Year ended 31st March 2025", ...],\n'
            f'           ["Revenue from operations", "54,842", "47,114"], ... 18 rows],\n'
            f' "formula": "{r["formula"]}",   # executed in the sandbox\n "gold": {r["gold"]}, "scale": "{r["scale"]}", "verified": false}}')


EXAMPLE_DC = """@dataclass
class Example:                 # one question, any dataset
    uid: str; dataset: str; question: str
    table: list                # rows of cell strings; row 0 = header
    texts: list                # sentences / paragraphs
    gold: float | str          # number or "yes"/"no"
    gold_program: str          # FinQA program / TAT-QA derivation / formula
    n_steps: int               # arithmetic operations needed
    evidence: str              # "table" | "text" | "table-text"
    scale: str                 # "percent", "million", "crore", ...
    gold_facts: list           # e.g. ["table_3", "text_5"]

@dataclass
class Prediction:              # what every strategy returns
    answer: float | str | None; how: str      # answer_line / code / vote ...
    output: str; code: str; trace: dict; error: str
    n_calls: int; prompt_tokens: int; completion_tokens: int
    latency: float; extra: dict              # votes, grounding, agreement"""

def _run_record():
    """A real (abridged) line from a VPSC run file."""
    path = ROOT / "results/runs/finqa_test_n100__ollama-qwen3-1.7b__vpsc__markdown__full.jsonl"
    r = next(x for x in map(json.loads, open(path)) if x["correct"] and x["n_steps"] >= 2)
    keep = ["uid", "dataset", "strategy", "model", "fmt", "context", "gold", "answer", "how", "correct", "exact_match",
            "error_category", "n_calls", "prompt_tokens", "completion_tokens", "latency"]
    short = {k: r[k] for k in keep}
    short["output"] = "```python …```"
    short["answer"] = round(short["answer"], 4)
    short["extra"] = {"votes": [None if v is None else round(v, 4) for v in r["extra"]["votes"]], "grounded": r["extra"]["grounded"], "agreement": r["extra"].get("agreement")}
    return json.dumps(short, ensure_ascii=False).replace(", \"", ",\n \"")


RUN_RECORD = _run_record()


# ------------------------------------------------------------------------------------------
# Slides
# ------------------------------------------------------------------------------------------
def slides():
    n_ver, ok_ops, ok_gold = verification_summary()
    fm = format_examples()
    d = Deck(LABEL)
    d.raw(title_slide("Review 2", "High-level design & data collection"))
    d.add("Recap", "Where we are", '<div class="cols c2"><div class="card"><h3>From Review 1</h3>' + ul([
        "Problem: numerical reasoning over financial tables + text",
        "Compare 6 manual prompting strategies, 3 automated optimizers and our VPSC",
        "Small (1.7B) and larger (8B) local models; cost, robustness, Indian reports",
    ], cls="small") + '</div><div class="card accent"><h3>This review</h3>' + ul([
        "High-level design: architecture, modules, data model, strategy, sandbox, optimizer and retrieval designs",
        "Experimental design and deployment",
        "Data collection: FinQA, TAT-QA, our Indian annual-report set; statistics; quality checks",
        "Implementation status and preliminary results",
    ], cls="small") + "</div></div>")
    d.add("High-level design", "System architecture: six layers", D.architecture(), lead="")
    d.add("High-level design", "End-to-end flow of one question", D.pipeline() +
          '<p class="small" style="margin-top:16px">Every strategy, model and dataset goes through exactly these stages, so differences in results come only from the prompting strategy (or the ablated variable).</p>')
    d.add("High-level design", "Module decomposition", '<div class="dense">' + table(
        ["Module", "Responsibility", "Key interface"], [[f"<code>{m}</code>", r, i] for m, r, i in MODULES[:9]], widths=[17, 53, 30]) + "</div>")
    d.add("High-level design", "Module decomposition (cont.)", '<div class="dense">' + table(
        ["Module", "Responsibility", "Key interface"], [[f"<code>{m}</code>", r, i] for m, r, i in MODULES[9:]], widths=[20, 50, 30]) + "</div>")
    d.add("Data model", "Core data structures and the run record",
          f'<div class="cols c2"><div class="qbox" style="font-size:11.5px;white-space:pre">{esc(EXAMPLE_DC)}</div><div><p class="small"><b>One JSON line per question per run</b> (results/runs/*.jsonl), appended as soon as it is answered — runs are resumable and fully auditable:</p>'
          f'<div class="qbox" style="font-size:12.5px">{esc(RUN_RECORD)}</div></div></div>')
    d.add("Strategy design", "Eleven prompting strategies behind one interface", '<div class="dense">' + table(
        ["Strategy", "What the prompt asks for", "LLM calls", "Few-shot", "Answer from"], STRATEGY_ROWS, widths=[25, 43, 9, 9, 14]) + "</div>")
    d.add("Prompt design", "Prompt anatomy (shared by all hand-written strategies)",
          f'<div class="cols c2"><div><p class="small"><b>System</b></p><div class="qbox">{esc(SYSTEM_PROMPT)}</div>'
          f'<p class="small" style="margin-top:10px"><b>Answer-format rules</b> (text strategies)</p><div class="qbox" style="font-size:13px">{esc(ANSWER_FORMAT)}</div></div>'
          f'<div><p class="small"><b>Program-of-Thought instruction</b></p><div class="qbox" style="font-size:13px">{esc(INSTRUCTIONS["pot"])}</div>'
          f'<p class="small" style="margin-top:10px"><b>Repair prompt</b> (after a sandbox error)</p><div class="qbox" style="font-size:13px">{esc(REPAIR_PROMPT)}</div>'
          '<p class="note" style="margin-top:10px">Few-shot: 3 real FinQA <i>train</i> questions, written in the same table format as the test question, shown as earlier user/assistant turns.</p></div></div>')
    d.add("Our method", "VPSC: Verified Program Self-Consistency", D.vpsc() + '<div class="cols c3" style="margin-top:8px">'
          '<div class="card"><h3>Why</h3><p>Programs make arithmetic exact; the remaining errors come from <i>wrong numbers</i> copied or invented by the model.</p></div>'
          '<div class="card"><h3>Grounding check</h3><p>Parse the program (AST); every numeric literal must appear in the report, allowing ×100/×1000 rescaling, small counts, years and unit constants.</p></div>'
          '<div class="card accent"><h3>Controlled ablation</h3><p>PoT Self-Consistency votes over the <i>same</i> 5 programs without the check → isolates the effect of verification exactly.</p></div></div>')
    d.add("Security design", "Running model-written code safely", D.sandbox() + '<div class="cols c2" style="margin-top:14px">' + ul([
        "Threat: generated code could read files, open sockets, loop forever or exhaust memory.",
        "Defence in depth: static AST rules <i>and</i> a fresh isolated interpreter <i>and</i> builtin whitelist <i>and</i> CPU / wall-clock limits.",
    ], cls="small") + ul([
        "Output is data only: JSON with <code>ans</code> and the numeric variables (the calculation trace shown in the app).",
        "Covered by unit tests (<code>tests/test_sandbox.py</code>): forbidden imports, dunder access, infinite loops.",
    ], cls="small") + "</div>")
    d.add("Optimization design", "Automated prompt optimization: DSPy and TextGrad", D.optimizers() +
          '<p class="note" style="margin-top:4px">Optimization uses only FinQA train (50 / 40 questions) and dev (40 / 30 questions); the compiled artifacts are then evaluated on all three test sets exactly like the manual strategies, and their one-time cost (calls, tokens, minutes) is recorded.</p>')
    d.add("Retrieval design", "Hybrid evidence retrieval (optional context mode)", '<div class="cols c2"><div>' + ul([
        "Page → evidence units: one per table row (as text) and one per sentence; ids follow FinQA (<code>table_i</code>, <code>text_j</code>).",
        f"Lexical: BM25 {cite('bm25')}. Semantic: all-MiniLM-L6-v2 {cite('sbert')} + FAISS inner-product index {cite('faiss')}.",
        f"Fusion: Reciprocal Rank Fusion {cite('rrf')}, k = 60.",
        "Context = header + top-k units in document order.",
    ], cls="small") + f'</div><div>{img("build/fig/retrieval_recall.png", "width:100%")}<p class="note">Recall of gold evidence on the full test sets (no LLM involved).</p></div></div>')
    d.add("Evaluation design", "Scoring rule and error taxonomy", '<div class="cols c2"><div class="card accent"><h3>Scoring (answers.score)</h3>' + ul([
        "Correct if within <b>0.5%</b> of gold, or equal to gold rounded to gold's precision.",
        "Percentage questions: 12.5 and 0.125 both accepted (FinQA stores fractions, TAT-QA percents).",
        "Also reported: accuracy at 1%, exact match (2 d.p.), token F1, format- and code-failure rates.",
        "Parser handles ₹/$, 1,00,000 grouping, (bracket) negatives, %, crore/lakh/million words.",
    ], cls="small") + '</div><div class="dense">' + table(["Error category", "Rule"], [[f"<code>{a}</code>", b] for a, b in ERROR_ROWS], widths=[34, 66]) + "</div></div>")
    d.add("Experimental design", "Variables, controls and statistics", '<div class="dense">' + table(
        ["Kind", "Variable", "Values"],
        [["Independent", "Prompting strategy", "6 manual + PoT-SC + VPSC + DSPy Bootstrap + DSPy MIPROv2 + TextGrad"],
         ["Independent", "Model", "Qwen3-1.7B, Qwen3-8B (4-bit, Ollama)"],
         ["Independent", "Dataset", "FinQA (100), TAT-QA arithmetic (100), Indian set (44)"],
         ["Ablation", "Table format · context · thinking · numbers", "Markdown/JSON/HTML/text · full vs top-5 retrieved · thinking on/off · original vs perturbed"],
         ["Dependent", "Quality", "Execution accuracy, accuracy@1%, exact match, F1, format/code failures"],
         ["Dependent", "Cost", "LLM calls, prompt/completion tokens, tokens per correct answer, latency, one-time optimization cost"],
         ["Controlled", "Everything else", "Same questions (seed 42), scorer, temperature 0 (except sampling), answer-format rules, worked examples"],
         ["Statistics", "Uncertainty / significance", "95% bootstrap CI (2,000 resamples); exact McNemar vs few-shot CoT; Holm correction"]], widths=[14, 26, 60]) + "</div>")
    d.add("Deployment", "Deployment view", D.deployment() + '<p class="note" style="margin-top:10px">Two Ollama servers so interactive questions in the web app never queue behind the long experiment runs. All model responses are cached, so any run can be stopped and resumed.</p>')
    d.add("Web app design", "Interaction design: one ‘Ask’ request", D.sequence())
    d.section("Data collection", "Three datasets, one format", "FinQA and TAT-QA (public benchmarks) plus a new test set of 44 questions we built from four Indian annual reports.")
    d.add("Data sources", "Datasets used", table(
        ["Dataset", "Source", "Size (full)", "Used for"],
        [["<b>FinQA</b> " + cite("finqa"), "GitHub czyssrs/FinQA (JSON); S&amp;P 500 earnings reports", "6,251 / 883 / 1,147 (train / dev / test)", "Test sample n = 100; train → few-shot examples &amp; optimization; dev → optimizer validation"],
         ["<b>TAT-QA</b> " + cite("tatqa"), "GitHub NExTplusplus/TAT-QA (JSON); annual reports", "13,215 / 1,668 / 1,663 questions (699 arithmetic in test)", "Arithmetic test sample n = 100"],
         ["<b>Indian set (ours)</b>", "Official PDFs: Titan, Asian Paints, Marico, Pidilite (FY2023-24 / 2024-25)", "44 questions, 4 companies, 7 statement pages", "Generalization test (all 44)"],
         ["<b>FinQA-perturbed (ours)</b>", "Generated from the FinQA sample with the gold programs", "88 of 100 questions", "Memorization / robustness test"]],
        widths=[18, 32, 22, 28]))
    d.add("Public benchmarks", "What a FinQA and a TAT-QA record look like",
          f'<div class="cols c2"><div><p class="small"><b>FinQA</b> (train example used as a worked example)</p><div class="qbox" style="font-size:12.5px">{esc(FINQA_RECORD)}</div></div>'
          f'<div><p class="small"><b>TAT-QA</b> (test, arithmetic)</p><div class="qbox" style="font-size:12.5px">{esc(TATQA_RECORD)}</div>'
          '<p class="note" style="margin-top:8px">Both are converted by <code>data.py</code> into the same <code>Example</code>: question, table, texts, gold, program/derivation, number of steps, evidence type, scale, gold evidence ids.</p></div></div>')
    d.add("Indian set", "Why build an Indian annual-report test set?", '<div class="cols c2"><div>' + ul([
        f"The main benchmarks use US filings; recent Indian benchmarks (2026) cover filing look-up {cite('indfin')} and regulatory text {cite('indiafin')} — not multi-step calculation.",
        "<b>₹ crore and lakh</b>: 1 crore = 100 lakh = 10 million; models must convert units correctly.",
        "<b>Indian digit grouping</b> (1,00,000) and <b>bracketed negatives</b> “(6,537)”.",
        "Ind AS statement layouts; standalone vs consolidated statements; 10-year highlight tables.",
        "Questions are new (written by us) over reports published in 2024–25, so the question–answer pairs cannot have been memorized.",
    ], cls="small") + "</div><div>" + table(["Company", "Document", "Pages used"], [
        ["Titan Company", "Annual Report 2024-25", "P&amp;L (PDF p. 275), balance sheet (p. 274)"],
        ["Asian Paints", "Financial statements, AR 2023-24", "P&amp;L (p. 12), balance sheet (p. 11)"],
        ["Marico", "Integrated Annual Report FY25", "Consolidated P&amp;L + BS (p. 170), 10-year highlights (p. 253)"],
        ["Pidilite Industries", "Consolidated FS 2024-25", "P&amp;L + balance sheet (p. 5)"]]) + "</div></div>")
    d.add("Indian set", "Collection pipeline and quality checks", D.indian_pipeline() + '<div class="cols c3" style="margin-top:8px">'
          '<div class="card"><h3>Gold answers are computed</h3><p>Each question has a Python formula, e.g. <code>(54842 - 47114) / 47114 * 100</code>; the gold is its sandboxed result — never typed by hand.</p></div>'
          '<div class="card"><h3>Built-in checks</h3><p>Build fails unless all 366 transcribed cells occur on their PDF page, and every formula number occurs in the question\'s table/text.</p></div>'
          f'<div class="card accent"><h3>Independent re-check</h3><p>For this review we re-extracted every cited page with pdfplumber: <b>{ok_ops}/{n_ver}</b> questions have all operands on the cited page (correct row and year column), and <b>{ok_gold}/{n_ver}</b> golds recompute exactly.</p></div></div>')
    d.add("Indian set", "Composition of the 44 questions", f'{img("build/fig/indian_types.png", "width:100%")}' + '<div class="cols c2" style="margin-top:10px">' + ul([
        "Reasoning steps: 15 one-step, 13 two-step, 16 with three or more.",
        "Formulas: growth, margins, effective tax rate, current/quick ratio, debt-to-equity, ROE, interest coverage, CAGR, 5-year average, dividend payout.",
    ], cls="small") + ul([
        "Includes negative answers (profit fell 5.90%; cash fell 37.12%), a 9-year CAGR and unit conversions (crore → lakh / million / billion).",
        "Two questions need a value from the text (return on average equity).",
    ], cls="small") + "</div>")
    d.add("Data statistics", "Dataset statistics", '<div class="dense">' + stats_table() + "</div>" + f'{img("build/fig/data_composition.png", "width:92%")}')
    d.add("Pre-processing", "Table normalization and the four serializations", f'''<div class="cols c2"><div>
        <p class="small"><b>Markdown</b> (default)</p><div class="qbox" style="font-size:13px">{esc(fm["markdown"])}</div>
        <p class="small" style="margin-top:8px"><b>JSON records</b></p><div class="qbox" style="font-size:13px">{esc(fm["json"])}</div></div><div>
        <p class="small"><b>HTML</b></p><div class="qbox" style="font-size:13px">{esc(fm["html"])}</div>
        <p class="small" style="margin-top:8px"><b>Row-wise text</b> (also the retrieval unit)</p><div class="qbox" style="font-size:13px">{esc(fm["text"])}</div></div></div>
        <p class="note" style="margin-top:8px">Rows are padded to equal width, cells stripped, empty/duplicate headers named; the format is an ablation variable {cite("tablellm")}.</p>''')
    d.add("Derived data", "Numerically perturbed FinQA (memorization test)", '<div class="cols c2"><div>' + ul([
        "For each sampled FinQA question, every operand of the gold program is scaled by a random factor in [0.7, 0.9] ∪ [1.1, 1.3] (seed 42), keeping its decimals.",
        "All occurrences in the table and text are replaced in one pass; the gold answer is <b>recomputed by executing the gold program</b>.",
        "Questions are skipped if an operand is a year, a percentage, negative, or not written verbatim in the report → <b>88 of 100</b> usable.",
        f"Idea follows GSM-Symbolic {cite('gsmsym')}: a model that reasons should not care which numbers appear.",
    ], cls="small") + '</div><div class="card"><h3>Example (STT 2009, p. 127)</h3><p><i>by how much more is the net gains from sales of available-for-sale securities in 2009 compare to 2008?</i></p>'
          '<p><b>Original:</b> <code>subtract(368, 68)</code> = 300<br><b>Perturbed:</b> <code>subtract(272, 82)</code> = 190</p>'
          '<p class="note">Same question text, same table layout — only the numbers change.</p></div></div>')
    d.add("Implementation status", "What is built and tested", '<div class="cols c2"><div class="card accent"><h3>Done</h3>' + ul([
        f"Library: {data.code_stats()[0]} modules, ~{round(data.code_stats()[1], -2):,} lines; {data.code_stats()[2]} automated tests passing (scoring, sandbox, FinQA programs, tables, prompts, perturbation, taxonomy, statistics, retrieval, every app page).",
        "All three datasets loaded and described; Indian set built and re-verified.",
        "Retrieval recall evaluated on full test sets.",
        "Qwen3-1.7B: main grid, VPSC and PoT-SC on FinQA / TAT-QA / Indian set.",
        "Streamlit app with 9 pages.",
    ], cls="small") + '</div><div class="card warn"><h3>In progress → Review 3</h3>' + ul([
        "Perturbation test, DSPy / TextGrad optimization, table-format, retrieval and thinking ablations (1.7B).",
        "Full grid with Qwen3-8B.",
        "Final analysis, IEEE report, demo.",
    ], cls="small") + "</div></div>")
    d.add("Preliminary results", "First numbers (Qwen3-1.7B, execution accuracy %)", '<div class="cols c46"><div class="dense">' + prelim_table() +
          '<p class="note"><sup>*</sup> run still in progress. n = 100 / 100 / 44.</p></div><div>' + ul([
              "Direct answering fails (≤ 11%): the model needs to show work.",
              "Any reasoning strategy lifts a 1.7B model to ~45–75%.",
              "Program-based strategies are strongest on FinQA and the Indian set.",
              "Final analysis with significance tests and the 8B model at Review 3.",
          ], cls="small") + "</div></div>")
    d.raw('<section class="slide section-slide"><div class="kicker">Review 2</div><h2>Thank you — questions?</h2>'
          '<p>Next: complete experiments (optimization, ablations, Qwen3-8B), final analysis and live demo at Review 3.</p></section>')
    return page(f"{LABEL} slides", SLIDE_CSS, d.html())


# ------------------------------------------------------------------------------------------
# Report
# ------------------------------------------------------------------------------------------
def report():
    n_ver, ok_ops, ok_gold = verification_summary()
    fm = format_examples()
    ind = indian_rows()
    ind_table = table(["ID", "Question (abridged)", "Formula", "Gold", "Unit"],
                      [[r["uid"], esc(r["question"][:88] + ("…" if len(r["question"]) > 88 else "")), f'<code>{esc(r["formula"])}</code>',
                        str(r["gold"]), r.get("scale") or "–"] for r in ind], widths=[9, 47, 27, 10, 7])
    body = cover("Review 2", "High-Level Design &amp; Data Collection", "Architecture, module and interface design, experimental design, datasets, collection process and data quality") + f"""
<h1 class="doc-title">Contents</h1>
<ol class="toc"><li>Overview</li><li>Design goals and constraints</li><li>System architecture</li><li>Module design</li><li>Data design</li>
<li>Strategy and prompt design (including VPSC)</li><li>Sandbox security design</li><li>Automated optimization design</li><li>Retrieval design</li>
<li>Evaluation design</li><li>Experimental design</li><li>Deployment and web-application design</li><li>Data collection</li><li>Data quality and verification</li>
<li>Implementation status and preliminary results</li><li>References</li><li>Appendix A: the 44 Indian-set questions</li></ol>

<h2>1. Overview</h2>
<p>FinReason answers numerical questions over financial report pages with Large Language Models and measures how prompting strategies and automated prompt
optimization change accuracy, cost and reliability. This document presents the high-level design of the system and the data-collection work: the public
benchmarks FinQA {cite("finqa")} and TAT-QA {cite("tatqa")}, and a new test set of 44 questions built from four Indian annual reports.</p>

<h2>2. Design goals and constraints</h2>
<ul>
<li><b>Controlled comparison:</b> every strategy must see the same questions, context, scorer and model; only the prompt may differ.</li>
<li><b>Reproducibility:</b> fixed seeds, pinned library versions, deterministic decoding (temperature 0 except for sampling strategies), cached responses.</li>
<li><b>Auditability:</b> every answer must be traceable to its prompt, raw output, generated code, variable trace and evidence rows.</li>
<li><b>Safety:</b> model-generated code is untrusted and must run isolated.</li>
<li><b>Runs on a laptop:</b> local models (Ollama, 4-bit Qwen3 {cite("qwen3")}) on an Apple M4 with 24 GB; long experiment queues must be resumable.</li>
<li><b>Provider-agnostic:</b> the same code must run API models (OpenAI-compatible providers, Anthropic) for future comparison.</li>
<li><b>No test leakage:</b> few-shot examples and all optimization data come from FinQA train/dev only.</li></ul>

<h2>3. System architecture</h2>
<p>The system is organized in six layers (Fig. 1). The <b>data layer</b> loads the three datasets into one common <code>Example</code> structure. The
<b>context layer</b> serializes tables and optionally retrieves the most relevant rows and sentences. The <b>reasoning layer</b> holds the prompt library,
the strategy engine, the LLM client, the code sandbox and the grounding verifier. The <b>optimization layer</b> compiles DSPy programs and TextGrad-optimized
prompts into artifacts that the strategy engine can load like any other strategy. The <b>evaluation layer</b> parses and scores answers, classifies
errors, computes statistics and generates perturbed questions. The <b>presentation layer</b> stores one JSON line per answered question and turns
the runs into tables, figures and an interactive web application.</p>
<figure>{D.architecture()}<div class="caption">Fig. 1. Layered architecture of FinReason.</div></figure>
<p>Fig. 2 shows how a single question flows through the system. The same eight stages are used by the experiment runner and by the web application.</p>
<figure>{D.pipeline()}<div class="caption">Fig. 2. End-to-end flow of one question.</div></figure>
<h3>3.1 Key design decisions</h3>
{table(["Decision", "Reason"], [[a, b] for a, b in DECISIONS], widths=[45, 55])}

<h2>4. Module design</h2>
<p>The library <code>finreason/</code> contains one module per responsibility; command-line scripts and the web app only compose these modules.</p>
{table(["Module", "Responsibility", "Key interface"], [[f"<code>{m}</code>", r, i] for m, r, i in MODULES], widths=[20, 52, 28])}

<h2>5. Data design</h2>
<p>Two data classes define the contract between modules. Every loader produces <code>Example</code> objects and every strategy returns a
<code>Prediction</code>; <code>experiment.evaluate_example</code> flattens both into one JSON record that is appended to the run file as soon as the
question is answered, which makes runs resumable (already-answered question IDs are skipped).</p>
<pre>{esc(EXAMPLE_DC)}</pre>
<p>Run files are named by every experimental variable, e.g. <code>finqa_test_n100__ollama-qwen3-1.7b__vpsc__markdown__full.jsonl</code>. A record:</p>
<pre>{esc(RUN_RECORD)}</pre>
<p>Model responses are cached in SQLite (<code>~/.cache/finreason/llm_cache.sqlite</code>) under a SHA-256 key of (model, thinking flag, max tokens,
messages, temperature, sample id); write-ahead logging lets the experiment runner and the web app use the cache concurrently. Optimization outputs
are stored as JSON artifacts (<code>artifacts/dspy_*.json</code> with a <code>.meta.json</code> describing cost and chosen demos; <code>artifacts/textgrad_*.json</code>
with the best prompt and the full optimization history).</p>

<h2>6. Strategy and prompt design</h2>
<p>All strategies share the signature <code>strategy(llm, example, context, fmt) → Prediction</code>, so the runner, the analysis and the web app treat
them identically. Table 1 lists them.</p>
<p class="tcaption">Table 1. Prompting strategies.</p>
{table(["Strategy", "What the prompt asks for", "Calls", "Few-shot", "Answer from"], STRATEGY_ROWS, widths=[25, 43, 8, 9, 15])}
<h3>6.1 Prompt anatomy</h3>
<p>Text strategies use one system prompt, a strategy instruction and the same answer-format rules; Program-of-Thought replaces the rules with a code
instruction. Few-shot strategies prepend three worked examples — real FinQA <i>train</i> questions on a percentage change, an average share price from text,
and a share computed across units (billion → million) — as earlier user/assistant turns, serialized in the same table format as the test question.
A unit test checks that every worked example itself evaluates to its gold answer.</p>
<pre>SYSTEM: {esc(SYSTEM_PROMPT)}

ANSWER FORMAT:
{esc(ANSWER_FORMAT)}

DECOMPOSITION: {esc(INSTRUCTIONS["decomp"])}

PROGRAM-OF-THOUGHT: {esc(INSTRUCTIONS["pot"])}

REPAIR: {esc(REPAIR_PROMPT)}</pre>
<h3>6.2 Answer extraction</h3>
<p>The parser removes Markdown/LaTeX decoration and reads, in order of preference, the last <code>Answer:</code> line, a <code>\\boxed{{}}</code> expression, or
the last number in the output (counted as a format failure). Numbers may carry currency symbols (₹, $, Rs, INR), Indian or Western digit grouping,
bracketed negatives, percent signs and scale words (thousand, lakh, million, crore, billion).</p>
<h3>6.3 Verified Program Self-Consistency (VPSC)</h3>
<p>Our error analysis of preliminary runs showed that, once arithmetic is delegated to code, most remaining errors are <i>evidence errors</i>: the model
uses a number that is not the correct one from the report. VPSC (Fig. 3) samples five programs — the greedy program (identical to the Program-of-Thought
call, so it is served from the cache) and four at temperature 0.7 — and executes each in the sandbox. A program is <b>grounded</b> if every numeric
literal in its abstract syntax tree occurs in the report, allowing small integers (0–12), unit constants (100, 1,000, 10<sup>5</sup>, 10<sup>6</sup>,
10<sup>7</sup>, 10<sup>9</sup>), years (1900–2100), and the report's numbers rescaled by ×100, ×1000, ÷100 or ÷1000. The answer is the majority vote over
executed, grounded programs; if no program is grounded, all executed programs vote. Confidence is the share of the five votes the winner received.
The ablation, PoT Self-Consistency, votes over the same five programs without the check, so VPSC − PoT-SC measures the effect of verification alone,
and VPSC vs CoT Self-Consistency compares equal budgets (five calls).</p>
<figure>{D.vpsc()}<div class="caption">Fig. 3. VPSC. The grounding check rejects programs that use numbers not found in the report.</div></figure>

<h2>7. Sandbox security design</h2>
<p>Generated code is untrusted. The sandbox applies four independent layers (Fig. 4): (1) a static AST check that allows only <code>import math</code> and rejects
names such as <code>open</code>, <code>eval</code>, <code>exec</code>, <code>os</code>, <code>sys</code> and any dunder attribute; (2) execution in a fresh
<code>python -I</code> process (isolated mode: no user site-packages, no environment variables), with the code passed on standard input; (3) a whitelist of
safe builtins with <code>print</code> disabled; and (4) a CPU-time resource limit plus a 5-second wall-clock timeout. The child process returns only JSON: the
value of <code>ans</code> and all numeric variables, which become the calculation trace shown to the user. On failure, Program-of-Thought shows the error message to
the model once and runs the repaired code.</p>
<figure>{D.sandbox()}<div class="caption">Fig. 4. Sandbox layers.</div></figure>

<h2>8. Automated optimization design</h2>
<p><b>DSPy</b> {cite("dspy")}: a <code>FinancialQA</code> signature (inputs: context, question; output: answer) with the same answer rules as the manual prompts,
wrapped in <code>dspy.ChainOfThought</code>. The optimization metric is our own scorer, so the optimizer maximizes exactly what we report.
<b>BootstrapFewShot</b> runs the program on 50 FinQA-train questions and keeps up to three traces the metric marks correct as demonstrations
(only self-generated demos, <code>max_labeled_demos = 0</code>). <b>MIPROv2</b> {cite("mipro")} (light setting) proposes instructions and demo sets and searches over them
scoring every trial on 40 FinQA-dev questions. <b>TextGrad</b> {cite("textgrad")}: the system prompt of zero-shot CoT is a trainable variable; for each batch of six
training questions, only wrongly answered questions produce a loss (“the correct answer is …; identify which step went wrong and which general instruction
would have prevented it”); the optimizer model writes the textual gradient and rewrites the prompt under two constraints (keep the <code>Answer:</code> line; stay
general). After each of six steps the candidate is kept only if accuracy on 40 FinQA-dev questions does not drop. For the 1.7B model the feedback is written by
the 8B model.</p>
<figure>{D.optimizers()}<div class="caption">Fig. 5. DSPy compilation (left) and the TextGrad loop (right).</div></figure>

<h2>9. Retrieval design</h2>
<p>By default the model sees the whole page. In retrieval mode, the page is split into evidence units — one per table row (rendered as “label: column =
value; …”) and one per sentence — and ranked by BM25 {cite("bm25")} and by cosine similarity of all-MiniLM-L6-v2 embeddings {cite("sbert")} in a FAISS
inner-product index {cite("faiss")}; the two rankings are fused with Reciprocal Rank Fusion {cite("rrf")} (k = 60). The context keeps the table header plus the top-k
units in document order. Fig. 6 shows recall of the gold evidence units on the full test sets.</p>
<figure>{img("build/fig/retrieval_recall.png", "width:92%")}<div class="caption">Fig. 6. Retrieval recall@k on the full FinQA (1,147) and TAT-QA arithmetic (696 with gold evidence) test sets.</div></figure>

<h2>10. Evaluation design</h2>
<p><b>Execution accuracy</b> is the primary metric: a numeric prediction is correct if it is within 0.5% of the gold value or equals the gold value rounded to
the number of decimals the gold is written with; for percentage questions the ×100 and ÷100 forms are also accepted. Yes/no answers must match exactly.
We also report accuracy at 1% tolerance, exact match after rounding both to two decimals, TAT-QA-style token F1, format-failure rate (no
<code>Answer:</code> line) and code-failure rate. Cost metrics are LLM calls, prompt and completion tokens, tokens per correct answer and latency per
question; optimizers additionally report their one-time compile cost. Each wrong answer receives exactly one error category (Table 2).</p>
<p class="tcaption">Table 2. Error taxonomy (checked in this order).</p>
{table(["Category", "Rule"], [[f"<code>{a}</code>", b] for a, b in ERROR_ROWS], widths=[28, 72])}
<p>Uncertainty is reported as 95% percentile-bootstrap confidence intervals {cite("bootstrap")} (2,000 resamples). Strategies are compared with few-shot CoT on
the same questions using the exact McNemar test {cite("mcnemar")}, with Holm correction {cite("holm")} within each setting, as recommended for NLP {cite("dror")}.</p>

<h2>11. Experimental design</h2>
{table(["Kind", "Variable", "Values"],
       [["Independent", "Prompting strategy", "direct, cot_zs, cot_fs, decomp_fs, pot_fs, sc_cot, pot_sc, vpsc, DSPy-Bootstrap, DSPy-MIPROv2, TextGrad"],
        ["Independent", "Model", "Qwen3-1.7B, Qwen3-8B (local, 4-bit, Ollama)"],
        ["Independent", "Dataset", "FinQA test sample (100), TAT-QA arithmetic sample (100), Indian set (44)"],
        ["Ablation", "Table format", "Markdown (default), JSON, HTML, row text — few-shot CoT"],
        ["Ablation", "Context", "Full page (default) vs top-5 retrieved units — Program-of-Thought"],
        ["Ablation", "Thinking mode", "Off (default) vs on — zero-shot CoT, 1.7B"],
        ["Ablation", "Perturbation", "Original vs perturbed FinQA (88 questions) — CoT, PoT, VPSC"],
        ["Dependent", "Quality and cost", "Accuracy (+CI), accuracy@1%, EM, F1, failures; calls, tokens, latency, optimization cost"],
        ["Controlled", "Everything else", "Questions (seed 42), scorer, decoding, answer rules, worked examples, hardware"]], widths=[14, 20, 66])}
<p>Stages, in the order of the experiment queue (<code>scripts/run_all.sh</code>): main grid (6 manual strategies × 2 models × FinQA, TAT-QA); VPSC and PoT-SC;
Indian set; perturbation; DSPy and TextGrad optimization and evaluation; ablations; then the same for the 8B model; finally the analysis. Retrieval recall is
measured separately without any LLM.</p>

<h2>12. Deployment and web-application design</h2>
<figure>{D.deployment()}<div class="caption">Fig. 7. Deployment view.</div></figure>
<p>The web application (Streamlit) has nine pages. <b>Overview</b> shows the headline findings, the literature gaps and a checklist of every claim. <b>Ask</b> runs the full pipeline live on a dataset question, a pasted table or a page of an uploaded
PDF, and shows the pipeline stages, an answer card with confidence, highlighted evidence rows, the generated code and variable trace, the votes (with grounding)
and the exact prompt. <b>Compare</b> runs several strategies on one question side by side with token costs. <b>Results</b> shows interactive charts,
significance tests and figures from the experiment runs. <b>Optimization</b> and <b>Robustness</b> show the DSPy / TextGrad artifacts, the perturbation
test and the ablations. <b>Errors</b> lists every wrong answer by strategy and category with its reasoning, <b>Data</b> shows each Indian question beside its PDF page,
and <b>Method</b> explains the method. Fig. 8 shows the sequence of one request.</p>
<figure>{D.sequence()}<div class="caption">Fig. 8. Sequence of an ‘Ask’ request with the VPSC strategy.</div></figure>

<h2 class="newpage">13. Data collection</h2>
<h3>13.1 Public benchmarks</h3>
<p><b>FinQA</b> {cite("finqa")} was downloaded from the authors' GitHub repository (<code>czyssrs/FinQA</code>, files <code>train/dev/test.json</code>): 6,251 / 883 / 1,147
questions over earnings reports of S&amp;P 500 companies. Each record holds the pre-text, table, post-text, question, gold program, executed answer and the gold
supporting facts (example below). We use a fixed random sample of 100 test questions (seed 42) for every strategy, the train split for the three worked
examples and for optimization, and the dev split for optimizer validation.</p>
<pre>{esc(FINQA_RECORD)}</pre>
<p><b>TAT-QA</b> {cite("tatqa")} was downloaded from <code>NExTplusplus/TAT-QA</code> (<code>tatqa_dataset_train/dev/test_gold.json</code>): 2,201 / 278 / 277 contexts
with 13,215 / 1,668 / 1,663 questions. We keep only <i>arithmetic</i> questions with a numeric answer (699 in the test split), store the derivation, scale and
answer source, map the gold evidence to <code>table_i</code>/<code>text_j</code> identifiers and count reasoning steps from the derivation. A fixed sample of 100 is used.</p>
<pre>{esc(TATQA_RECORD)}</pre>

<h3>13.2 The Indian annual-report set (new)</h3>
<p><b>Motivation.</b> The main benchmarks contain only US filings, and recent Indian financial benchmarks (2026) cover filing look-up {cite("indfin")} and
regulatory text {cite("indiafin")} rather than multi-step calculation. Indian reports express amounts in ₹ crore and lakh (1 crore = 100 lakh = 10 million),
use Indian digit grouping (1,00,000), write negatives in brackets, follow Ind AS layouts and distinguish standalone from consolidated statements. The questions are new
(written by us) over reports published in 2024–25, so the question–answer pairs cannot have been memorized from public benchmarks.</p>
<p><b>Sources.</b> Annual reports downloaded from the companies' official websites:</p>
{table(["Company", "Document", "Pages used (PDF page)"],
       [["Titan Company Ltd", "Annual Report 2024-25", "Standalone P&amp;L (275), balance sheet (274)"],
        ["Asian Paints Ltd", "Financial statements, Integrated Annual Report 2023-24", "Standalone P&amp;L (12), balance sheet (11)"],
        ["Marico Ltd", "Integrated Annual Report FY25", "Consolidated P&amp;L and balance sheet (170), 10-year financial highlights (253)"],
        ["Pidilite Industries Ltd", "Consolidated financial statements 2024-25", "Consolidated P&amp;L and balance sheet (5)"]], widths=[24, 40, 36])}
<p><b>Process</b> (Fig. 9). We located the statement pages, extracted their text, and transcribed the needed rows into tables in
<code>scripts/build_indian_set.py</code>, copying numbers exactly as printed (including brackets and Indian grouping). For each question we wrote a formula in Python
syntax; the gold answer is the formula's result computed in the sandbox, never typed by hand. Two automatic checks make the build fail on any discrepancy:
every transcribed cell (366 in total) must literally occur in the text of its PDF page, and every number in a formula (other than unit and averaging constants)
must occur in the question's table or text. A checklist (<code>data/indian/verification_checklist.csv</code>) lists every question with its PDF page for manual sign-off.</p>
<figure>{D.indian_pipeline()}<div class="caption">Fig. 9. Construction of the Indian set.</div></figure>
<p>A record of the set:</p>
<pre>{esc(indian_record())}</pre>
<p><b>Composition.</b> 44 questions: Titan 13, Asian Paints 12, Marico 12, Pidilite 7; 15 one-step, 13 two-step and 16 with three or more operations;
23 percentages, 8 ratios or ₹ amounts, 5 in ₹ crore, 3 in ₹ lakh, 2 in ₹ billion, 2 in ₹ million and 1 yes/no. The set includes negative answers, a 9-year CAGR,
a 5-year average, unit conversions and two questions that need a value from the text. The full list is in Appendix A.</p>
<figure>{img("build/fig/indian_types.png", "width:90%")}<div class="caption">Fig. 10. Indian set by company and by answer unit.</div></figure>

<h3>13.3 Derived data: numerically perturbed FinQA</h3>
<p>To test memorization (cf. GSM-Symbolic {cite("gsmsym")}), <code>perturb.py</code> rewrites each sampled FinQA question: every literal operand of the gold program
is multiplied by a random factor from [0.7, 0.9] ∪ [1.1, 1.3] (seed 42) with its original number of decimals; all occurrences in the table and text are replaced
in a single pass; and the new gold answer is obtained by executing the rewritten gold program with our FinQA program interpreter. Questions are skipped when an
operand is a year, a percentage or negative, when it does not appear verbatim in the report, or when the program fails — leaving 88 of the 100 questions. Example
(STT 2009, p. 127): <code>subtract(368, 68) = 300</code> becomes <code>subtract(272, 82) = 190</code>.</p>

<h3>13.4 Dataset statistics</h3>
<p class="tcaption">Table 3. Dataset statistics (computed by <code>scripts/dataset_stats.py</code>).</p>
{stats_table()}
<figure>{img("build/fig/data_composition.png", "width:96%")}<div class="caption">Fig. 11. Reasoning steps and evidence source of the evaluated sets.</div></figure>
<p>The FinQA sample is dominated by one- and two-step questions with evidence mostly in the table; TAT-QA's arithmetic sample has more three-plus-step questions
(averages, sums of several items) and more questions that combine table and text; the Indian set has the longest tables (18 rows on average) and the largest share of
multi-step questions. Average context length is about 660 words for FinQA, 315 for TAT-QA and 225 for the Indian set.</p>
<h3>13.5 Pre-processing</h3>
<p>Tables are normalized (rows padded to equal width, cells stripped, empty and repeated header cells given unique names) and serialized in one of four formats,
which is an experimental variable {cite("tablellm")}:</p>
<div class="two"><pre>MARKDOWN
{esc(fm["markdown"])}

ROW TEXT
{esc(fm["text"])}</pre><pre>JSON
{esc(fm["json"])}

HTML
{esc(fm["html"])}</pre></div>

<h2>14. Data quality and verification</h2>
<ul>
<li><b>Indian set — independent re-check (performed for this review).</b> We re-extracted the text of every cited PDF page with pdfplumber and checked, for each
question, that every operand of its formula occurs on the cited page, then inspected the PDF line containing each operand to confirm it is the intended row and year
column, and recomputed the gold answer from the formula. Result: <b>{ok_ops}/{n_ver}</b> questions have all operands on their cited pages and <b>{ok_gold}/{n_ver}</b>
gold answers match exactly (<code>results/indian_verification.csv</code>). Two return-on-equity questions use profit from the P&amp;L page (adjacent to the cited
balance-sheet page), which the question text also states.</li>
<li><b>FinQA gold programs:</b> a unit test re-executes the gold program of all 1,147 FinQA test questions with our interpreter and reproduces every published answer; the three worked examples are tested to produce their gold answers.</li>
<li><b>No leakage:</b> worked examples and optimization data come only from FinQA train/dev; the test samples are fixed by seed and never used for tuning.</li>
<li><b>Known label noise:</b> some FinQA gold answers are themselves wrong (e.g. the direction of a change), which caps reachable accuracy; we keep the official labels.</li>
<li><b>Remaining step:</b> a human sign-off of the verification checklist by a team member (opening each PDF page) before the final report.</li></ul>

<h2>15. Implementation status and preliminary results</h2>
<p>The library (19 modules), scripts, web application and 30 unit tests are implemented and passing. Retrieval recall has been measured, and the Qwen3-1.7B runs of
the main grid, VPSC and its ablation are complete. Table 4 gives preliminary execution accuracies; the full analysis with significance tests, the optimization
results, the ablations and the 8B model will be presented at Review 3.</p>
<p class="tcaption">Table 4. Preliminary execution accuracy (%), Qwen3-1.7B (* = run in progress).</p>
{prelim_table()}

<h2>16. References</h2>
{ref_list_html()}

<h2 class="newpage">Appendix A. The 44 Indian-set questions</h2>
{ind_table}
"""
    return page(f"{LABEL} report", REPORT_CSS, body, running="FinReason · Review 2 · High-level design & data collection")
