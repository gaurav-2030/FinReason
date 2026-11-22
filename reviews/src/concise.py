"""Concise versions of the three reviews: a short deck (one key point per slide) and 2-3 pages of
study notes per review. Numbers come from the experiment runs via data.py / review3.py helpers."""
import data
import diagrams as D
import review3 as R
from common import (NOTES_CSS, SLIDE_CSS_CONCISE, TEAM, Deck, img, notes_head, page, table, title_slide, ul)
from references import cite, ref_list_html

S, L = data.SMALL, data.LARGE
ML, SL, P, acc = data.model_label, data.strategy_label, R.P, R.acc
KEY_REFS = ["finqa", "tatqa", "financebench", "eedp", "cot", "zscot", "sc", "pot", "dspy", "mipro", "textgrad", "gsmsym", "qwen3", "indfin", "indiafin", "verifin", "dcrc", "finreasoning"]
ROLES = ["Problem definition, architecture and integration, results analysis", "Datasets (incl. Indian set), prompting strategies, prompt templates",
         "Code sandbox, scoring, error taxonomy, web app and live demo", "DSPy, TextGrad, VPSC, retrieval, statistics and ablations"]
G, SU, DH, HA = (n for n, _ in TEAM)

# Equal division: every member presents one block per review (about 9 content slides in total) with a mix of
# overview and technical slides. PLAN fixes the slide order and presenter; DIVISION says what to learn and answer.
TITLE_S, THANKS_S = "Title & introductions", "Thank you & Q&A"
PLAN = {
    # Review 1: the first 14 slides (title to "What is new") are divided; references and thank-you are not assigned
    1: [(G, [TITLE_S, "Numerical questions", "LLMs read finance", "Problem statement"]),
        (SU, ["Objectives", "Financial QA benchmarks", "Main and latest papers", "One pipeline"]),
        (HA, ["Our seven prompting strategies", "Text-based strategies", "Code-based strategies"]),
        (DH, ["Optimizing the prompts", "Experimental design", "What is new"]),
        (None, ["Key references", THANKS_S])],
    2: [(G, [TITLE_S, "Six layers", "How one question flows", "Key modules"]),
        (SU, ["Strategies compared", "Three datasets", "How we built and checked it"]),
        (HA, ["VPSC: Verified", "DSPy and TextGrad design", "Scoring rule"]),
        (DH, ["Sandbox: running", "Project status", "First results", THANKS_S])],
}


def plan3():
    """Review 3: 16 content slides, 4 per member, with or without the 8B results."""
    if R.has_model(L):
        return [(SU, [TITLE_S, "What we compared", "Experimental setup", "Accuracy by strategy — Qwen3-1.7B", "Accuracy by strategy — Qwen3-8B"]),
                (G, ["1.7B vs 8B", "Indian annual reports", "Accuracy vs. cost", "Why answers are wrong"]),
                (HA, ["VPSC result", "DSPy and TextGrad", "Memorization check", "What else changes accuracy"]),
                (DH, ["Key findings", "Live demo", "Demo plan", "Conclusion", THANKS_S])]
    return [(SU, [TITLE_S, "What we compared", "Experimental setup", "Experiment status", "Accuracy by strategy"]),
            (G, ["Indian annual reports", "Accuracy vs. cost", "Why answers are wrong", "VPSC result"]),
            (HA, ["DSPy and TextGrad", "Memorization check", "What else changes accuracy", "Key findings"]),
            (DH, ["Live demo", "Demo plan", "Conclusion", "Limitations", THANKS_S])]


DIVISION = {
    1: {G: ("Introduction, the problem, motivation, problem statement (notes §1)", "“The project in one line?”, “Why local models?”"),
        SU: ("Objectives; benchmarks; main papers (FinQA, PoT, EEDP) and latest papers (FinanceReasoning, VeriFin, IndiaFinBench) with gaps; the pipeline (notes §2–4)", "“How are you different from EEDP / VeriFin?”, “Why an Indian set?”"),
        HA: ("The seven strategies: CoT, Self-Consistency, decomposition, PoT, VPSC and their prompts (notes §3–4)", "“How do the strategies differ?”, “How does VPSC work?”"),
        DH: ("DSPy/TextGrad design; experimental design; novelty (notes §4–5)", "“How do you avoid test leakage?”, “What is new?”")},
    2: {G: ("Six layers, flow of a question, key modules (notes §1)", "“Why one common format?”, “Why cache responses?”"),
        SU: ("Strategies; FinQA, TAT-QA; how the Indian set was built and verified (notes §2–3)", "“How do you trust the Indian set?”"),
        HA: ("VPSC design; DSPy and TextGrad design; scoring rule and McNemar (notes §2)", "“How do you prevent test leakage?”, “Why McNemar?”"),
        DH: ("Sandbox (4 layers); project status; first results (notes §2–3)", "“How is model code kept safe?”, “What is done and what is next?”")},
    3: {G: ("Indian results, cost, error analysis, VPSC result (notes §2)", "“Did VPSC beat PoT-SC?”, “What are the main errors?”"),
        SU: ("Recap, setup, experiment status, main results (notes §1)", "“What exactly is the task?”, “Why are the CIs wide?”"),
        HA: ("DSPy/TextGrad, perturbation, ablations incl. thinking mode, key findings (notes §2)", "“Why McNemar?”, “What is the perturbation test?”"),
        DH: ("Web app, live demo, conclusion, limitations (notes §3–4)", "“How is the sandbox safe?”, “What are the limitations?”; runs the demo")},
}


DIVISION_3_WITH_8B = {
    SU: ("Recap, setup, main results for both models (notes §1)", "“What exactly is the task?”, “Why are the CIs wide?”"),
    G: ("1.7B vs 8B, Indian results, cost, error analysis (notes §1–2)", "“Does a bigger model help?”, “What are the main errors?”"),
    HA: ("VPSC result, DSPy/TextGrad, perturbation, ablations incl. thinking mode (notes §2)", "“Did VPSC beat PoT-SC?”, “What is the perturbation test?”"),
    DH: ("Key findings, web app, live demo, conclusion and limitations (notes §2–4)", "“How is the sandbox safe?”, “What are the limitations?”; runs the demo")}


def division_for(review, name):
    if review == 3 and R.has_model(L):
        return DIVISION_3_WITH_8B[name]
    return DIVISION[review][name]


def _ranges(nums):
    out, start = [], None
    for i, n in enumerate(nums):
        if start is None:
            start = n
        if i == len(nums) - 1 or nums[i + 1] != n + 1:
            out.append(f"{start}" if start == n else f"{start}–{n}")
            start = None
    return ", ".join(out)


def counted(review, titles):
    """Slides that count towards a member's share: in Review 1 the title slide is one of the 11 divided slides."""
    skip = ("Thank you & Q&A",) if review == 1 else ("Title & introductions", "Thank you & Q&A")
    return [t for t in titles if t not in skip]


def division_rows(review, deck):
    rows = []
    asg = deck.assignments()
    for name, _ in TEAM:
        mine = [(n, t) for n, t, w in asg if w == name]
        content = counted(review, [t for n, t in mine])
        learn, qs = division_for(review, name)
        rows.append([f"<b>{name}</b>", _ranges([n for n, _ in mine]) + f"<br><span style='color:#5b6678'>{len(content)} slides</span>",
                     "; ".join(content), learn, qs])
    return rows


def division_html(review, deck):
    return ('<h2>Who presents what</h2>' + table(["Member", "Slides", "Slide topics", "Learn", "Answers"], division_rows(review, deck),
                                                widths=[13, 11, 30, 25, 21]) +
            ('<p class="note">Slides 1–14 are divided (14 slides: 4 + 4 + 3 + 3). The “Key references” and “Thank you” slides are not assigned; '
             'the last presenter shows them and the team takes questions together.</p>' if review == 1 else
             '<p class="note">The first presenter of each review introduces the team; the last one leads the Q&amp;A.</p>'))


def tk(text):
    return f'<div class="takeaway">{text}</div>'


def roles_cards():
    return '<div class="cols c4">' + "".join(
        f'<div class="card"><h3 style="font-size:19px">{n}</h3><p style="font-size:16px">{r}</p></div>' for (n, _), r in zip(TEAM, ROLES)) + "</div>"


def thanks(label):
    return (f'<section class="slide section-slide"><div class="kicker">{label}</div><h2>Thank you — questions?</h2>'
            '<p>FinReason · numerical reasoning over financial reports</p></section>')


def qbox(head, body, style=""):
    return (f'<div><div style="font-size:16px;font-weight:700;color:#13294b;margin:0 0 5px">{head}</div>'
            f'<div class="qbox" style="font-size:15.5px;line-height:1.42;{style}">{body}</div></div>')


def papers_and_gaps(d):
    """The three foundational and three latest (2025-2026) papers, the gap each leaves, and how FinReason fills it."""
    head = ["Paper", "What it addresses", "Key result", "Gap it leaves", "How FinReason fills it"]
    groups = [
        ("Foundational papers", [
            ("FinQA", "finqa", "EMNLP 2021", "Numerical QA over financial tables + text (8,281 Qs)", "Fine-tuned FinQANet 61.2% vs experts 91.2%",
             "Needs fine-tuning; US $ reports only; no prompting or cost study",
             "<b>Prompting only</b> on small local LLMs; <b>Indian ₹&nbsp;set</b>; tokens and latency"),
            ("Program-of-Thought", "pot", "TMLR 2023", "LLMs slip at arithmetic in text; let Python compute", "FinQA: CoT 40.4% → PoT 64.5%",
             "Trusts every number in the code; no code safety",
             "<b>VPSC</b> rejects numbers not in the report; 4-layer <b>sandbox</b>"),
            ("EEDP", "eedp", "Findings ACL 2024", "Where LLMs fail at maths over financial documents", "Matches or beats CoT / PoT; errors in extraction",
             "Hand-written prompts only; no memorization check",
             "<b>DSPy / TextGrad</b> vs 7 strategies; <b>perturbation test</b>")]),
        ("Latest papers (2025–2026)", [
            ("FinanceReasoning", "finreasoning", "ACL 2025", "Harder, cleaner financial numerical-reasoning benchmark", "o1 + PoT best at 89.1%; numbers still imprecise",
             "Large frontier models only; no operand check",
             "<b>Small local models</b>; VPSC; prompt optimization"),
            ("VeriFin", "verifin", "arXiv 2026", "Verify the numbers in LLM financial answers", "XBRL + Z3 solver: 0 wrong claims accepted",
             "Needs XBRL-tagged US filings and a solver",
             "VPSC checks the <b>plain report table</b> — works on Indian PDFs"),
            ("IndiaFinBench", "indiafin", "arXiv 2026", "Indian regulatory text (SEBI, RBI), 406 Qs", "12 models zero-shot: 70.4–89.7%",
             "Regulatory text, not report tables; zero-shot only",
             "<b>Indian annual-report set</b>; <b>7 strategies</b> compared")])]
    widths = [15, 21, 20, 21, 23]
    cols = "".join(f'<col style="width:{w}%">' for w in widths)
    rows = ""
    for label, papers in groups:
        rows += (f'<tr><td colspan="5" style="background:#e3f1f2;color:#0e7c86;font-weight:800;font-size:12.5px;'
                 f'letter-spacing:.1em;text-transform:uppercase;padding:5px 10px">{label}</td></tr>')
        for name, key, venue, *cells in papers:
            rows += (f'<tr><td><b>{name}</b> {cite(key)}<br><span class="tiny">{venue}</span></td>' +
                     "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    d.add("Key papers", "Main and latest papers — and the gaps we address",
          '<style>.pg td,.pg th{font-size:15px;line-height:1.3;padding:5px 9px !important;vertical-align:top}</style>'
          f'<table class="t pg" style="width:100%;table-layout:fixed"><colgroup>{cols}</colgroup><thead><tr>' +
          "".join(f"<th>{h}</th>" for h in head) + f"</tr></thead><tbody>{rows}</tbody></table>" +
          tk("Big models only, XBRL-only number checks, no Indian reports — the gaps FinReason fills."))


def strategy_slides(d):
    """The prompting strategies in detail: overview, text prompts, code prompts, optimizers, experimental design."""
    d.add("Approach 1/5", "Our seven prompting strategies", '<div class="dense">' + table(
        ["Strategy", "What the prompt asks for", "Model output", "Calls", "Error it targets"], [
            ["Direct <span class='tiny'>(baseline)</span>", "Only the final answer line", "A number", "1", "— (no reasoning)"],
            ["Zero-shot CoT " + cite("zscot"), "“Think step by step”: find numbers → write calculation → compute", "Reasoning + answer", "1", "Multi-step slips"],
            ["Few-shot CoT " + cite("cot"), "Same, plus 3 worked FinQA <i>train</i> examples", "Reasoning + answer", "1", "Format, units, scale"],
            ["Decomposition " + cite("eedp"), "Knowledge → Extract → Decompose → Answer (labelled parts)", "Formula, operands, steps", "1", "Wrong formula / operand"],
            ["Program-of-Thought " + cite("pot"), "Python with named variables; sandbox runs it; 1 repair retry", "Code → executed result", "1–2", "Arithmetic errors"],
            ["Self-Consistency " + cite("sc"), "5 CoT samples (1 greedy + 4 at T = 0.7), majority vote", "5 answers → vote", "5", "Unstable reasoning"],
            ["<b>VPSC (ours)</b>", "5 programs → run → reject ungrounded numbers → vote", "Verified vote", "5", "Hallucinated numbers"]],
        num_cols=(3,), widths=[19, 38, 17, 7, 19]) + "</div>" +
          tk("7 hand-written strategies + 3 automatic optimizers (DSPy BootstrapFewShot, MIPROv2, TextGrad) = 10 prompt configurations, "
             "all with the same system prompt and answer rules."))

    d.add("Approach 2/5", "Text-based strategies — one question, four prompts",
          '<p class="small" style="margin:-6px 0 10px"><b>Q:</b> Revenue from operations was ₹54,842 cr (FY25) and ₹47,114 cr (FY24). What was the growth?</p>'
          '<div class="cols c2" style="gap:14px 22px">' +
          qbox("Direct", "<b>Prompt:</b> Give only the final answer line, with no explanation.\n<b>Output:</b> Answer: 16.4\n<span style='color:#ff9b7a'>No working shown → no way to check it.\nOnly 2–11% correct for the 1.7B model.</span>") +
          qbox("Zero-shot CoT", "<b>Prompt:</b> Think step by step: find the relevant numbers,\nwrite down the calculation, then compute it.\n"
               "<b>Output:</b> FY25 = 54,842; FY24 = 47,114\n(54,842 − 47,114) / 47,114 × 100 = 16.40\nAnswer: 16.40") +
          qbox("Few-shot CoT", "<b>Prompt:</b> 3 worked examples (question → steps → Answer)\n+ the same step-by-step instruction\n"
               "<b>Effect:</b> copies the format: units, signs, rounding,\nfinal line “Answer: &lt;number&gt;”") +
          qbox("Decomposition (EEDP)", "<b>Knowledge:</b> growth % = (new − old) / old × 100\n<b>Extract:</b> new = 54,842 (FY25, ₹ cr); old = 47,114 (FY24)\n"
               "<b>Decompose:</b> 1) 54,842 − 47,114 = 7,728\n             2) 7,728 / 47,114 × 100 = 16.40\n<b>Answer:</b> 16.40") + "</div>" +
          tk("More structure in the prompt → the model shows where every number comes from, so its errors become visible."))

    d.add("Approach 3/5", "Code-based strategies — Program-of-Thought → VPSC",
          '<div class="cols c2" style="gap:26px"><div>' +
          qbox("Program-of-Thought prompt → model code",
               "<span style='color:#9fb3cf'># Put each value in a named variable, store result in ans</span>\n"
               "revenue_fy25 = 54842\nrevenue_fy24 = 47114\nans = (revenue_fy25 - revenue_fy24) / revenue_fy24 * 100") +
          '<div style="margin-top:12px">' + ul([
              "<b>Sandbox</b> runs it → <code>ans = 16.40</code>; the computer, not the LLM, does arithmetic",
              "On an error the traceback is sent back once (<b>repair prompt</b>)"], cls="small") + "</div></div><div>" +
          '<div class="card accent"><h3>VPSC — Verified Program Self-Consistency</h3><ol style="padding-left:22px;margin:0">' + "".join(
              f"<li style='font-size:18px;margin-bottom:7px'>{x}</li>" for x in [
                  "Sample <b>5 programs</b>: 1 greedy + 4 at temperature 0.7",
                  "Run each in the sandbox",
                  "<b>Grounding check</b>: every number in the code must appear in the report (rescaling ×100/×1000 and constants such as 100, lakh, crore, years allowed)",
                  "<b>Majority vote</b> over grounded programs only",
                  "None grounded → vote over all executed programs"]) + "</ol></div>" +
          qbox("Rejected by the check", "revenue_fy25 = 54482   <span style='color:#ff9b7a'># 54,482 is not in the report → dropped</span>", "margin-top:4px") +
          "</div></div>" +
          tk("Ablation: PoT-SC uses the same 5 programs without the check — so any gain is due to verification alone."))

    d.add("Approach 4/5", "Optimizing the prompts automatically", '<div class="dense">' + table(
        ["Optimizer", "What it changes", "How it searches", "Reported effect"], [
            ["<b>DSPy BootstrapFewShot</b> " + cite("dspy"), "The few-shot examples", "Runs the CoT program on train questions; keeps traces our scorer marks correct as demos", "&gt;25% over few-shot (GPT-3.5)"],
            ["<b>DSPy MIPROv2</b> " + cite("mipro"), "Instruction + example set", "LLM proposes candidate instructions; Bayesian search over (instruction, demos) pairs", "Up to +13% (Llama-3-8B)"],
            ["<b>TextGrad</b> " + cite("textgrad"), "The system prompt text", "An LLM critiques wrong answers (“textual gradient”) and rewrites the prompt; kept only if dev accuracy holds", "GPT-4o GPQA 51 → 55%"]],
        widths=[22, 18, 44, 16]) + "</div>" +
          '<div class="cols c3" style="margin-top:16px">' + "".join(f'<div class="card"><h3 style="font-size:19px">{a}</h3><p>{b}</p></div>' for a, b in [
              ("Data", "50 train + 40 dev FinQA questions; test sets never seen"),
              ("Metric", "The same scorer as the experiments (0.5% tolerance)"),
              ("Cost", "One-time optimization tokens reported next to the accuracy gain")]) + "</div>" +
          tk("Question: can automatic optimization beat carefully hand-written prompts on financial tables?"))

    d.add("Approach 5/5", "Experimental design", '<div class="cols c3" style="gap:20px">' + "".join(
        f'<div class="card"><h3 style="font-size:21px">{a}</h3>{ul(b)}</div>' for a, b in [
            ("Factors", ["10 prompt configurations", "Qwen3-1.7B and Qwen3-8B " + cite("qwen3") + " (local, Ollama)", "FinQA (100), TAT-QA (100), Indian set (44)",
                         "Table as Markdown / JSON / HTML / text", "Full page vs top-5 retrieved rows", "Thinking mode on / off"]),
            ("Metrics", ["Execution accuracy (±0.5%)", "Exact match and F1", "Tokens per question and <b>per correct answer</b>", "Latency (s)",
                         "Format and code-failure rate"]),
            ("Analysis", ["95% bootstrap confidence intervals", "McNemar vs few-shot CoT (Holm-corrected)", "Accuracy by reasoning steps and evidence source",
                         "8-category error taxonomy", "Number-perturbation (memorization) test " + cite("gsmsym")])]).replace("<li>", "<li style='font-size:17px;margin-bottom:6px'>") +
          "</div>" + tk("Every claim comes with a confidence interval, a paired significance test and its token cost."))


# ============================================================================================
# Review 1
# ============================================================================================
def r1_deck():
    d = Deck("Review 1")
    d.raw(title_slide("Review 1", "Idea & literature survey"), "Title & introductions")
    d.add("The problem", "Numerical questions over financial reports",
          '<div class="cols c2"><div>' + table(["₹ crore", "FY25", "FY24"], [["Revenue from operations", "54,842", "47,114"], ["Profit before tax", "4,481", "4,607"],
                                                                         ["Changes in inventories", "(6,537)", "(2,149)"]], num_cols=(1, 2)) +
          '<p class="small" style="margin-top:12px"><b>Q:</b> What was the revenue growth from FY24 to FY25?</p></div><div>' + ul([
              "<b>Locate</b> the right row and years", "<b>Extract</b> with unit, scale, sign — “(6,537)” = −6,537",
              "<b>Formula</b>: (new − old) / old × 100", "<b>Compute</b>: 16.40%"]) + "</div></div>" +
          tk("Four skills in one question — one wrong digit, unit or sign gives a confident wrong answer."))
    d.add("Motivation", "LLMs read finance well but calculate badly",
          '<div class="cols c3">' + "".join(f'<div class="card"><div class="big">{a}</div><div class="stat lbl">{b}</div></div>' for a, b in [
              ("61%", f"best fine-tuned model on FinQA vs <b>91%</b> for experts {cite('finqa')}"),
              ("81%", f"FinanceBench questions GPT-4-Turbo + retrieval got wrong or refused {cite('financebench')}"),
              ("+24 pts", f"on FinQA when the model writes Python instead of text {cite('pot')}")]) + "</div>" +
          '<div style="margin-top:24px">' + ul(["Financial data is sensitive → we use <b>small local models</b>.", "Prompting is cheap to change — but which technique actually works?"]) + "</div>" +
          tk("Better prompting is the cheapest way to make LLMs reliable on financial numbers."))
    d.add("Problem statement", "Problem statement",
          '<div class="card accent" style="font-size:24px;line-height:1.45">Find which prompting and automatic prompt-optimization methods make LLMs most '
          '<b>accurate, reliable and cheap</b> at numerical questions over financial reports.</div>' +
          '<div class="cols c3" style="margin-top:24px">' + "".join(f'<div class="card"><h3>{a}</h3><p>{b}</p></div>' for a, b in [
              ("Input", "A report page (table + text) and a question"), ("Output", "The number, with evidence rows and the calculation"),
              ("Out of scope", "Fine-tuning models; whole 300-page documents")]) + "</div>" +
          tk("We change only the prompt — never the model — and measure accuracy, cost and reliability."))
    d.add("Objectives", "Objectives", '<ol style="padding-left:28px">' +
          "".join(f"<li style='font-size:26px;margin-bottom:18px'>{x}</li>" for x in [
              "Compare 7 prompting strategies (direct, CoT, Self-Consistency, decomposition, Program-of-Thought, our VPSC)",
              "Test automatic optimization: DSPy (BootstrapFewShot, MIPROv2) and TextGrad",
              "Compare a small (1.7B) and a larger (8B) local model on accuracy and cost",
              "Analyse errors and robustness; test on Indian annual reports (₹ crore/lakh)"]) + "</ol>")
    d.add("Literature", "Financial QA benchmarks", table(["Work", "What it is", "Key result"], [
        ["<b>FinQA</b> " + cite("finqa"), "8,281 questions with expert reasoning programs", "Model 61.2% vs experts 91.2%"],
        ["<b>TAT-QA</b> " + cite("tatqa"), "16,552 questions over tables + text", "50.1 EM vs humans 84.1"],
        ["<b>FinanceBench</b> " + cite("financebench"), "Open-book QA over company filings", "GPT-4-Turbo: 81% wrong/refused"],
        ["<b>EEDP</b> " + cite("eedp"), "LLM study on 4 financial datasets; Extract→Decompose prompt", "Matches or beats CoT / PoT"],
        ["<b>Indian benchmarks</b> " + cite("indfin", "indiafin"), "IndFin-Bench: 100 look-up Qs on Indian filings; IndiaFinBench: SEBI/RBI regulatory text", "Indian data is new (2026); little multi-step calculation"]]) +
          tk("Even the best systems are ~30 points below human experts."))
    papers_and_gaps(d)
    d.add("Approach", "One pipeline — only the prompt changes", D.pipeline() + tk(
        "Same questions, same scorer, same models → differences come only from the strategy."))
    strategy_slides(d)
    d.add("Novelty", "What is new", ul([
        "<b>VPSC</b> (ours): sample 5 programs → run them → <b>reject programs using numbers not in the report</b> → vote. Training-free, works on plain tables — lighter than recent verifiers " + cite("verifin", "dcrc") + ".",
        "<b>Indian calculation set</b>: 44 multi-step questions from Titan, Asian Paints, Marico, Pidilite (₹ crore/lakh), answers computed from formulas — complements look-up benchmarks " + cite("indfin") + ".",
        "<b>Manual vs automatic prompting</b>, head-to-head, with cost and statistical tests.",
        "<b>Auditable web app</b>: evidence rows, code, votes for every answer.",
    ]))
    d.add("References", "Key references", '<style>.refs2 ol{columns:2;column-gap:34px;padding-left:24px;margin:0}'
          '.refs2 li{font-size:12.5px !important;line-height:1.32;margin:0 0 6px;break-inside:avoid}</style>'
          '<div class="refs2">' + ref_list_html("refs", KEY_REFS) + "</div>")
    d.raw(thanks("Review 1"), "Thank you & Q&A")
    d.arrange(PLAN[1])
    return d


def r1_notes():
    lit = table(["Ref", "Work", "Remember this"], [
        [cite("finqa"), "FinQA (EMNLP 2021)", "8,281 Qs with reasoning programs; model 61.24% vs experts 91.16%"],
        [cite("tatqa"), "TAT-QA (ACL 2021)", "16,552 Qs over table + text; TagOp 50.1 EM vs humans 84.1"],
        [cite("financebench"), "FinanceBench (2023)", "GPT-4-Turbo + retrieval: 81% wrong or refused"],
        [cite("eedp"), "EEDP (ACL Findings 2024)", "Elicit→Extract→Decompose→Predict; basis of our decomposition prompt"],
        [cite("cot"), "Chain-of-Thought (NeurIPS 2022)", "Examples with steps → better reasoning"],
        [cite("zscot"), "Zero-shot CoT (NeurIPS 2022)", "“Let's think step by step”: GSM8K 10.4→40.7%"],
        [cite("sc"), "Self-Consistency (ICLR 2023)", "Vote over sampled answers: +17.9 pts GSM8K"],
        [cite("pot"), "Program-of-Thought (TMLR 2023)", "Python does the math: FinQA 40.4→64.5% (Codex)"],
        [cite("dspy"), "DSPy (ICLR 2024)", "Compiles prompts; BootstrapFewShot keeps correct self-made demos"],
        [cite("mipro"), "MIPROv2 (EMNLP 2024)", "Optimizes instructions + demos; up to +13%"],
        [cite("textgrad"), "TextGrad (Nature 2025)", "Textual “gradients” rewrite the prompt; GPT-4o GPQA 51→55%"],
        [cite("gsmsym"), "GSM-Symbolic (ICLR 2025)", "Changing only numbers lowers accuracy → memorization test idea"],
        [cite("indfin", "indiafin"), "IndFin-Bench, IndiaFinBench (2026)", "Indian benchmarks: filing look-up (100 Qs) and SEBI/RBI regulatory text (406 Qs) — not multi-step calculation"],
        [cite("finreasoning"), "FinanceReasoning (ACL 2025)", "Harder, cleaner financial numerical-reasoning benchmark; o1 + PoT best at 89.1%; reasoning models still imprecise with numbers"],
        [cite("verifin", "dcrc"), "VeriFin (2026), DCRC (KDD 2026)", "Check a model's numbers against XBRL facts with a solver / train an evidence-auditing agent — closest to VPSC"],
    ], widths=[7, 30, 63])
    qa = [("What is the project in one line?", "We test which prompting and prompt-optimization methods make LLMs accurate and cheap at numerical questions over financial reports, using local models."),
          ("Why not fine-tune?", "Needs labelled data, GPUs and retraining for every model; prompting is cheap, works with any model and is the course focus."),
          ("Why Program-of-Thought?", "LLMs make arithmetic slips; in PoT the model writes Python and the computer calculates exactly."),
          ("What is new?", "A fair manual-vs-automatic prompting comparison with cost and significance; a training-free grounding check inside program voting (VPSC); and Indian multi-step calculation questions."),
          ("Isn't this already done (VeriFin, IndFin-Bench)?", "Related, not the same: VeriFin needs XBRL data and a solver, DCRC needs training — VPSC needs neither. IndFin-Bench is mostly fact look-up; our Indian set is multi-step calculation."),
          ("Why local models?", "Financial data is sensitive; local models keep data on the laptop and cost nothing per query."),
          ("Why an Indian set?", "The main benchmarks are US filings; Indian reports use ₹ crore/lakh, 1,00,000 grouping and bracketed negatives, and existing Indian benchmarks do not test multi-step calculation.")]
    body = notes_head("Review 1", "Idea &amp; literature survey") + f"""
<div class="oneline">Which prompting strategies and automatic prompt optimizers make LLMs accurate, reliable and cheap at numerical questions over financial reports?</div>
{division_html(1, r1_deck())}
<h2>1. Problem</h2>
<p>Financial reports mix tables and text. A question like “What was revenue growth?” needs four skills: <b>locate</b> the row, <b>extract</b> values with
unit/scale/sign (₹ crore; “(6,537)” = −6,537), choose the <b>formula</b>, and <b>compute</b> without slips. LLMs are fluent but unreliable at this.</p>
<h2>2. Objectives</h2>
<ol><li>Compare 7 prompting strategies: direct, zero/few-shot CoT, decomposition, Program-of-Thought, Self-Consistency and our VPSC.</li>
<li>Test automatic optimization: DSPy BootstrapFewShot, MIPROv2, TextGrad — vs hand-written prompts, with their cost.</li>
<li>Compare Qwen3-1.7B and Qwen3-8B (local, Ollama) on accuracy, tokens, latency.</li>
<li>Analyse errors and robustness; test on 44 new questions from Indian annual reports.</li></ol>
<h2>3. Literature — papers to remember</h2>
{lit}
<h2>4. Gaps → our answer</h2>
{table(["Gap", "What we do"], [["Cost and significance rarely reported together", "Same questions/scorer/models; accuracy + CI, tokens, McNemar tests"],
                               ["No manual-vs-automatic comparison on financial calculations (that we found)", "DSPy + TextGrad vs strong manual prompts, with one-time cost"],
                               ["Indian benchmarks cover look-up and regulation, not calculation", "Indian calculation set: Titan, Asian Paints, Marico, Pidilite"],
                               ["Number verifiers need XBRL, a solver or training", "VPSC: training-free check that program numbers occur in the report"]], widths=[45, 55])}
<h2>5. Approach in one sentence</h2>
<p>Load question → build context (table as Markdown, optional retrieval) → prompt with a strategy → run code in a sandbox → score (0.5% tolerance) →
classify errors → statistics. Only the strategy changes between runs.</p>
<h2>6. Likely questions</h2>
<dl class="qa">{"".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in qa)}</dl>
<p class="note">[n] = reference numbers on the “Key references” slide.</p>"""
    return page("Review 1 notes", NOTES_CSS, body, running="FinReason · Review 1 · notes")


# ============================================================================================
# Review 2
# ============================================================================================
def r2_deck():
    import review2 as R2
    n_ver, ok_ops, ok_gold = R2.verification_summary()
    d = Deck("Review 2")
    d.raw(title_slide("Review 2", "High-level design & data collection"), "Title & introductions")
    d.add("Flow", "How one question flows", D.pipeline() + tk("The runner and the web app use exactly this flow."))
    d.add("Architecture", "Six layers", D.architecture())
    d.add("Modules", "Key modules", '<div>' + table(["Module", "Job"], [
        ["data.py", "Load FinQA, TAT-QA, Indian set → one <code>Example</code> format"],
        ["tables.py · retrieval.py", "Table → Markdown/JSON/HTML/text; BM25 + embeddings retrieval"],
        ["prompts.py · strategies.py", "Prompt templates; 8 strategies + DSPy/TextGrad behind one interface"],
        ["llm.py", "One client for Ollama and APIs; response cache; tokens and latency"],
        ["sandbox.py · verify.py", "Run model code safely; grounding check for VPSC"],
        ["answers.py · errors.py · metrics.py", "Parse and score answers; error taxonomy; CIs and McNemar"],
        ["app/ (streamlit_app.py, views/)", "Web app, 9 pages: Overview, Ask, Compare, Results, Optimization, Robustness, Errors, Data, Method"]], widths=[34, 66]) + "</div>")
    d.add("Safety", "Sandbox: running model code safely", D.sandbox() + '<div style="margin-top:18px">' + ul([
        "<b>Static check</b>: only <code>import math</code>; no files, network or dunders", "<b>Separate isolated Python process</b> for each program",
        "<b>Safe builtins only</b>; <b>CPU limit + 5 s timeout</b>"], cls="small") + "</div>" +
          tk("Model-written code is untrusted — four independent layers keep it harmless."))
    d.add("Scoring", "Scoring rule", ul([
        "Correct if within <b>0.5%</b> of the gold answer (or equal at the gold's precision)",
        "Percentages: <b>12.5 and 0.125 both accepted</b> (FinQA stores fractions, TAT-QA percents)",
        "Parser handles ₹, $, 1,00,000 grouping, (brackets) = negative, crore / lakh / million",
        "Statistics: 95% bootstrap CI; paired <b>McNemar</b> test vs few-shot CoT (Holm-corrected)"]) +
          tk("One scorer everywhere: experiments, DSPy metric, TextGrad, the app and the analysis."))
    d.add("Strategies", "Strategies compared", '<div>' + table(["Strategy", "Idea", "Calls"], [
        ["Direct", "Answer only", "1"], ["CoT zero-shot / few-shot", "Step-by-step (0 or 3 worked examples)", "1"],
        ["Decomposition", "Knowledge → Extract → Decompose → Answer", "1"], ["Program-of-Thought", "Write Python; sandbox runs it", "1–2"],
        ["Self-Consistency", "5 CoT samples, majority vote", "5"], ["<b>VPSC (ours)</b>", "5 programs, keep grounded ones, vote", "5"],
        ["DSPy / TextGrad", "Automatically optimized prompts", "1"]], num_cols=(2,), widths=[30, 58, 12]) + "</div>" +
          tk("Same system prompt, answer rules and worked examples for all — only the strategy differs."))
    d.add("Our method", "VPSC: Verified Program Self-Consistency", D.vpsc() + tk(
        "Grounding check: every number in the code must appear in the report. The ablation (PoT-SC) uses the same 5 programs without the check."))
    d.add("Optimization", "DSPy and TextGrad design", D.optimizers() + tk("Optimizers train only on FinQA train/dev — test sets are never seen."))
    d.add("Datasets", "Three datasets", table(["Dataset", "Source", "Used"], [
        ["FinQA " + cite("finqa"), "US earnings reports (GitHub)", "100 test Qs (seed 42); train for examples"],
        ["TAT-QA " + cite("tatqa"), "Annual reports (GitHub)", "100 arithmetic test Qs"],
        ["<b>Indian set (ours)</b>", "Titan, Asian Paints, Marico, Pidilite PDFs", "All 44 Qs"]]) +
          img("build/fig/data_composition.png", "width:100%;margin-top:10px"))
    d.add("Indian set", "How we built and checked it", D.indian_pipeline() + '<div class="cols c3" style="margin-top:10px">' + "".join(
        f'<div class="card"><div class="big" style="font-size:42px">{a}</div><div class="stat lbl">{b}</div></div>' for a, b in [
            ("366", "table cells — each must appear on its PDF page"), ("0", "answers typed by hand — all computed from formulas"),
            (f"{ok_ops}/{n_ver}", "questions re-verified against the PDF by us")]) + "</div>")
    d.add("Status", "Project status", '<div class="cols c2"><div class="card accent"><h3>Done</h3>' + ul([
        f"Library ({data.code_stats()[0]} modules), 9-page web app, {data.code_stats()[2]} automated tests passing", "FinQA, TAT-QA and Indian set ready and verified", "Retrieval recall measured",
        "All Qwen3-1.7B experiments"], cls="small") + '</div><div class="card warn"><h3>Next → Review 3</h3>' + ul([
        "Qwen3-8B experiments", "DSPy / TextGrad results", "Final analysis, IEEE paper, live demo"], cls="small") + "</div></div>")
    d.add("First results", "First results (Qwen3-1.7B, accuracy %)", '<div style="width:62%">' + R2.prelim_table() + "</div>" +
          tk(f"Asking for reasoning lifts a 1.7B model from ≤{P(max(acc(dd, S, 'direct') or 0 for dd in data.DATASETS), 0)}% to "
             f"{P(R.reasoning_range(S)[0], 0)}–{P(R.reasoning_range(S)[1], 0)}%."))
    d.raw(thanks("Review 2"), "Thank you & Q&A")
    d.arrange(PLAN[2])
    return d


def r2_notes():
    import review2 as R2
    n_ver, ok_ops, ok_gold = R2.verification_summary()
    qa = [("Why one common Example format?", "Every stage works on every dataset without special cases."),
          ("Why cache model responses?", "Identical re-runs for free; long experiments can resume; VPSC reuses the PoT call."),
          ("How is model code kept safe?", "AST check (only math), isolated process, safe builtins, CPU + 5 s limits; output is JSON only."),
          ("How do you prevent test leakage?", "Worked examples and optimizer data come only from FinQA train/dev."),
          ("Why McNemar?", "All strategies answer the same questions, so results are paired; McNemar compares only the questions where they differ."),
          ("How do you trust the Indian set?", f"366 cells checked against the PDFs at build time; answers computed from formulas; we re-verified {ok_ops}/{n_ver} questions.")]
    body = notes_head("Review 2", "High-level design &amp; data collection") + f"""
<div class="oneline">One controlled pipeline: only the prompting strategy changes; everything else (questions, scorer, model, settings) stays fixed.</div>
{division_html(2, r2_deck())}
<h2>1. Architecture (6 layers)</h2>
<ul><li><b>Data</b>: loaders turn FinQA, TAT-QA and the Indian set into one <code>Example</code> (question, table, text, gold, steps, unit).</li>
<li><b>Context</b>: table as Markdown/JSON/HTML/text; optional hybrid retrieval (BM25 + MiniLM embeddings in FAISS, fused with RRF).</li>
<li><b>Reasoning</b>: prompt library, strategy engine, LLM client (Ollama/API, cache), code sandbox, grounding verifier.</li>
<li><b>Optimization</b>: DSPy (BootstrapFewShot, MIPROv2) and TextGrad save optimized prompts as artifacts.</li>
<li><b>Evaluation</b>: answer parser + scorer (0.5% tolerance), 8-category error taxonomy, bootstrap CIs, McNemar + Holm.</li>
<li><b>Presentation</b>: one JSON line per answer → analysis tables/figures → Streamlit app.</li></ul>
<h2>2. Key designs to explain</h2>
{table(["Design", "In one line"], [
    ["VPSC", "5 programs (1 greedy + 4 at T=0.7) → run → keep those whose numbers all appear in the report → majority vote"],
    ["Sandbox", "AST rules + isolated <code>python -I</code> + safe builtins + CPU/time limits"],
    ["Scoring", "Within 0.5% of gold, or equal at gold's precision; % and fraction both accepted"],
    ["DSPy", "ChainOfThought program; metric = our scorer; 50 train / 40 dev FinQA questions"],
    ["TextGrad", "System prompt is the variable; critiques of wrong answers rewrite it; keep only if dev accuracy holds"],
    ["Experiments", "Same 100/100/44 questions (seed 42), temperature 0, same examples; McNemar vs few-shot CoT"]], widths=[18, 82])}
<h2>3. Data collection</h2>
<div class="nums"><div><b>1,147</b>FinQA test Qs (100 sampled)</div><div><b>699</b>TAT-QA arithmetic test Qs (100 sampled)</div>
<div><b>44</b>Indian questions, 4 companies</div><div><b>{ok_ops}/{n_ver}</b>Indian Qs re-verified vs PDF</div></div>
<ul><li><b>FinQA / TAT-QA</b>: downloaded from the authors' GitHub; TAT-QA filtered to arithmetic questions.</li>
<li><b>Indian set</b>: statements from Titan (AR 2024-25), Asian Paints (2023-24), Marico (FY25), Pidilite (2024-25) → rows transcribed exactly →
each question has a formula → gold = formula result in the sandbox → build fails unless all 366 cells appear on the PDF page.</li>
<li>Mix: 23 percentages, 8 ratios/₹ amounts, 13 in crore/lakh/million/billion, 1 yes/no; 16 questions need 3+ steps.</li>
<li><b>Perturbed FinQA</b> (88 Qs): operands changed by 10–30%, gold recomputed from the gold program — tests memorization.</li></ul>
<h2>4. Likely questions</h2>
<dl class="qa">{"".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in qa)}</dl>"""
    return page("Review 2 notes", NOTES_CSS, body, running="FinReason · Review 2 · notes")


# ============================================================================================
# Review 3
# ============================================================================================
def short_findings(m):
    """Five to eight one-line findings, each computed from the runs."""
    f = []
    if not R.has_model(m):
        return f
    lo, hi = R.reasoning_range(m)
    dmax = max(acc(d, m, "direct") or 0 for d in data.DATASETS)
    f.append(f"<b>Reasoning is essential:</b> direct ≤{P(dmax, 0)}% → reasoning strategies {P(lo, 0)}–{P(hi, 0)}%.")
    f.append(f"<b>Best single call:</b> {R.single_sentence(m).replace(' is the best single-call strategy on', ' on')}"
             + (" — differences not significant." if not R.any_significant(m, R.REASONING) else "."))
    mult = R.five_sample_multiplier(m)
    if mult:
        f.append(f"<b>5 samples don't pay:</b> Self-Consistency / VPSC cost {mult[0]:.1f}–{mult[1]:.1f}× tokens"
                 + (" for no significant gain." if not R.any_significant(m, ["sc_cot", "pot_sc", "vpsc"]) else "."))
    es = R.error_shares(m)
    if es:
        vc, n = es
        f.append(f"<b>Errors are about evidence:</b> {100 * vc.get('evidence_error', 0):.0f}% wrong/missing number, "
                 f"{100 * vc.get('reasoning_error', 0):.0f}% wrong formula, {100 * vc.get('scale_error', 0):.0f}% unit/scale.")
    dg = data.vpsc_diagnostics(m)
    if not dg.empty:
        flagged, wrong = int(dg.flagged_questions.sum()), int(dg.flagged_questions.sum() - dg.flagged_correct.sum())
        same = all(acc(d, m, "vpsc") == acc(d, m, "pot_sc") for d in dg.dataset)
        f.append(f"<b>VPSC:</b> {'same accuracy as PoT-SC' if same else 'changes some answers vs PoT-SC'}; flagged {flagged} questions, {wrong} of them wrong"
                 + (" → a precise warning flag." if flagged and wrong == flagged else "."))
    ind, fin = acc("indian", m, "pot_fs"), acc("finqa", m, "pot_fs")
    if ind is not None and fin is not None:
        f.append(f"<b>Indian reports:</b> PoT {P(ind, 0)}% vs {P(fin, 0)}% on FinQA → " + ("generalizes." if ind >= fin else "a generalization gap."))
    pt = data.perturbation()
    pm = pt[pt.model == m] if not pt.empty else pt
    if not pm.empty:
        f.append("<b>Perturbed numbers:</b> " + ", ".join(f"{SL(r.strategy)} {P(r.original_accuracy, 0)}→{P(r.perturbed_accuracy, 0)}%" for r in pm.itertuples())
                 + (" — no significant drop (no sign of memorization)." if all(r.p_value >= 0.05 for r in pm.itertuples()) else "."))
    th = data.cell("finqa", m, "cot_zs", think=True)
    if th is not None and th.n >= 100:
        tp, r0 = thinking_p(m), data.cell("finqa", m, "cot_zs")
        f.append(f"<b>Thinking mode:</b> zero-shot CoT on FinQA {P(r0.accuracy, 0)}% → {P(th.accuracy, 0)}% with thinking on, at {th.total_tokens / r0.total_tokens:.1f}× tokens and {th.latency_s / r0.latency_s:.0f}× time"
                 + (f" (McNemar p = {R.pfmt(tp)}" + (" — significant" if tp < 0.05 else "") + ")." if tp is not None else "."))
    for st in data.optimized_strategies(m):
        a, b = acc("finqa", m, st), acc("finqa", m, "cot_fs")
        if a is not None and b is not None:
            f.append(f"<b>{SL(st)}:</b> FinQA {P(a, 0)}% vs few-shot CoT {P(b, 0)}%.")
    return f


def ablation_rows(m):
    rows = []
    for f, lab in [("markdown", "Table as Markdown (default)"), ("json", "Table as JSON"), ("html", "Table as HTML"), ("text", "Table as row text")]:
        vals = [acc(d, m, "cot_fs", fmt=f) for d in ["finqa", "tatqa"]]
        rows.append([lab + " · few-shot CoT"] + [P(v, 0) if v is not None else "–" for v in vals])
    if all(r[1] == "–" and r[2] == "–" for r in rows[1:]):
        rows = []
    for cx, lab in [("full", "Full page · PoT"), ("retrieved", "Top-5 retrieved rows · PoT")]:
        vals = [acc(d, m, "pot_fs", context=cx) for d in ["finqa", "tatqa"]]
        if cx == "retrieved" and all(v is None for v in vals):
            rows = [r for r in rows if not r[0].startswith("Full page")]
            break
        rows.append([lab] + [P(v, 0) if v is not None else "–" for v in vals])
    th = data.cell("finqa", m, "cot_zs", think=True)
    if th is not None:
        r0 = data.cell("finqa", m, "cot_zs")
        rows.append(["Thinking off · zero-shot CoT", P(r0.accuracy, 0), "–"])
        rows.append([f"Thinking on · zero-shot CoT ({th.total_tokens / r0.total_tokens:.0f}× tokens)", P(th.accuracy, 0) + ("" if th.n >= 100 else f" (n={int(th.n)})"), "–"])
    return rows


def thinking_p(m):
    """Exact McNemar test: zero-shot CoT with vs without thinking on the same FinQA questions."""
    from finreason.metrics import mcnemar
    df = data.runs()
    g = df[(df.dataset == "finqa") & (df.model == m) & (df.strategy == "cot_zs") & (df.fmt == "markdown") & (df.context == "full") & (~df.perturbed)]
    piv = g.pivot_table(index="uid", columns="think", values="correct", aggfunc="first").dropna()
    if piv.shape[1] < 2:
        return None
    return mcnemar(piv[True].astype(bool), piv[False].astype(bool))[2]


def ablation_point(m):
    parts = []
    fm = {f: acc("finqa", m, "cot_fs", fmt=f) for f in ["markdown", "json", "html", "text"]}
    if all(v is not None for v in fm.values()):
        best_f = max(fm, key=fm.get)
        parts.append(f"best table format on FinQA: {best_f} ({P(fm[best_f], 0)}%), worst {min(fm, key=fm.get)} ({P(min(fm.values()), 0)}%)")
    a, b = acc("finqa", m, "pot_fs", context="retrieved"), acc("finqa", m, "pot_fs")
    if a is not None:
        parts.append(f"top-5 retrieval {P(a, 0)}% vs full page {P(b, 0)}% (FinQA PoT)")
    th = data.cell("finqa", m, "cot_zs", think=True)
    if th is not None:
        tp = thinking_p(m)
        parts.append(f"thinking mode {P(th.accuracy, 0)}% vs {P(acc('finqa', m, 'cot_zs'), 0)}% at {th.total_tokens / data.cell('finqa', m, 'cot_zs').total_tokens:.1f}× tokens"
                     + (f" (McNemar p = {R.pfmt(tp)})" if tp is not None else ""))
    if not parts:
        return ""
    txt = "; ".join(parts)
    return txt[0].upper() + txt[1:] + "."


def r3_main_table(m):
    rows = []
    for s in data.MAIN_ORDER + data.optimized_strategies(m):
        r = [SL(s)] + [P(acc(d, m, s), 0) if acc(d, m, s) is not None else "–" for d in data.DATASETS]
        c = data.cell("finqa", m, s)
        r.append(f"{c.total_tokens:,.0f}" if c is not None else "–")
        rows.append(r)
    return table(["Strategy", "FinQA", "TAT-QA", "Indian", "Tokens (FinQA)"], rows, num_cols=(1, 2, 3, 4), highlight=lambda i, r: "VPSC" in r[0])


def r3_deck():
    d = Deck("Review 3")
    d.raw(title_slide("Review 3", "Final demo & results"), "Title & introductions")
    d.add("Recap", "What we compared", D.pipeline() + tk(
        "11 strategies · 3 datasets (244 questions) · Qwen3 1.7B and 8B, local · same questions, scorer and settings."))
    setup = table(["Item", "Setting"], [
        ["Test sets", "FinQA 100 · TAT-QA 100 · Indian 44 · FinQA-perturbed 88"], ["Metric", "Correct if within 0.5% of the gold answer"],
        ["Statistics", "95% bootstrap CI; McNemar vs few-shot CoT (Holm-corrected)"], ["Models", "Qwen3-1.7B, Qwen3-8B via Ollama (Apple M4)"]], widths=[22, 78])
    if R.has_model(L):   # 16 content slides with the 8B results, so setup and status share one slide
        d.add("Setup", "Experimental setup", '<div class="dense">' + setup + R.status_table() + "</div>")
    else:                # without them, setup and status get one slide each (keeps 4 slides per presenter)
        d.add("Setup", "Experimental setup", setup + tk("Same questions, scorer and settings for every strategy — only the prompt changes."))
        d.add("Status", "Experiment status", R.status_table())
    for m in data.models():
        d.add("Main result", f"Accuracy by strategy — {ML(m)}",   # height capped so a one-dataset chart fits the slide
              R.img_or_pending(R.fig(f"main_bars_{ML(m)}"), "max-width:100%;max-height:300px;display:block;margin:0 auto") +
              tk(short_findings(m)[0] if short_findings(m) else ""))
    if R.has_model(L) and R.fig("model_compare"):
        d.add("Model size", "1.7B vs 8B", img(R.fig("model_compare"), "width:100%"))
    d.add("Generalization", "Indian annual reports", '<div class="dense">' + table(["Strategy"] + [ML(m) for m in data.models()],
          [[SL(s)] + [P(acc("indian", m, s), 0) if acc("indian", m, s) is not None else "–" for m in data.models()] for s in data.MAIN_ORDER],
          num_cols=range(1, 1 + len(data.models())), highlight=lambda i, r: "VPSC" in r[0]) + "</div>" +
          tk(next((x for x in short_findings(S) if "Indian" in x), "")))
    d.add("Cost", "Accuracy vs. cost", '<div class="cols c2">' + R.img_or_pending(R.fig("pareto_finqa")) + R.img_or_pending(R.fig("pareto_tatqa")) + "</div>" +
          tk(next((x for x in short_findings(S) if "5 samples" in x), "")))
    o = R.opt_table()
    d.add("Optimization", "DSPy and TextGrad", (R.img_or_pending(R.fig("optimization"), "width:100%")) if o else R.img_or_pending(None, what="The DSPy / TextGrad stage"))
    pt = data.perturbation()
    pm = pt[pt.model == S] if not pt.empty else pt
    if not pm.empty:
        d.add("Robustness", "Memorization check: change the numbers", table(["Strategy", "Original", "Numbers changed", "McNemar p"], [
            [SL(r.strategy), P(r.original_accuracy, 0), P(r.perturbed_accuracy, 0), R.pfmt(r.p_value)] for r in pm.itertuples()], num_cols=(1, 2, 3)) +
              f'<p class="note" style="margin-top:10px">Same {int(pm.n.iloc[0])} FinQA questions; every operand changed by 10–30% and the answer recomputed.</p>' +
              tk(next((x for x in short_findings(S) if "Perturbed" in x), "")))
    abl = ablation_rows(S)
    if abl:
        d.add("Ablations", "What else changes accuracy?", table(["Variant", "FinQA", "TAT-QA"], abl, num_cols=(1, 2)) + tk(ablation_point(S)))
    d.add("Errors", "Why answers are wrong", R.img_or_pending(R.fig(f"errors_{ML(S)}"), "width:100%") +
          tk(next((x for x in short_findings(S) if "evidence" in x), "")))
    dg = data.vpsc_diagnostics(S)
    d.add("Our method", "VPSC result", '<div class="dense">' + table(["Dataset", "VPSC", "PoT-SC", "Programs rejected", "Flagged Qs (wrong)"], [
        [data.DLABEL[r.dataset], P(acc(r.dataset, S, "vpsc"), 0), P(acc(r.dataset, S, "pot_sc"), 0), f"{r.ungrounded} / {r.executed}",
         f"{r.flagged_questions} ({r.flagged_questions - r.flagged_correct})"] for r in dg.itertuples()], num_cols=(1, 2, 3, 4)) + "</div>" +
          '<p class="small" style="margin-top:14px">The 1.7B model\'s 5 programs almost always agree, so rejecting ungrounded ones rarely changes the vote.</p>' +
          tk("Grounding is a precise warning flag: when it fires, the answer was wrong — use it to alert or abstain."))
    if R.shot("ask_result"):
        d.add("Web app", "Live demo: every answer is auditable", '<div class="cols c2">' + img(R.shot("ask_result"), "width:100%;border-radius:10px") +
              img(R.shot("ask_votes"), "width:100%;border-radius:10px") + "</div>" +
              tk("Answer, evidence rows, generated code and votes with grounding status — all in the app."))
    d.add("Demo", "Demo plan (5 minutes)", '<ol style="padding-left:26px">' + "".join(f"<li style='font-size:22px;margin-bottom:12px'>{x}</li>" for x in [
        "<b>Overview</b>: headline findings and the claims checklist, computed from the results",
        "<b>Ask</b>: Indian question <i>marico-08</i> (9-year CAGR) with VPSC → answer, evidence, code, votes; then <b>paste a table</b> typed live",
        "<b>Data</b>: the same question next to its annual-report PDF page", "<b>Compare</b>: Direct vs CoT vs PoT vs VPSC on one question",
        "<b>Results</b> and <b>Optimization</b>: accuracy with CIs, cost, DSPy / TextGrad; <b>Errors</b>: open one evidence error"]) + "</ol>")
    d.add("Findings", "Key findings", ul(short_findings(S), cls="small"))
    concl = ["Reasoning prompts make small local models usable", "Python beats text for the arithmetic", "Remaining problem: picking the right numbers",
             "Grounding flags unreliable answers"]
    limits = ["Small samples (±10 pts) → full test sets", "One model family → larger / API models", "Value-level grounding → cell-level check + abstain",
              "Rule-based error labels → human annotation"]
    if R.has_model(L):
        d.add("Conclusion", "Conclusion, limitations, future work", '<div class="cols c2"><div class="card accent"><h3>Conclusion</h3>' + ul(concl, cls="small") +
              '</div><div class="card"><h3>Limits → future</h3>' + ul(limits, cls="small") + "</div></div>")
    else:
        d.add("Conclusion", "Conclusion", ul(concl) + tk("Prompt choice matters most at the bottom: reasoning and code turn a small local model into a usable one."))
        d.add("Limitations", "Limitations and future work", ul(limits))
    d.raw(thanks("Review 3"), "Thank you & Q&A")
    d.arrange(plan3())
    return d


def r3_notes():
    sf = short_findings(S)
    lo, hi = R.reasoning_range(S)
    t = R.totals()
    qa = [(q, a) for q, a in R.viva()][:8]
    body = notes_head("Review 3", "Final results &amp; demo") + f"""
<div class="oneline">For a small local model, asking for reasoning matters most; Python does the arithmetic best; the remaining errors are about picking the right numbers.</div>
{division_html(3, r3_deck())}
<h2>1. Numbers to remember ({ML(S)})</h2>
<div class="nums"><div><b>≤{P(max(acc(d, S, 'direct') or 0 for d in data.DATASETS), 0)}%</b>direct answering</div><div><b>{P(lo, 0)}–{P(hi, 0)}%</b>reasoning strategies</div>
<div><b>{t['records']:,}</b>answers recorded (all runs, both models)</div><div><b>{t['tokens'] / 1e6:.1f} M</b>tokens processed (all runs)</div></div>
<p class="tcaption">Accuracy (%) and tokens per question.</p>
{r3_main_table(S)}
{("<p class='tcaption'>Qwen3-8B</p>" + r3_main_table(L)) if R.has_model(L) else ""}
<h2>2. Findings (one line each)</h2>
<ul>{"".join(f"<li>{x}</li>" for x in sf)}</ul>
<h2>3. Research questions — short answers</h2>
{table(["RQ", "Answer"], [
    ["RQ1 strategies", f"Reasoning ≫ direct ({P(lo, 0)}–{P(hi, 0)}% vs ≤{P(max(acc(d, S, 'direct') or 0 for d in data.DATASETS), 0)}%); among reasoning strategies small, non-significant differences."],
    ["RQ2 optimization", ("; ".join(x.replace("<b>", "").replace("</b>", "") for x in sf if x.startswith("<b>DSPy") or x.startswith("<b>TextGrad")) or "Pending (running).")],
    ["RQ3 model size", "See the 8B table." if R.has_model(L) else "Pending (8B running)."],
    ["RQ4 errors / robustness", " ".join(x.split("</b>", 1)[1].strip() for x in sf if x.startswith(("<b>Errors", "<b>Perturbed", "<b>Indian")))],
    ["RQ5 VPSC", next((x.split("</b>", 1)[1].strip() for x in sf if x.startswith("<b>VPSC")), "Pending.")]], widths=[20, 80])}
<h2>4. Demo (5 min)</h2>
<ol><li>Start: <code>OLLAMA_NUM_PARALLEL=4 ollama serve</code> and <code>bash scripts/start_app.sh</code> → <code>localhost:8501</code>.</li>
<li><b>Overview</b> → headline findings and the claims checklist.</li>
<li><b>Ask</b> → Indian reports → <i>marico-08</i> → VPSC → show answer, Evidence, Code &amp; trace, Votes; then <b>Paste a table</b> and ask a growth question.</li>
<li><b>Data</b> → Marico → the same question beside its PDF page. <b>Compare</b> → Direct / CoT / PoT / VPSC. <b>Results</b> → CIs and cost; <b>Optimization</b> → DSPy / TextGrad. <b>Errors</b> → one evidence error.</li>
<li>Backup: slides with screenshots; <code>results/report.md</code>.</li></ol>
<h2>5. Top viva questions</h2>
<dl class="qa">{"".join(f"<dt>{q}</dt><dd>{a}</dd>" for q, a in qa)}</dl>"""
    return page("Review 3 notes", NOTES_CSS, body, running="FinReason · Review 3 · notes")


def r1_slides():
    return page("Review 1 slides", SLIDE_CSS_CONCISE, r1_deck().html())


def r2_slides():
    return page("Review 2 slides", SLIDE_CSS_CONCISE, r2_deck().html())


def r3_slides():
    return page("Review 3 slides", SLIDE_CSS_CONCISE, r3_deck().html())


def work_division():
    """One page: who presents what in every review, plus project responsibilities."""
    decks = {1: r1_deck(), 2: r2_deck(), 3: r3_deck()}
    rows = []
    for name, srn in TEAM:
        r = [f"<b>{name}</b><br><span style='color:#5b6678'>{srn}</span>"]
        total = 0
        for k in (1, 2, 3):
            mine = [(n, t) for n, t, w in decks[k].assignments() if w == name]
            content = counted(k, [t for n, t in mine])
            total += len(content)
            r.append(f"<b>Slides {_ranges([n for n, _ in mine])}</b><br>" + "<br>".join(content))
        r.append(str(total))
        rows.append(r)
    resp = table(["Member", "Project responsibility"], [[n, r] for (n, _), r in zip(TEAM, ROLES)], widths=[25, 75])
    body = notes_head("All reviews", "Work division") + f"""
<div class="oneline">The work is divided (almost) equally in every review. Review 1: its first 14 slides (4 + 4 + 3 + 3; references and thank-you not assigned).
Review 2: 3 slides each. Review 3: 4 slides each. Everyone has a mix of overview and technical slides.</div>
<h2>Who presents which slides</h2>
{table(["Member", "Review 1", "Review 2", "Review 3", "Slides"], rows, num_cols=(4,), widths=[15, 27, 27, 27, 4])}
<h2>Project responsibilities</h2>
{resp}
<h2>How to prepare</h2>
<ul><li>Read your part of the review's <b>Speaker script</b>: what to say on each of your slides, with the hand-over line to the next presenter.</li>
<li>Learn your slides' “Key point” lines first — they are the sentence to stress on each slide.</li>
<li>Then read the “Learn” column of your review's notes and practise the questions listed under “Answers”.</li>
<li>Everyone should be able to explain three things in one sentence: the scoring rule (within 0.5%), Program-of-Thought (Python does the maths) and VPSC (reject programs using numbers not in the report).</li>
<li>Dhruvagouda runs the live demo in Review 3; Gaurav keeps the slides with screenshots ready as a backup.</li></ul>"""
    return page("Work division", NOTES_CSS, body, running="FinReason · work division")
