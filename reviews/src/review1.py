"""Review 1 (10 marks): idea presentation + literature survey. Slides and a written report."""
import diagrams as D
from common import (Deck, REPORT_CSS, SLIDE_CSS, TEAM, cover, img, page, table, title_slide, ul)
from references import cite, ref_list_html

LABEL = "Review 1"
TICK, DASH = '<b style="color:#0e7c86">✓</b>', '<span style="color:#9aa3b2">–</span>'
PARTIAL = '<span style="color:#c2610c">◐</span>'

# ------------------------------------------------------------------------------------------
# Shared content
# ------------------------------------------------------------------------------------------
EXAMPLE_TABLE = table(
    ["Particulars (₹ in crore)", "FY 2024-25", "FY 2023-24"],
    [["Revenue from operations", "54,842", "47,114"], ["Finance costs", "767", "480"],
     ["Changes in inventories …", "(6,537)", "(2,149)"], ["Profit before tax", "4,481", "4,607"],
     ["Profit for the year", "3,335", "3,544"]], num_cols=(1, 2))

OBJECTIVES = [
    "<b>Benchmark manual prompting strategies</b> (direct, zero/few-shot Chain-of-Thought, Self-Consistency, decomposition, Program-of-Thought) for multi-step financial numerical reasoning.",
    "<b>Evaluate automated prompt optimization</b> (DSPy BootstrapFewShot and MIPROv2, TextGrad): does it beat carefully engineered prompts, and at what one-time cost?",
    "<b>Compare a small and a larger local model</b> (Qwen3-1.7B vs Qwen3-8B; API models supported) on accuracy, tokens, latency and cost per query.",
    "<b>Analyse failure modes and robustness</b>: an error taxonomy, a numerical-perturbation (memorization) test, table-format and retrieval ablations, and generalization to Indian annual reports (₹ crore / lakh).",
    "<b>Propose and test an improvement</b> motivated by the error analysis — Verified Program Self-Consistency (VPSC) — and deliver an interactive web application with evidence and calculation traces.",
]

RQS = [
    ("RQ1", "How much do prompting strategies change accuracy on multi-step financial questions, and which is best per token spent?"),
    ("RQ2", "Do automatically optimized prompts (DSPy, TextGrad) outperform hand-written prompts, and is the optimization cost justified?"),
    ("RQ3", "How do model size (1.7B vs 8B) and strategy interact — can a good strategy close the gap of a smaller model?"),
    ("RQ4", "Where do models fail (evidence, units/scale, sign, arithmetic), and are the results robust to changed numbers and to Indian reports?"),
    ("RQ5", "Does verifying that a program's numbers are grounded in the report (VPSC) improve over plain program self-consistency?"),
]

GAPS = [
    ("No controlled, cost-aware comparison", "Prior work reports accuracy for one or two strategies on large proprietary models; token cost, latency and statistical significance across strategies are rarely reported together."),
    ("Manual vs automated prompting not compared in finance", "DSPy, MIPROv2 and TextGrad were evaluated on general QA, math and code tasks; we found no evaluation on financial table-text reasoning against strong hand-written baselines."),
    ("Small local models under-studied", "Banks and analysts often cannot send filings to external APIs; how far a 2–8B model on a laptop gets with good prompting is largely unknown."),
    ("No Indian calculation benchmark", "FinQA, TAT-QA, ConvFinQA and FinanceBench use US/Western reports. The 2026 Indian benchmarks cover filing look-up (IndFin-Bench " + cite("indfin") + ") and regulatory text (IndiaFinBench " + cite("indiafin") + "), not multi-step calculation with ₹ crore/lakh, 1,00,000 grouping and bracketed negatives."),
    ("Errors are counted, not explained", "Few studies categorize why answers are wrong or test for memorization of public benchmarks by perturbing numbers (cf. GSM-Symbolic for math)."),
    ("No lightweight number check", "PoT/PAL execute whatever numbers the model writes. Recent verifiers check operands against XBRL facts with a solver (VeriFin " + cite("verifin") + ") or train an evidence-auditing agent (DCRC " + cite("dcrc") + "); we found no training-free check for plain report tables."),
]

LIT_ROWS = [
    ("finqa", "FinQA — Chen et al., EMNLP 2021", "8,281 expert-annotated QA pairs over S&P 500 earnings reports, each with a gold reasoning program; FinQANet retriever + program generator.",
     "Best fine-tuned model 61.24% execution accuracy vs 91.16% for financial experts.", "Main benchmark; gold programs used for operand-level error analysis and perturbation."),
    ("tatqa", "TAT-QA — Zhu et al., ACL 2021", "16,552 questions over 2,757 hybrid table + text contexts from real financial reports; TagOp sequence tagging + symbolic operators.",
     "TagOp 50.1 EM / 58.0 F1 vs humans 84.1 / 90.8; about 42% of questions are arithmetic.", "Second benchmark; we use its arithmetic subset and scale labels."),
    ("convfinqa", "ConvFinQA — Chen et al., EMNLP 2022", "Conversational extension of FinQA: chains of dependent numerical questions.",
     "Long reasoning chains remain hard for both fine-tuned models and LLM prompting.", "Motivates step-wise analysis by number of operations."),
    ("docfinqa", "DocFinQA — Reddy et al., ACL 2024", "7,437 FinQA questions re-posed over full filings (≈123k words on average).",
     "Retrieval + long-context LLMs struggle badly with full documents.", "Motivates our evidence-retrieval module and recall study."),
    ("financebench", "FinanceBench — Islam et al., 2023", "Open-book QA benchmark over public-company filings.",
     "GPT-4-Turbo with retrieval answered 81% of evaluated questions wrongly or refused.", "Shows LLMs are unreliable on real financial QA."),
    ("eedp", "EEDP — Srivastava et al., Findings ACL 2024", "Evaluates LLM math reasoning on TAT-QA, FinQA, ConvFinQA, MultiHiertt; proposes Elicit→Extract→Decompose→Predict prompting.",
     "EEDP matches or beats CoT/PoT baselines; errors concentrate in extraction and multi-step arithmetic.", "Basis of our decomposition strategy (Knowledge→Extract→Decompose→Answer)."),
    ("cot", "Chain-of-Thought — Wei et al., NeurIPS 2022", "Few-shot exemplars with intermediate reasoning steps.",
     "Large gains on arithmetic reasoning that emerge with model scale.", "Few-shot CoT is our main baseline."),
    ("zscot", "Zero-shot CoT — Kojima et al., NeurIPS 2022", "Adds “Let's think step by step” without exemplars.",
     "MultiArith 17.7→78.7%, GSM8K 10.4→40.7% (InstructGPT).", "Zero-shot CoT baseline; TextGrad starts from it."),
    ("sc", "Self-Consistency — Wang et al., ICLR 2023", "Sample diverse reasoning paths, majority-vote the answers.",
     "+17.9 points on GSM8K over greedy CoT.", "CoT-SC baseline; voting idea reused in VPSC."),
    ("l2m", "Least-to-most / Decomposed / Plan-and-solve (ICLR 2023, ACL 2023)", "Break a problem into sub-problems or an explicit plan before solving.",
     "Better generalization to harder, longer problems.", "Informs the decomposition prompt."),
    ("pot", "Program-of-Thought — Chen et al., TMLR 2023", "The LLM writes a Python program; an interpreter does the arithmetic.",
     "FinQA (Codex): CoT 40.4 → PoT 64.5; with self-consistency 44.4 → 68.1.", "Core strategy; we add sandboxing and grounding checks."),
    ("pal", "PAL — Gao et al., ICML 2023", "Program-aided LMs: reasoning as code, execution offloaded to Python.",
     "Outperforms much larger CoT models on math word problems.", "Confirms ‘compute with code, reason with language’."),
    ("ape", "APE / OPRO — ICLR 2023 / 2024", "LLMs propose and score instructions (APE) or iteratively optimize prompts from a score trajectory (OPRO).",
     "Automatically found prompts match or beat human prompts (OPRO: up to +8% GSM8K, +50% BBH).", "Background for automated optimization."),
    ("dspy", "DSPy — Khattab et al., ICLR 2024", "Declarative LM programs (signatures, modules) compiled by optimizers such as BootstrapFewShot.",
     "Self-bootstrapped pipelines beat standard few-shot prompting by >25% (GPT-3.5) and >65% (Llama-2-13B).", "Optimizer #1 (BootstrapFewShot)."),
    ("mipro", "MIPROv2 — Opsahl-Ong et al., EMNLP 2024", "Jointly optimizes instructions and demonstrations with a Bayesian surrogate and minibatch evaluation.",
     "Beats baselines on 5 of 6 programs with Llama-3-8B, by up to 13% accuracy.", "Optimizer #2 (MIPROv2)."),
    ("textgrad", "TextGrad — Yuksekgonul et al., Nature 2025", "‘Backpropagates’ natural-language feedback (textual gradients) to update prompts or solutions.",
     "e.g. GPT-4o zero-shot GPQA accuracy 51% → 55%.", "Optimizer #3 (system-prompt optimization)."),
    ("tablellm", "Table Meets LLM — Sui et al., WSDM 2024", "Benchmark of LLM structural understanding of tables under different serializations and prompts.",
     "Input format and prompt choices change accuracy substantially.", "Motivates our table-format ablation (Markdown/JSON/HTML/text)."),
    ("rrf", "BM25, Sentence-BERT, FAISS, RRF", "Lexical ranking, dense sentence embeddings, fast vector search, reciprocal-rank fusion.",
     "Simple RRF fusion is a strong, robust way to combine rankers.", "Our hybrid evidence retriever."),
    ("gsmsym", "GSM-Symbolic — Mirzadeh et al., ICLR 2025", "Re-instantiates GSM8K problems with new names and numbers.",
     "Accuracy drops and varies when only the numbers change, suggesting pattern matching.", "Our numerical-perturbation (memorization) test for FinQA."),
    ("indfin", "IndFin-Bench (2026) / IndiaFinBench " + cite("indiafin") + " (2026)", "Indian benchmarks: 100 mostly look-up questions over listed companies' filings; 406 questions over SEBI/RBI regulatory text (92 numerical).",
     "Recent Indian financial benchmarks; little multi-step calculation over statements.", "Our Indian set complements them with formula-computed multi-step calculations."),
    ("verifin", "VeriFin — Hall et al., 2026; DCRC " + cite("dcrc") + " — Chen et al., KDD 2026", "Ground operands of LLM financial claims in XBRL facts and verify with Z3; or train an evidence-auditing agent that compiles executable programs.",
     "VeriFin: zero false accepts on 600 10-K questions; DCRC deployed in an online QA system.", "Closest to VPSC; our check is training-free and needs no XBRL or solver."),
    ("bloomberggpt", "BloombergGPT / TAT-LLM (2023 / ICAIF 2024)", "Domain pre-training (50B params, 363B finance tokens) or fine-tuning LLaMA-2-7B with an extractor–reasoner–executor pipeline.",
     "Domain models help, but need large data and compute budgets.", "We study the cheaper alternative: prompting + optimization."),
]

MATRIX_COLS = ["Fin. tables + text", "Compares prompt strategies", "Executes code", "Automated prompt optimization",
               "Small open / local models", "Cost & latency", "Robustness test", "Indian (₹ crore/lakh) data"]
MATRIX = [
    ("FinQA " + cite("finqa"), [TICK, DASH, PARTIAL, DASH, DASH, DASH, DASH, DASH]),
    ("TAT-QA " + cite("tatqa"), [TICK, DASH, PARTIAL, DASH, DASH, DASH, DASH, DASH]),
    ("FinanceBench " + cite("financebench"), [TICK, DASH, DASH, DASH, DASH, DASH, DASH, DASH]),
    ("EEDP " + cite("eedp"), [TICK, TICK, DASH, DASH, DASH, DASH, DASH, DASH]),
    ("Program-of-Thought " + cite("pot"), [TICK, TICK, TICK, DASH, DASH, DASH, DASH, DASH]),
    ("DSPy / MIPROv2 " + cite("dspy", "mipro"), [DASH, DASH, DASH, TICK, TICK, DASH, DASH, DASH]),
    ("TextGrad " + cite("textgrad"), [DASH, DASH, DASH, TICK, DASH, DASH, DASH, DASH]),
    ("Table Meets LLM " + cite("tablellm"), [PARTIAL, TICK, DASH, DASH, DASH, DASH, DASH, DASH]),
    ("GSM-Symbolic " + cite("gsmsym"), [DASH, DASH, DASH, DASH, TICK, DASH, TICK, DASH]),
    ("IndFin-Bench / IndiaFinBench " + cite("indfin", "indiafin"), [PARTIAL, DASH, DASH, DASH, DASH, DASH, DASH, TICK]),
    ("VeriFin " + cite("verifin"), [TICK, DASH, PARTIAL, DASH, DASH, DASH, DASH, DASH]),
    ("DCRC " + cite("dcrc"), [TICK, DASH, TICK, DASH, DASH, DASH, DASH, DASH]),
    ("<b>This project (FinReason)</b>", [TICK] * 8),
]


def matrix_table(cls="t"):
    return table(["Work"] + MATRIX_COLS, [[w] + v for w, v in MATRIX], cls=cls,
                 highlight=lambda i, r: "This project" in r[0])


# ------------------------------------------------------------------------------------------
# Slides
# ------------------------------------------------------------------------------------------
def slides():
    d = Deck(LABEL)
    d.raw(title_slide("Review 1", "Idea presentation & literature survey"))
    d.add("Agenda", "What this review covers", '<div class="cols c2">' + ul([
        "The problem: numerical reasoning over financial reports", "Why it matters and why it is hard",
        "Problem statement, objectives and research questions", "Literature survey (20+ works in 6 themes)",
    ]) + ul([
        "Comparison matrix and research gaps", "Proposed approach and novelty", "Datasets, tools and evaluation plan",
        "Expected outcomes",
    ]) + "</div>")
    d.add("The problem", "Answering analytical questions over financial statements",
          f'<div class="cols c46"><div><p class="small" style="color:#5b6678;margin-bottom:6px">Titan Company Ltd — standalone P&amp;L (Annual Report 2024-25, p. 275)</p>{EXAMPLE_TABLE}'
          '<div class="callout" style="margin-top:12px"><b>Q:</b> What was the percentage growth in revenue from operations from FY 2023-24 to FY 2024-25?</div></div>'
          '<div><div class="card accent"><h3>What a correct answer requires</h3><ol style="padding-left:22px;margin:0">'
          '<li><b>Locate</b> the right row and both year columns</li>'
          '<li><b>Extract</b> values with unit, scale and sign: ₹ crore; “(6,537)” means −6,537</li>'
          '<li><b>Choose the formula</b>: growth = (new − old) / old × 100</li>'
          '<li><b>Compute</b>: (54,842 − 47,114) / 47,114 × 100 = <b>16.40%</b></li></ol></div>'
          '<p class="small" style="margin-top:14px">Analysts ask such questions constantly — growth, margins, ratios, CAGR, coverage. A single misread digit, unit or sign gives a confidently wrong answer.</p></div></div>')
    d.add("Motivation", "LLMs read finance fluently, but calculate unreliably",
          '<div class="cols c3">'
          '<div class="card"><div class="big">61.2%</div><div class="stat lbl">best fine-tuned model on FinQA, vs <b>91.2%</b> for financial experts ' + cite("finqa") + '</div></div>'
          '<div class="card"><div class="big">81%</div><div class="stat lbl">of evaluated FinanceBench questions answered wrongly or refused by GPT-4-Turbo with retrieval ' + cite("financebench") + '</div></div>'
          '<div class="card"><div class="big">+24</div><div class="stat lbl">points on FinQA when Codex writes a program instead of free-text reasoning (40.4 → 64.5) ' + cite("pot") + '</div></div></div>'
          '<div class="cols c2" style="margin-top:22px">' + ul([
              "Errors cost money: a wrong ratio or growth figure flows into investment and credit decisions.",
              "Answers must be <b>auditable</b>: which numbers were used, and how?",
          ]) + ul([
              "Financial data is sensitive: small <b>local</b> models avoid sending filings to external APIs.",
              "Prompting is cheap to change — but which technique works, and is automatic optimization worth it?",
          ]) + "</div>")
    d.add("Problem statement", "What we set out to solve",
          '<div class="card accent" style="font-size:21px;line-height:1.45;padding:22px 26px">Given a page of a financial report (a table plus surrounding text) and a natural-language question that needs numerical reasoning, '
          'produce the correct numeric answer <i>with a transparent evidence and calculation trace</i> — and determine, through controlled experiments, '
          'which prompting strategies and automated prompt-optimization methods make Large Language Models most <b>accurate, reliable and cost-efficient</b> at this task, '
          'for both small local and larger models, on public benchmarks and on unseen Indian annual reports.</div>'
          '<div class="cols c3" style="margin-top:22px">'
          '<div class="card"><h3>Input</h3><p>Table (rows × columns) + text paragraphs + question</p></div>'
          '<div class="card"><h3>Output</h3><p>Number (or yes/no) in the report\'s units, plus evidence rows, program / reasoning and confidence</p></div>'
          '<div class="card"><h3>Out of scope</h3><p>Model fine-tuning; span-extraction questions; whole-document (100+ page) search</p></div></div>')
    d.add("Objectives", "Five objectives", '<ol style="padding-left:28px">' + "".join(f"<li style='font-size:22px;margin-bottom:14px'>{o}</li>" for o in OBJECTIVES) + "</ol>")
    d.add("Research questions", "Questions the experiments must answer",
          table(["", "Research question"], [[f"<b>{a}</b>", b] for a, b in RQS]) +
          '<p class="note" style="margin-top:12px">Every comparison uses the same questions, the same scorer and the same models — only the prompt changes — and is tested for significance (paired McNemar test, Holm correction).</p>')
    d.section("Literature survey", "Six themes, 20+ works", "Financial QA benchmarks · prompting strategies for reasoning · program-aided reasoning · automated prompt optimization · tables, retrieval and robustness · domain-specific models")
    d.add("Literature 1/6", "Benchmarks for financial numerical reasoning", table(
        ["Work", "What it contributes", "Key reported result"],
        [["<b>FinQA</b> " + cite("finqa") + "<br><span class='tiny'>EMNLP 2021</span>", "8,281 QA pairs over S&amp;P 500 earnings reports with expert-written reasoning programs", "FinQANet 61.24% vs experts 91.16% execution accuracy"],
         ["<b>TAT-QA</b> " + cite("tatqa") + "<br><span class='tiny'>ACL 2021</span>", "16,552 questions over 2,757 hybrid table + text contexts", "TagOp 50.1 EM / 58.0 F1 vs humans 84.1 / 90.8"],
         ["<b>ConvFinQA</b> " + cite("convfinqa") + "<br><span class='tiny'>EMNLP 2022</span>", "Conversational chains of dependent numerical questions", "Long reasoning chains remain hard"],
         ["<b>DocFinQA</b> " + cite("docfinqa") + "<br><span class='tiny'>ACL 2024</span>", "FinQA questions over full filings (~123k words)", "Retrieval and long-context LLMs struggle"],
         ["<b>FinanceBench</b> " + cite("financebench") + "<br><span class='tiny'>arXiv 2023</span>", "Open-book QA over public-company filings", "GPT-4-Turbo + retrieval: 81% wrong or refused"],
         ["<b>IndFin-Bench / IndiaFinBench</b> " + cite("indfin", "indiafin") + "<br><span class='tiny'>2026</span>", "Indian filings (100 look-up Qs) / SEBI-RBI regulatory text (406 Qs)", "Recent Indian benchmarks; little multi-step calculation"]]),
        lead="Gap between the best systems and human experts is still ~30 points.")
    d.add("Literature 2/6", "Prompting strategies for multi-step reasoning", '<div class="cols c2"><div>' + ul([
        f"<b>Few-shot prompting</b> {cite('gpt3')}: in-context examples, no training.",
        f"<b>Chain-of-Thought</b> {cite('cot')}: exemplars show intermediate steps; gains emerge with scale.",
        f"<b>Zero-shot CoT</b> {cite('zscot')}: “Let's think step by step” — GSM8K 10.4 → 40.7%.",
        f"<b>Self-Consistency</b> {cite('sc')}: sample many paths, majority vote — +17.9 pts GSM8K.",
    ]) + "</div><div>" + ul([
        f"<b>Least-to-most</b> {cite('l2m')}, <b>Decomposed prompting</b> {cite('decomp')}, <b>Plan-and-solve</b> {cite('pands')}: split into sub-problems / plans.",
        f"<b>EEDP</b> {cite('eedp')}: Elicit → Extract → Decompose → Predict for financial tables; matches or beats CoT/PoT on 4 financial datasets.",
    ]) + '<div class="callout" style="margin-top:10px"><b>Takeaway:</b> structure in the prompt helps, but benefits depend on model size and task — they must be measured, not assumed, for small models on financial data.</div></div></div>')
    d.add("Literature 3/6", "Program-aided reasoning: let Python do the arithmetic",
          '<div class="cols c46"><div>' + ul([
              f"<b>Program-of-Thought</b> {cite('pot')}: the model writes Python; the interpreter computes.",
              f"<b>PAL</b> {cite('pal')}: beats much larger CoT models on math.",
              f"<b>Binder</b> {cite('binder')}: binds LMs to SQL / Python over tables.",
              f"<b>Number checks:</b> VeriFin {cite('verifin')} verifies operands against XBRL facts with a solver; DCRC {cite('dcrc')} trains an evidence auditor. Plain PoT trusts its numbers.",
          ], cls="small") + f'</div><div class="fig">{img("build/fig/lit_gap.png", "width:100%;margin-top:6px")}</div></div>')
    d.add("Literature 4/6", "Automated prompt optimization", table(
        ["Method", "How it optimizes", "Reported effect"],
        [["<b>APE</b> " + cite("ape"), "LLM proposes candidate instructions; best by score", "Human-level instructions"],
         ["<b>OPRO</b> " + cite("opro"), "LLM sees past prompts + scores, proposes better ones", "Up to +8% GSM8K, +50% BBH vs human prompts"],
         ["<b>DSPy</b> " + cite("dspy"), "Declarative LM programs compiled by optimizers (e.g. BootstrapFewShot keeps correct self-generated demos)", ">25% (GPT-3.5) and >65% (Llama-2-13B) over standard few-shot"],
         ["<b>MIPROv2</b> " + cite("mipro"), "Jointly searches instructions + demos with a Bayesian surrogate on minibatches", "Up to +13% accuracy (Llama-3-8B), best on 5 of 6 programs"],
         ["<b>TextGrad</b> " + cite("textgrad"), "LLM critiques errors (“textual gradients”); optimizer rewrites the prompt", "GPT-4o GPQA 51% → 55%"]]),
        lead="We found no evaluation of these on financial table-text reasoning against strong hand-written prompts.")
    d.add("Literature 5/6", "Tables, retrieval and robustness", '<div class="cols c2"><div>' + ul([
        f"<b>Table serialization</b> {cite('tablellm')}: Markdown vs JSON vs HTML vs text changes LLM accuracy on structural tasks.",
        f"<b>BM25</b> {cite('bm25')} (lexical) + <b>Sentence-BERT</b> {cite('sbert')} embeddings in <b>FAISS</b> {cite('faiss')} (semantic).",
        f"<b>Reciprocal Rank Fusion</b> {cite('rrf')}: simple, strong fusion of rankers; <b>RAG</b> {cite('rag')} grounds generation in retrieved evidence.",
    ]) + "</div><div>" + ul([
        f"<b>GSM-Symbolic</b> {cite('gsmsym')}: changing only the numbers lowers accuracy → models partly pattern-match. Public benchmarks may be memorized.",
        f"<b>Statistics for NLP</b> {cite('dror')}: paired tests (McNemar {cite('mcnemar')}), bootstrap CIs {cite('bootstrap')}, multiple-comparison correction {cite('holm')} — small test sets need them.",
    ]) + "</div></div>")
    d.add("Literature 6/6", "Domain models vs. prompting",
          '<div class="cols c2">' + '<div class="card"><h3>Train a finance model</h3>' + ul([
              f"<b>BloombergGPT</b> {cite('bloomberggpt')}: 50B parameters, 363B finance tokens + 345B general tokens.",
              f"<b>TAT-LLM</b> {cite('tatllm')}: fine-tuned LLaMA-2-7B (extractor → reasoner → executor) beats GPT-4 on FinQA / TAT-QA / TAT-DQA.",
              "Cost: large curated data, GPU training, retraining for every new model.",
          ], cls="small") + '</div><div class="card accent"><h3>Prompt + optimize a general model (our focus)</h3>' + ul([
              f"No training; works with any new model (e.g. <b>Qwen3</b> {cite('qwen3')}, 0.6B–235B, thinking / non-thinking modes).",
              "Runs on a laptop with local models → data never leaves the machine.",
              "Question: how close can prompting + optimization get, and at what cost?",
          ], cls="small") + "</div></div>")
    d.add("Literature summary", "Comparison matrix: what existing work covers", '<div class="dense">' + matrix_table() + '</div>' +
          '<p class="note" style="margin-top:8px">✓ addressed · ◐ partially (dataset-specific programs / tables not financial) · – not a focus of the work</p>')
    d.add("Research gaps", "Six gaps this project addresses", '<div class="cols c3">' + "".join(
        f'<div class="card"><h3 style="font-size:20px">{i + 1}. {t}</h3><p style="font-size:17.5px">{x}</p></div>' for i, (t, x) in enumerate(GAPS)) + "</div>")
    d.add("Proposed approach", "One controlled pipeline — only the prompt changes", D.pipeline() +
          '<div class="cols c3" style="margin-top:6px">'
          '<div class="card"><h3>6 manual strategies</h3><p>direct · zero/few-shot CoT · decomposition · Program-of-Thought · Self-Consistency (×5)</p></div>'
          '<div class="card"><h3>3 automated optimizers</h3><p>DSPy BootstrapFewShot · DSPy MIPROv2 · TextGrad (trained on FinQA train/dev only)</p></div>'
          '<div class="card accent"><h3>1 new method (VPSC)</h3><p>5 programs → sandbox → reject programs using numbers not found in the report → vote</p></div></div>')
    d.add("Novelty", "What is new in this project", '<div class="cols c2"><div>' + ul([
        f"<b>VPSC — Verified Program Self-Consistency</b>: Program-of-Thought + self-consistency + a training-free <i>grounding check</i> (every number in the code must appear in the report, allowing unit rescaling) — lighter than recent verifiers {cite('verifin', 'dcrc')}. Its ablation (same 5 programs, no check) isolates the effect exactly.",
        f"<b>Indian calculation set</b>: 44 multi-step questions over Titan, Asian Paints, Marico and Pidilite statements (₹ crore/lakh); gold answers computed from formulas — complements look-up benchmarks {cite('indfin')}.",
    ]) + "</div><div>" + ul([
        "<b>Manual vs automated prompting, head-to-head</b> on the same questions, scorer and models, with one-time optimization cost reported.",
        "<b>Cost-aware, statistically tested benchmark</b>: tokens, latency, bootstrap CIs, McNemar + Holm.",
        "<b>Diagnosis, not just accuracy</b>: rule-based error taxonomy and a numerical-perturbation memorization test.",
        "<b>Auditable web app</b>: evidence rows, code, trace, votes and exact prompt for every answer.",
    ]) + "</div></div>")
    d.add("Data, tools & evaluation", "Plan for datasets, tools and metrics", '<div class="cols c3">'
          '<div class="card"><h3>Datasets</h3>' + ul(["FinQA test (1,147 Q)", "TAT-QA arithmetic test (699 Q)", "Indian set (44 Q, ours)", "FinQA train/dev for few-shot & optimization only"], cls="small") + "</div>"
          '<div class="card"><h3>Tools</h3>' + ul(["Python 3.13, Ollama (Qwen3-1.7B / 8B)", "DSPy, TextGrad, LiteLLM", "rank-bm25, Sentence-Transformers, FAISS", "pdfplumber/pypdf, Streamlit, pytest"], cls="small") + "</div>"
          '<div class="card"><h3>Metrics</h3>' + ul(["Execution accuracy (0.5% tolerance), exact match, F1", "Format / code failure rates", "Tokens, latency, tokens per correct answer", "Bootstrap 95% CI, McNemar + Holm"], cls="small") + "</div></div>")
    d.add("Expected outcomes", "Deliverables at Review 3", ul([
        "A <b>reproducible benchmark</b> quantifying accuracy–cost trade-offs of prompting and optimization strategies across two model sizes.",
        "Evidence on whether <b>automated optimization</b> beats careful manual prompts — and its one-time cost.",
        "An <b>error taxonomy and robustness analysis</b> (perturbation, table formats, retrieval) showing where LLMs fail in financial calculations.",
        "A new verified strategy (<b>VPSC</b>) and a new <b>Indian test set</b>.",
        "An <b>interactive web application</b> with evidence-grounded, auditable answers, and a <b>report in IEEE format</b>.",
    ]))
    keys1 = ["finqa", "tatqa", "convfinqa", "docfinqa", "financebench", "bloomberggpt", "tatllm", "eedp", "gpt3", "cot", "zscot", "sc", "l2m", "decomp", "pot", "pal", "ape"]
    keys2 = [k for k in ["opro", "dspy", "mipro", "textgrad", "tablellm", "bm25", "sbert", "faiss", "rrf", "rag", "gsmsym", "qwen3", "mcnemar", "bootstrap", "dror", "holm", "binder", "pands"]]
    d.add("References", "References (1/2)", ref_list_html("refs", keys1))
    d.add("References", "References (2/2)", ref_list_html("refs", keys2))
    d.raw('<section class="slide section-slide"><div class="kicker">Review 1</div><h2>Thank you — questions?</h2>'
          '<p>FinReason: numerical reasoning over financial reports with prompting, optimization and verification.</p></section>')
    return page(f"{LABEL} slides", SLIDE_CSS, d.html())


# ------------------------------------------------------------------------------------------
# Report
# ------------------------------------------------------------------------------------------
def report():
    lit_table = table(["Ref.", "Work", "Approach / data", "Key finding", "Use in this project"],
                      [[cite(k), w, a, f, u] for k, w, a, f, u in LIT_ROWS], widths=[6, 17, 29, 27, 21])
    gaps = "".join(f"<li><b>{t}.</b> {x}</li>" for t, x in GAPS)
    body = cover("Review 1", "Idea Presentation &amp; Literature Survey", "Problem definition, objectives, survey of related work, research gaps and proposed approach") + f"""
<h1 class="doc-title">Contents</h1>
<ol class="toc">
<li>Introduction</li><li>Problem statement and scope</li><li>Motivation</li><li>Objectives and research questions</li>
<li>Literature survey</li><li>Comparison of existing work and research gaps</li><li>Proposed approach</li>
<li>Datasets, tools and evaluation plan</li><li>Expected outcomes</li><li>References</li></ol>

<h2>1. Introduction</h2>
<p>Financial reports — annual reports, 10-K filings, earnings releases — communicate a company's performance through a mix of
tables (statements of profit and loss, balance sheets, multi-year highlights) and narrative text. Analysts routinely ask
<i>numerical</i> questions of these documents: How much did revenue grow? What was the operating margin? What is the current ratio,
the interest coverage, the five-year CAGR? Answering such a question requires four distinct skills: (i) locating the right evidence
among dozens of rows and paragraphs, (ii) extracting values with the correct unit, scale and sign (millions vs. billions, ₹ crore vs. lakh,
bracketed negatives), (iii) applying the right domain formula, and (iv) carrying out multi-step arithmetic without error.</p>
<p>Large Language Models (LLMs) write fluent financial prose, but they remain unreliable at this kind of numerical reasoning. On the FinQA
benchmark the best fine-tuned model of the original paper reached 61.24% execution accuracy against 91.16% for financial experts {cite("finqa")};
on FinanceBench, GPT-4-Turbo with a retrieval system answered 81% of the evaluated questions incorrectly or refused to answer {cite("financebench")}.
Prompt engineering offers a cheap lever: Chain-of-Thought {cite("cot")}, Self-Consistency {cite("sc")} and Program-of-Thought {cite("pot")} improve
multi-step reasoning without any training, and recent frameworks such as DSPy {cite("dspy")}, MIPROv2 {cite("mipro")} and TextGrad {cite("textgrad")}
promise to optimize prompts automatically. This project, <b>FinReason</b>, systematically measures how far these techniques take small and
mid-sized open models on financial numerical reasoning, what they cost, where they fail, and whether a verification step can fix the dominant failure.</p>

<h2>2. Problem statement and scope</h2>
<div class="box"><p><b>Problem statement.</b> Given a page of a financial report (a table and its surrounding text) and a natural-language question
that requires numerical reasoning, produce the correct numeric answer together with a transparent evidence and calculation trace; and determine,
through controlled experiments, which prompting strategies and automated prompt-optimization methods make LLMs most accurate, reliable and
cost-efficient at this task — for small local and larger models, on public benchmarks and on unseen Indian annual reports.</p></div>
<h3>2.1 Formal task definition</h3>
<p>Each instance is a tuple (<i>T</i>, <i>P</i>, <i>q</i>, <i>a</i>) where <i>T</i> is a table (a header row and data rows), <i>P</i> a list of text
sentences or paragraphs, <i>q</i> a question and <i>a</i> the gold answer (a real number or yes/no). A system <i>f</i> maps (<i>T</i>, <i>P</i>, <i>q</i>) to a
prediction <i>â</i>. The prediction is correct when it is within 0.5% of <i>a</i>, or equals <i>a</i> rounded to the precision <i>a</i> is written with;
for percentage questions both the percent (12.5) and fraction (0.125) forms are accepted, because FinQA stores percentages as fractions
while TAT-QA stores them as percent numbers.</p>
<h3>2.2 Scope</h3>
<ul><li><b>In scope:</b> arithmetic questions over a single report page (FinQA, the arithmetic subset of TAT-QA, our Indian set); six manual
prompting strategies; three automated optimizers; two local model sizes (Qwen3-1.7B and Qwen3-8B {cite("qwen3")}), with API models supported by the code;
evidence retrieval within the page; robustness and error analysis; a web application.</li>
<li><b>Out of scope:</b> fine-tuning or training models; span-extraction and counting questions; search over whole 300-page reports;
real-time market data.</li></ul>

<h2>3. Motivation</h2>
<ul>
<li><b>Accuracy matters.</b> A wrong growth rate or ratio silently propagates into investment, credit and audit decisions. The ~30-point gap between
the best systems and experts on FinQA and TAT-QA {cite("finqa", "tatqa")} shows the problem is far from solved.</li>
<li><b>Answers must be auditable.</b> Financial users need to see which numbers were used and how they were combined — not only a final number.</li>
<li><b>Privacy and cost favour small local models.</b> Many organizations cannot send unpublished financial data to external APIs. A 2–8B-parameter model
running on a laptop costs nothing per query, but its reasoning ability is limited — prompting may be the cheapest way to compensate.</li>
<li><b>Prompting choices are made by folklore.</b> Practitioners pick CoT or few-shot prompts by habit. Whether automated optimization beats a careful
manual prompt, and whether code execution beats free-text reasoning for small models, should be measured with proper statistics.</li>
<li><b>Regional conventions are barely tested.</b> The main benchmarks use US filings; recent Indian benchmarks (2026) cover filing look-up {cite("indfin")} and
regulatory text {cite("indiafin")}. Indian reports use ₹ crore and lakh (1 crore = 100 lakh = 10 million), Indian digit grouping (1,00,000), bracketed negatives
and Ind AS statement layouts — multi-step calculation over them is a realistic test of generalization.</li>
</ul>

<h2>4. Objectives and research questions</h2>
<h3>4.1 Objectives</h3>
<ol>{"".join(f"<li>{o}</li>" for o in OBJECTIVES)}</ol>
<h3>4.2 Research questions</h3>
{table(["", "Research question"], [[f"<b>{a}</b>", b] for a, b in RQS])}

<h2>5. Literature survey</h2>
<p>We surveyed work in six themes: (5.1) benchmarks for financial numerical reasoning, (5.2) prompting strategies for multi-step reasoning,
(5.3) program-aided reasoning, (5.4) automated prompt optimization, (5.5) tables, retrieval and robustness, and (5.6) domain-specific models.
Table 1 at the end of this section summarizes each work and how it is used in this project.</p>

<h3>5.1 Financial question-answering benchmarks</h3>
<p><b>FinQA</b> {cite("finqa")} introduced 8,281 question–answer pairs written by financial experts over earnings reports of S&amp;P 500 companies.
Each question comes with a gold <i>reasoning program</i> in a small domain-specific language (e.g. <code>subtract(5829, 5735), divide(#0, 5735)</code>) and
the supporting facts. The authors' FinQANet (a RoBERTa-large retriever plus a program generator) achieved 61.24% execution accuracy on the test set,
compared with 91.16% for human experts, establishing a large gap. FinQA's gold programs let us identify exactly which operands a correct
solution needs — we use them for operand-level error analysis and for building numerically perturbed questions.</p>
<p><b>TAT-QA</b> {cite("tatqa")} contains 16,552 questions over 2,757 hybrid contexts (a table plus at least two paragraphs) from real financial reports, with
answer types span, multi-span, counting and arithmetic, and a scale label (thousand, million, percent). The proposed TagOp model, which tags
evidence cells and applies symbolic aggregation operators, reached 50.1% exact match and 58.0% F1, far below human performance (84.1% EM, 90.8% F1).
About 42% of TAT-QA questions are arithmetic; we use this subset. <b>ConvFinQA</b> {cite("convfinqa")} extends FinQA to conversations in which
later questions depend on earlier answers, showing that long chains of numerical reasoning remain difficult. <b>DocFinQA</b> {cite("docfinqa")} re-poses
7,437 FinQA questions over full filings averaging about 123,000 words, and finds that both retrieval pipelines and long-context LLMs struggle —
evidence location is itself a major failure point. <b>FinanceBench</b> {cite("financebench")} evaluates open-book QA over public-company filings and reports
that GPT-4-Turbo with retrieval answered 81% of the evaluated questions incorrectly or refused, illustrating that even frontier models are unreliable
in this domain. Indian data has only recently been addressed: <b>IndFin-Bench</b> {cite("indfin")} (April 2026, an open dataset released by a company) has 100
questions over Indian listed companies' filings that are mostly fact look-up, and <b>IndiaFinBench</b> {cite("indiafin")} (2026) has 406 questions over SEBI and RBI
regulatory text, 92 of them numerical. Neither targets multi-step calculation over annual-report statements with ₹ crore/lakh conversions.</p>
<p>Srivastava et al. {cite("eedp")} evaluate LLM mathematical reasoning across TAT-QA, FinQA, ConvFinQA and MultiHiertt, analysing how accuracy changes
with table complexity and the number of reasoning steps. They propose <b>EEDP</b> (Elicit → Extract → Decompose → Predict), a prompt that first
elicits domain knowledge, then extracts the relevant values, decomposes the computation and predicts the answer; it matches or outperforms
CoT and PoT baselines. Our decomposition strategy (Knowledge → Extract → Decompose → Answer) follows this design.</p>

<h3>5.2 Prompting strategies for multi-step reasoning</h3>
<p>Brown et al. {cite("gpt3")} showed that large models can perform tasks from a few in-context examples (few-shot prompting). Wei et al. {cite("cot")}
found that exemplars containing intermediate reasoning steps — <b>Chain-of-Thought (CoT)</b> — strongly improve arithmetic and symbolic reasoning, an
ability that emerges with scale. Kojima et al. {cite("zscot")} showed that simply appending “Let's think step by step” elicits reasoning without exemplars
(zero-shot CoT), raising InstructGPT's accuracy on MultiArith from 17.7% to 78.7% and on GSM8K from 10.4% to 40.7%. <b>Self-Consistency</b> {cite("sc")}
samples several reasoning paths at non-zero temperature and returns the most frequent answer, improving GSM8K by 17.9 points over greedy CoT.
Decomposition methods — <b>least-to-most prompting</b> {cite("l2m")}, <b>decomposed prompting</b> {cite("decomp")} and <b>plan-and-solve prompting</b>
{cite("pands")} — first break a problem into sub-problems or an explicit plan, which helps on problems harder than the exemplars. These results come
mostly from very large models on math word problems; whether they transfer to small models reading financial tables is an open, empirical question.</p>

<h3>5.3 Program-aided reasoning</h3>
<p>Free-text reasoning mixes two very different jobs: deciding <i>what</i> to compute and actually computing it. <b>Program-of-Thought (PoT)</b>
{cite("pot")} asks the model to express the reasoning as a Python program and delegates computation to an interpreter. On FinQA with Codex, PoT
improved accuracy from 40.4% (CoT) to 64.5%, and from 44.4% to 68.1% with self-consistency; similar gains held on ConvFinQA and TAT-QA.
<b>PAL</b> {cite("pal")} independently showed that program-aided LMs outperform much larger CoT models on math, and <b>Binder</b> {cite("binder")} binds LMs to
SQL/Python for table reasoning. A limitation shared by these methods is that the generated program is trusted completely: if the model copies a
wrong number or invents one, the interpreter computes the wrong answer exactly. Two recent works verify numbers: <b>VeriFin</b> {cite("verifin")} grounds
the operands of LLM-generated financial claims in filed XBRL facts and checks the calculation with the Z3 solver, reporting zero false accepts; <b>DCRC</b>
{cite("dcrc")} trains a data-centric agent that audits evidence and compiles executable programs. Both need structured filing data, a solver or task-specific
training; plain PoT pipelines over report tables still have no lightweight check that a program's numbers occur in the source.</p>
<figure>{img("build/fig/lit_gap.png", "width:88%")}<div class="caption">Fig. 1. Published FinQA test results (execution accuracy) from {cite("finqa")} and {cite("pot")}.</div></figure>

<h3>5.4 Automated prompt optimization</h3>
<p>Hand-written prompts are brittle and model-specific, which motivated methods that search for prompts automatically. <b>APE</b> {cite("ape")} lets an
LLM propose candidate instructions and keeps the best-scoring one, matching human-written instructions. <b>OPRO</b> {cite("opro")} treats the LLM as an
optimizer that sees previous prompts with their scores and proposes better ones, outperforming human-designed prompts by up to 8% on GSM8K and
up to 50% on Big-Bench Hard. <b>DSPy</b> {cite("dspy")} replaces prompt strings with declarative <i>signatures</i> and <i>modules</i> whose prompts are compiled by
optimizers; its BootstrapFewShot optimizer runs the program on training examples and keeps the traces that a metric marks correct as demonstrations.
DSPy pipelines outperformed standard few-shot prompting by over 25% (GPT-3.5) and 65% (Llama-2-13B-chat). <b>MIPROv2</b> {cite("mipro")} jointly optimizes
instructions and demonstrations using program- and data-aware instruction proposals, minibatch evaluation and a Bayesian surrogate model,
outperforming baselines on five of six programs with Llama-3-8B by up to 13% accuracy. <b>TextGrad</b> {cite("textgrad")} generalizes back-propagation
to text: an LLM writes natural-language critiques of outputs (“textual gradients”) and an optimizer rewrites the variable (e.g. a system prompt)
accordingly; it improved, for example, GPT-4o's zero-shot accuracy on GPQA from 51% to 55%. We found no study that compares these methods with strong
hand-written prompts on financial table-text reasoning, or that reports their one-time optimization cost alongside the accuracy gain.</p>

<h3>5.5 Tables, retrieval and robustness</h3>
<p>How a table is linearized matters: Sui et al. {cite("tablellm")} show that the serialization format (e.g. Markdown, HTML, JSON-like formats)
and prompt choices significantly change LLM accuracy on structural table tasks, so the format must be treated as an experimental variable.
For evidence selection, the classic <b>BM25</b> ranking function {cite("bm25")} matches keywords, while <b>Sentence-BERT</b> {cite("sbert")} embeddings
indexed with <b>FAISS</b> {cite("faiss")} match meaning; <b>Reciprocal Rank Fusion</b> {cite("rrf")} combines rankings simply and robustly. Retrieval-augmented
generation {cite("rag")} grounds outputs in retrieved evidence. On robustness, <b>GSM-Symbolic</b> {cite("gsmsym")} re-instantiates GSM8K problems with new
values and finds that accuracy drops and varies even when only the numbers change — evidence that models partly pattern-match or have memorized
public benchmarks. FinQA and TAT-QA are public since 2021, so a similar numerical-perturbation test is needed. Finally, with test sets of a few
hundred questions, differences of a few points can be noise; Dror et al. {cite("dror")} recommend paired significance tests such as McNemar's test
{cite("mcnemar")}, with bootstrap confidence intervals {cite("bootstrap")} and multiple-comparison correction {cite("holm")}.</p>

<h3>5.6 Domain-specific models</h3>
<p>An alternative to prompting is to build finance-specific models. <b>BloombergGPT</b> {cite("bloomberggpt")} is a 50-billion-parameter model trained on a
363-billion-token financial corpus plus 345 billion general tokens. <b>TAT-LLM</b> {cite("tatllm")} fine-tunes LLaMA-2-7B on automatically generated
extractor–reasoner–executor traces and reports results above GPT-4 on FinQA, TAT-QA and TAT-DQA. These approaches are effective but need curated
data, GPU training and retraining for every new base model. General open models such as <b>Qwen3</b> {cite("qwen3")} (0.6B–235B parameters, with
switchable thinking and non-thinking modes) improve rapidly; this project studies the cheaper path of prompting and prompt optimization on such models.</p>

<p class="tcaption">Table 1. Summary of the surveyed literature.</p>
{lit_table}

<h2 class="newpage">6. Comparison of existing work and research gaps</h2>
<p>Table 2 compares representative works along the dimensions this project studies. We found no study that combines financial table-text data, a
controlled comparison of manual prompting strategies, automated prompt optimization, small local models, cost and latency, robustness testing and
regional (Indian) data.</p>
<p class="tcaption">Table 2. Coverage of existing work (✓ addressed, ◐ partially, – not a focus).</p>
{matrix_table()}
<h3>Research gaps</h3>
<ol>{gaps}</ol>

<h2>7. Proposed approach</h2>
<p>FinReason is built as one controlled pipeline in which only the prompting strategy changes (Fig. 2). Every question flows through the same stages:
load into a common format, build the context (full page, or top-<i>k</i> evidence retrieved with a hybrid BM25 + dense retriever), prompt the model,
execute any generated code in a sandbox, parse and score the answer, diagnose errors, and record everything for analysis and the web application.</p>
<figure>{D.pipeline()}<div class="caption">Fig. 2. The FinReason pipeline (one question).</div></figure>
<h3>7.1 Strategies compared</h3>
<ul>
<li><b>Manual:</b> direct answer; zero-shot CoT; few-shot CoT (three worked FinQA <i>train</i> examples); decomposition (Knowledge → Extract →
Decompose → Answer, after EEDP {cite("eedp")}); Program-of-Thought with sandboxed execution and one repair round; CoT Self-Consistency (5 samples).</li>
<li><b>Automated:</b> DSPy BootstrapFewShot and MIPROv2 compiling a Chain-of-Thought program; TextGrad optimizing the system prompt of zero-shot CoT.
All optimization uses FinQA train/dev only, so test sets are never seen.</li>
<li><b>Proposed — Verified Program Self-Consistency (VPSC):</b> sample five programs (one greedy, four at temperature 0.7), execute each in the
sandbox, reject programs that use a number not present in the report (allowing harmless constants and unit rescaling), and majority-vote
the remaining answers. The same five programs voted without the check form the ablation (PoT Self-Consistency), so the effect of verification is
measured exactly at no extra model cost.</li></ul>
<h3>7.2 Analyses</h3>
<ul><li>Accuracy with 95% bootstrap CIs; paired McNemar tests against few-shot CoT with Holm correction.</li>
<li>Accuracy stratified by number of reasoning steps and by evidence source (table / text / both).</li>
<li>Rule-based error taxonomy: no answer, code failure, sign, scale/unit, near miss, no work shown, evidence error, reasoning error.</li>
<li>Numerical perturbation of FinQA questions (operands changed by 10–30%, gold recomputed with the gold program) to test memorization.</li>
<li>Ablations: table format (Markdown/JSON/HTML/row text), retrieval vs full page, thinking mode on/off; token cost and latency per strategy.</li></ul>

<h2>8. Datasets, tools and evaluation plan</h2>
{table(["Item", "Plan"], [
    ["FinQA", "Test split (1,147 questions); a fixed random sample of 100 (seed 42) for every strategy so comparisons are paired; train/dev for exemplars and optimization."],
    ["TAT-QA", "Arithmetic questions of the test split (699); a fixed sample of 100 (seed 42)."],
    ["Indian set (new)", "44 questions over statements of Titan, Asian Paints, Marico and Pidilite (FY2023-24 / 2024-25); tables transcribed from the official PDFs; gold answers computed from formulas."],
    ["Models", "Qwen3-1.7B and Qwen3-8B, 4-bit, served locally by Ollama; API models (OpenAI, Groq, Gemini, OpenRouter, Anthropic) supported via one client."],
    ["Libraries", "DSPy, TextGrad, LiteLLM, rank-bm25, Sentence-Transformers (all-MiniLM-L6-v2), FAISS, pdfplumber/pypdf, pandas, SciPy, matplotlib, Streamlit, pytest."],
    ["Metrics", "Execution accuracy (0.5% tolerance; 1% also reported), exact match (2 d.p.), token F1, format- and code-failure rates, calls, tokens, latency, tokens per correct answer, one-time optimization cost."],
    ["Statistics", "95% percentile bootstrap CIs (2,000 resamples), exact McNemar test on paired questions, Holm–Bonferroni correction."],
], cls="t kv")}

<h2>9. Expected outcomes</h2>
<ul><li>A reproducible benchmark quantifying accuracy–cost trade-offs of six manual strategies, three optimizers and VPSC across two model sizes.</li>
<li>Evidence on whether automated prompt optimization beats careful manual prompting, and at what one-time cost.</li>
<li>An error taxonomy and robustness analysis (perturbation, table format, retrieval) showing where LLMs fail in financial calculations.</li>
<li>A new curated Indian annual-report test set and a new verification-based strategy (VPSC).</li>
<li>An interactive web application with evidence-grounded, auditable answers; a final report in IEEE format.</li></ul>

<h2 class="newpage">10. References</h2>
{ref_list_html()}
"""
    return page(f"{LABEL} report", REPORT_CSS, body, running="FinReason · Review 1 · Idea presentation & literature survey")
