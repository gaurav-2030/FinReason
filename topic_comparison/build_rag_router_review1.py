"""Review 1 deck (idea & literature survey) for the alternative topic: Cost-Aware Adaptive RAG Router.
Uses the FinReason slide template.  Run:  python topic_comparison/build_rag_router_review1.py
Writes RAGRouter_Review1_Slides.html / .pdf / .pptx next to this file."""
import html as H
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "reviews" / "src"))

import common  # noqa: E402
from common import (AMBER, CHROME, SLIDE_CSS_CONCISE, TEAM, TEAL, Deck, arrow, box, page, path_arrow, render_pdf, svg,  # noqa: E402
                    table, text, title_slide, ul)
from diagrams import AMBER_FILL, BLUE_FILL, GREEN_FILL, TEAL_FILL  # noqa: E402

common.TITLE = "Cost-Aware Adaptive RAG Router"
common.SUBTITLE = "Choosing the cheapest retrieval pipeline per query to cut tokens, latency and cost at fixed accuracy"
common.SHORT = "RAG Router"

REFS = [
    ("rag", 'P. Lewis <i>et al.</i>, "Retrieval-augmented generation for knowledge-intensive NLP tasks," in <i>NeurIPS</i>, 2020.'),
    ("dpr", 'V. Karpukhin <i>et al.</i>, "Dense passage retrieval for open-domain question answering," in <i>Proc. EMNLP</i>, 2020.'),
    ("bm25", 'S. Robertson and H. Zaragoza, "The probabilistic relevance framework: BM25 and beyond," <i>Found. Trends Inf. Retr.</i>, 2009.'),
    ("rrf", 'G. V. Cormack, C. L. A. Clarke, and S. Büttcher, "Reciprocal rank fusion outperforms Condorcet and individual rank learning methods," in <i>Proc. SIGIR</i>, 2009.'),
    ("monobert", 'R. Nogueira and K. Cho, "Passage re-ranking with BERT," arXiv:1901.04085, 2019.'),
    ("mallen", 'A. Mallen <i>et al.</i>, "When not to trust language models: Investigating effectiveness of parametric and non-parametric memories," in <i>Proc. ACL</i>, 2023.'),
    ("flare", 'Z. Jiang <i>et al.</i>, "Active retrieval augmented generation," in <i>Proc. EMNLP</i>, 2023.'),
    ("selfrag", 'A. Asai, Z. Wu, Y. Wang, A. Sil, and H. Hajishirzi, "Self-RAG: Learning to retrieve, generate, and critique through self-reflection," in <i>ICLR</i>, 2024.'),
    ("ircot", 'H. Trivedi, N. Balasubramanian, T. Khot, and A. Sabharwal, "Interleaving retrieval with chain-of-thought reasoning for knowledge-intensive multi-step questions," in <i>Proc. ACL</i>, 2023.'),
    ("adaptiverag", 'S. Jeong, J. Baek, S. Cho, S. J. Hwang, and J. C. Park, "Adaptive-RAG: Learning to adapt retrieval-augmented large language models through question complexity," in <i>Proc. NAACL</i>, 2024.'),
    ("frugalgpt", 'L. Chen, M. Zaharia, and J. Zou, "FrugalGPT: How to use large language models while reducing cost and improving performance," arXiv:2305.05176, 2023.'),
    ("routellm", 'I. Ong <i>et al.</i>, "RouteLLM: Learning to route LLMs with preference data," arXiv:2406.18665, 2024.'),
    ("mbarag", 'X. Tang <i>et al.</i>, "MBA-RAG: A bandit approach for adaptive retrieval-augmented generation through question complexity," in <i>Proc. COLING</i>, 2025.'),
    ("uncert", 'V. Moskvoretskii <i>et al.</i>, "Adaptive retrieval without self-knowledge? Bringing uncertainty back home," in <i>Proc. ACL</i>, 2025.'),
    ("nq", 'T. Kwiatkowski <i>et al.</i>, "Natural Questions: A benchmark for question answering research," <i>TACL</i>, vol. 7, 2019.'),
    ("hotpot", 'Z. Yang <i>et al.</i>, "HotpotQA: A dataset for diverse, explainable multi-hop question answering," in <i>Proc. EMNLP</i>, 2018.'),
    ("2wiki", 'X. Ho, A.-K. Duong Nguyen, S. Sugawara, and A. Aizawa, "Constructing a multi-hop QA dataset for comprehensive evaluation of reasoning steps," in <i>Proc. COLING</i>, 2020.'),
]
NUM = {k: i + 1 for i, (k, _) in enumerate(REFS)}


def cite(*keys):
    return '<span class="tiny" style="font-size:.8em">[' + ", ".join(str(NUM[k]) for k in keys) + "]</span>"


def tk(s):
    return f'<div class="takeaway">{s}</div>'


def cards(items, n=2, h3=21):
    return (f'<div class="cols c{n}">' + "".join(f'<div class="card"><h3 style="font-size:{h3}px">{a}</h3><p>{b}</p></div>' for a, b in items)
            + "</div>")


def qbox(head, body, style=""):
    return (f'<div><div style="font-size:16px;font-weight:700;color:#13294b;margin:0 0 5px">{head}</div>'
            f'<div class="qbox" style="font-size:15.5px;line-height:1.45;{style}">{body}</div></div>')


def pipeline_svg():
    cy = 185
    o = [box(8, cy - 43, 150, 86, "Query", ["NQ / HotpotQA /", "2WikiMultiHopQA"], fill=BLUE_FILL, stroke="#9fb0c8"),
         box(206, cy - 55, 210, 110, "Router", ["up-front classifier", "or cascade controller", "(confidence-based)"], fill=AMBER_FILL, stroke="#9fb0c8")]
    ps = [("P0 · No retrieval", ["LLM answers from memory"]), ("P1 · Dense retrieval", ["embed → FAISS top-5"]),
          ("P2 · Hybrid + rerank", ["BM25 + dense → RRF →", "cross-encoder → top-5"])]
    for i, (t, ls) in enumerate(ps):
        y = 10 + i * 130
        o.append(box(476, y, 260, 86, t, ls, fill=TEAL_FILL, stroke="#9fb0c8"))
        o.append(arrow(416, cy, 474, y + 43))
        o.append(arrow(736, y + 43, 794, cy))
        if i < 2:
            o.append(arrow(560, y + 88, 560, y + 128, color=AMBER, dash="5 4"))
            o.append(text(572, y + 113, "escalate if unsure (cascade)", fs=12, color=AMBER, anchor="start"))
    o += [box(796, cy - 43, 160, 86, "LLM answer", ["Qwen3-8B / API model"], fill=GREEN_FILL, stroke="#9fb0c8"),
          box(1000, cy - 55, 156, 110, "Score + log", ["EM / F1", "tokens · latency", "$ and GPU-s"], fill=BLUE_FILL, stroke="#9fb0c8"),
          arrow(158, cy, 204, cy), arrow(956, cy, 998, cy)]
    return svg(1164, 372, "".join(o), style="width:100%;margin-top:6px")


def deck():
    d = Deck("Review 1")
    d.raw(title_slide("Review 1", "Idea & literature survey"), "Title & introductions")

    d.add("The problem", "Not every question needs the same retrieval", table(
        ["Question (illustrative)", "Type", "What it needs", "Cheapest pipeline that suffices"], [
            ["“who wrote pride and prejudice”", "NQ, popular fact", "Nothing — the LLM already knows", "<b>P0</b> no retrieval"],
            ["“who played the coach in a 1990s indie film”", "NQ, long-tail fact", "One relevant passage", "<b>P1</b> dense retrieval"],
            ["“Were Scott Derrickson and Ed Wood of the same nationality?”", "HotpotQA, 2-hop", "Two passages, ranked precisely", "<b>P2</b> hybrid + rerank"]],
        widths=[36, 18, 24, 22]) +
          '<div class="cols c3" style="margin-top:22px">' + "".join(
              f'<div class="card"><div class="big" style="font-size:40px">{a}</div><div class="stat lbl">{b}</div></div>' for a, b in [
                  ("Over-pay", "Always using the strongest pipeline wastes tokens and reranker time on easy questions"),
                  ("Under-perform", "Always using the cheapest pipeline fails multi-hop and long-tail questions"),
                  ("Per query", "The right choice depends on the question — so decide it per query")]) + "</div>" +
          tk("One fixed RAG pipeline either over-pays on easy questions or fails hard ones."))

    d.add("Problem statement", "Problem statement",
          '<div class="card accent" style="font-size:24px;line-height:1.45">Build a router that, for every query, chooses the <b>cheapest retrieval pipeline that still answers '
          'correctly</b> — minimising tokens, latency and cost per query at a fixed accuracy target.</div>' +
          '<div class="cols c3" style="margin-top:24px">' + "".join(f'<div class="card"><h3>{a}</h3><p>{b}</p></div>' for a, b in [
              ("Input", "An open-domain question; a Wikipedia passage index; three pipelines of rising cost"),
              ("Output", "The answer, the pipeline used, and its tokens, latency and $ / GPU-seconds"),
              ("Target", "Accuracy within ~1 point of always using the best pipeline, at much lower cost")]) + "</div>" +
          tk("RAG treated as a cost-versus-accuracy optimisation, not a single fixed pipeline."))

    d.add("Objectives", "Objectives", '<ol style="padding-left:28px">' + "".join(
        f"<li style='font-size:25px;margin-bottom:17px'>{x}</li>" for x in [
            "Build three pipelines of increasing cost over one Wikipedia index: no retrieval, dense, hybrid + reranking",
            "Compare <b>up-front routing</b> (classify the query first) with a <b>confidence-based cascade</b> (try cheap first, escalate)",
            "Measure cost with one realistic model — tokens, embeddings, reranker and search time, index size — in $ and GPU-seconds",
            "Test whether a tiny router works as well as an LLM router, and whether routers transfer to new domains"]) + "</ol>")

    d.add("Literature 1/3", "Retrieval building blocks", table(["Work", "Idea", "Key result / cost"], [
        ["<b>RAG</b> " + cite("rag"), "Retriever + generator trained together", "State of the art on open-domain QA (NQ) in 2020"],
        ["<b>DPR</b> " + cite("dpr"), "Dense dual-encoder passage retrieval", "+9–19 pts top-20 accuracy over BM25"],
        ["<b>BM25</b> " + cite("bm25"), "Sparse lexical matching", "Cheap (CPU); strong on rare names and entities"],
        ["<b>RRF</b> " + cite("rrf"), "Fuse rankings: Σ 1 / (k + rank)", "Beats each individual ranker; no training"],
        ["<b>Cross-encoder rerank</b> " + cite("monobert"), "BERT scores each (query, passage) pair", "≈2× BM25 MRR@10 on MS MARCO — one forward pass per candidate"]],
        widths=[24, 38, 38]) +
          tk("Each extra stage buys accuracy with extra latency and compute — the trade-off a router can exploit."))

    d.add("Literature 2/3", "Adaptive retrieval — deciding when and how to retrieve", table(["Work", "How it decides", "Limitation for us"], [
        ["<b>Popularity-based</b> " + cite("mallen"), "Retrieve only for less popular entities", "Needs entity popularity; one binary choice"],
        ["<b>FLARE</b> " + cite("flare"), "Retrieve when upcoming tokens have low probability", "Many LLM calls; cost not reported in $"],
        ["<b>Self-RAG</b> " + cite("selfrag"), "Fine-tuned model emits “retrieve” / critique tokens", "Needs a specially trained model"],
        ["<b>IRCoT</b> " + cite("ircot"), "Interleaves retrieval with chain-of-thought (multi-hop)", "Strong but many retrieval + LLM calls"],
        ["<b>Adaptive-RAG</b> " + cite("adaptiverag"), "T5 classifier: no / single-step / multi-step; labels from model outcomes", "Up-front only; cost = steps and time"]],
        widths=[24, 42, 34]) +
          tk("Adaptive-RAG already routes on our datasets — our work must go beyond it, not replicate it."))

    d.add("Literature 3/3", "Cost-aware routing and cascades", table(["Work", "Idea", "Reported effect"], [
        ["<b>FrugalGPT</b> " + cite("frugalgpt"), "Cascade of LLMs; a scorer decides when to stop", "Matches GPT-4 with up to 98% lower cost"],
        ["<b>RouteLLM</b> " + cite("routellm"), "Router between a strong and a weak LLM, trained on preferences", "Over 2× cost reduction at similar quality"],
        ["<b>MBA-RAG</b> " + cite("mbarag"), "Multi-armed bandit picks the retrieval strategy; cost-penalised reward", "Fewer retrieval steps on NQ / HotpotQA / 2Wiki"],
        ["<b>Uncertainty study</b> " + cite("uncert"), "Compares many adaptive-retrieval and uncertainty methods", "Simple uncertainty signals are often as good, and cheaper"]],
        widths=[24, 44, 32]) +
          tk("Cost is usually counted as LLM calls or retrieval steps — reranker, embedding and index costs are ignored."))

    d.add("Datasets", "Datasets and corpus", table(["Dataset", "What it is", "Role in our study"], [
        ["<b>Natural Questions</b> " + cite("nq"), "Real Google search queries; answers in one Wikipedia passage", "Mostly single-hop → P0 / P1 should suffice"],
        ["<b>HotpotQA</b> " + cite("hotpot"), "113k multi-hop questions over 2 Wikipedia paragraphs (bridge, comparison)", "Router training set; needs P2 more often"],
        ["<b>2WikiMultiHopQA</b> " + cite("2wiki"), "Multi-hop with evidence paths (compositional, comparison, inference)", "Harder multi-hop; transfer test"],
        ["<b>University documents</b> (ours)", "Small domain corpus: PES handbooks and regulations", "Out-of-domain transfer test"]],
        widths=[26, 44, 30]) +
          '<p class="small" style="margin-top:14px">Corpus: Wikipedia split into 100-word passages (DPR dump) · ~500 test queries per dataset · separate train queries for router labels.</p>')

    d.add("Research gaps", "Gaps we address", cards([
        ("Up-front vs cascade", "Routing before answering and escalating after a cheap attempt are rarely compared under one cost model."),
        ("Unrealistic cost", "Papers count LLM calls or retrieval steps; reranker latency, embedding calls and index size are left out."),
        ("Router overhead", "If the router is itself an LLM, does it cost more than it saves?"),
        ("Transfer", "Routers are trained and tested on the same datasets; behaviour on new domains is unknown.")]))

    d.add("Approach", "One system — three pipelines, one router", pipeline_svg() +
          tk("Same questions, same index, same generator — only the routing decision changes."))

    d.add("Approach 1/5", "The three pipelines", '<div class="dense">' + table(
        ["Pipeline", "Components", "LLM calls", "Extra prompt tokens", "Main latency"], [
            ["<b>P0</b> No retrieval", "Question → LLM", "1", "0", "Generation only"],
            ["<b>P1</b> Dense", "Embed query (MiniLM / e5) → FAISS top-5 passages → LLM", "1 (+1 embedding)", "≈ 650", "Embedding + ANN search"],
            ["<b>P2</b> Hybrid + rerank", "BM25 top-50 + dense top-50 → RRF → cross-encoder → top-5 → LLM", "1 (+1 embedding, +100 reranker passes)", "≈ 650",
             "Cross-encoder on GPU"]], widths=[17, 39, 17, 12, 15]) + "</div>" +
          '<div class="cols c3" style="margin-top:18px">' + "".join(
              f'<div class="card"><h3 style="font-size:20px">{a}</h3><p>{b}</p></div>' for a, b in [
                  ("Shared", "One Wikipedia index, one prompt template, one generator LLM"),
                  ("Generator", "Qwen3-8B locally (Ollama) + one API model for $ prices"),
                  ("Framework", "LangChain runnables; every call logged with tokens and timings")]) + "</div>" +
          tk("Cost rises from P0 to P2 — the router's job is to use P2 only when it is needed."))

    d.add("Approach 2/5", "Two ways to route: up-front vs cascade", '<div class="cols c2" style="gap:24px">' +
          '<div class="card"><h3>Up-front router</h3><ol style="padding-left:22px;margin:0 0 10px">' + "".join(
              f"<li style='font-size:19px;margin-bottom:6px'>{x}</li>" for x in [
                  "Classify the query text → P0, P1 or P2", "Run only that pipeline", "Return the answer"]) + "</ol>" +
          ul(["<b>+</b> one pass, predictable latency", "<b>−</b> decides blind, before seeing any evidence"], cls="small") + "</div>" +
          '<div class="card accent"><h3>Cascade with escalation</h3><ol style="padding-left:22px;margin:0 0 10px">' + "".join(
              f"<li style='font-size:19px;margin-bottom:6px'>{x}</li>" for x in [
                  "Run P0 → confidence c₀", "If c₀ &lt; τ₀ → run P1 → c₁", "If c₁ &lt; τ₁ → run P2"]) + "</ol>" +
          ul(["<b>+</b> uses real evidence of difficulty", "<b>−</b> hard queries pay for every stage"], cls="small") + "</div></div>" +
          '<p class="small" style="margin-top:14px"><b>Confidence signals:</b> answer log-probability · self-consistency (agreement of 3 samples) · retrieval score gap (top-1 − top-2).</p>' +
          tk("Sweeping the thresholds τ traces a Pareto curve; we compare both designs at equal accuracy."))

    d.add("Approach 3/5", "Router labels from outcomes, and router size", '<div class="cols c2" style="gap:26px"><div>' +
          '<h3 style="font-size:21px;color:#13294b;margin:0 0 8px">Labels — no manual annotation</h3>' + table(
              ["Train query", "P0", "P1", "P2", "Label"], [
                  ["q₁ popular fact", "✓", "✓", "✓", "<b>P0</b>"], ["q₂ long-tail fact", "✗", "✓", "✓", "<b>P1</b>"],
                  ["q₃ two-hop", "✗", "✗", "✓", "<b>P2</b>"], ["q₄ unanswerable", "✗", "✗", "✗", "<b>P2</b>*"]], widths=[40, 12, 12, 12, 24]) +
          '<p class="tiny" style="margin-top:6px">Label = cheapest pipeline that answered correctly · *none correct → strongest pipeline</p></div><div>' +
          '<h3 style="font-size:21px;color:#13294b;margin:0 0 8px">Router models — small to large</h3>' + table(
              ["Router", "Runs on"], [["TF-IDF + logistic regression", "CPU, ~1 ms"], ["MiniLM / DistilBERT classifier", "CPU/GPU, ~5 ms"],
                                     ["Qwen3-1.7B, zero-shot prompt", "GPU, 1 short call"], ["Qwen3-8B, zero-shot prompt", "GPU, 1 short call"]],
              widths=[62, 38]) + "</div></div>" +
          tk("The router's own cost is charged to it — a router that costs more than it saves is a failure."))

    d.add("Approach 4/5", "A realistic cost model",
          qbox("Cost per query", "Cost(q) = p_in·T_in + p_out·T_out              <span style='color:#9fb3cf'># LLM tokens</span>\n"
                                 "        + p_emb·N_emb                          <span style='color:#9fb3cf'># embedding calls</span>\n"
                                 "        + p_gpu·(t_rerank + t_router)          <span style='color:#9fb3cf'># GPU-seconds</span>\n"
                                 "        + p_cpu·t_search                       <span style='color:#9fb3cf'># BM25 / FAISS search</span>\n"
                                 "        + index memory cost / queries served   <span style='color:#9fb3cf'># amortised index</span>") +
          '<div class="cols c3" style="margin-top:18px">' + "".join(
              f'<div class="card"><h3 style="font-size:20px">{a}</h3><p>{b}</p></div>' for a, b in [
                  ("Measured", "Tokens from the LLM API; wall-clock timings for every stage"),
                  ("Priced", "Public API prices per token; cloud GPU price per second"),
                  ("Reported", "$ per 1,000 queries and GPU-seconds per query, next to accuracy")]) + "</div>" +
          tk("One number per query that includes retrieval, reranking and the router — not just LLM calls."))

    d.add("Approach 5/5", "Experimental design", '<div class="cols c3" style="gap:20px">' + "".join(
        f'<div class="card"><h3 style="font-size:21px">{a}</h3>{ul(b)}</div>' for a, b in [
            ("Policies compared", ["Always P0 / P1 / P2", "Random routing", "Up-front router × 4 sizes", "Cascade × 3 confidence signals",
                                   "Oracle (cheapest correct) — upper bound"]),
            ("Metrics", ["Exact match and F1", "Tokens per query", "Latency p50 / p95", "$ per 1k queries, GPU-s per query", "Router accuracy vs oracle labels"]),
            ("Analysis", ["Accuracy–cost Pareto curves vs always-P2", "Cost saved at ≤ 1 pt accuracy drop", "Bootstrap 95% CIs, McNemar tests",
                          "Out-of-domain: train HotpotQA → test NQ, 2Wiki, university docs"])]).replace(
        "<li>", "<li style='font-size:17px;margin-bottom:6px'>") + "</div>" +
          tk("The headline result is a Pareto curve: same accuracy as the best pipeline, at a fraction of the cost."))

    d.add("Novelty", "What is new", ul([
        "<b>Up-front vs cascade, head-to-head</b> under one cost model, with three confidence signals.",
        "<b>A realistic cost model</b> in $ and GPU-seconds that includes reranker, embeddings, search and index — not just LLM calls.",
        "<b>Router-size study</b>: does a 1 ms classifier route nearly as well as an LLM, once each pays its own cost?",
        "<b>Out-of-domain transfer</b>: train on HotpotQA, test on NQ, 2Wiki and our university documents.",
        "Honest positioning: outcome-based labels follow Adaptive-RAG " + cite("adaptiverag") + "; our contribution is cost, cascades and transfer."]))

    d.add("References", "Key references", '<ol style="font-size:13.5px;line-height:1.35;padding-left:24px;columns:2;column-gap:36px">' +
          "".join(f"<li style='font-size:13.5px;margin-bottom:5px'>{r}</li>" for _, r in REFS) + "</ol>")
    d.raw('<section class="slide section-slide"><div class="kicker">Review 1</div><h2>Thank you — questions?</h2>'
          '<p>Cost-aware adaptive RAG router</p></section>', "Thank you & Q&A")
    G, SU, DH, HA = (n for n, _ in TEAM)
    d.arrange([(G, ["Title & introductions", "Not every question", "Problem statement", "Objectives"]),
               (SU, ["Retrieval building blocks", "Adaptive retrieval", "Cost-aware routing", "Datasets and corpus"]),
               (HA, ["Gaps we address", "One system", "The three pipelines", "Two ways to route"]),
               (DH, ["Router labels", "A realistic cost model", "Experimental design", "What is new"]),
               (None, ["Key references", "Thank you"])])
    return d


NOTES = {
    "Title": "Good morning. We are Gaurav, Sunay, Dhruvagouda and Hanshal. Our project is a cost-aware adaptive RAG router. "
             "Retrieval-augmented generation, or RAG, lets a language model look up documents before answering. But looking things up costs tokens, time and money. "
             "Our router decides, for every question, how much retrieval is really needed, so we spend as little as possible without losing accuracy.",
    "Not every question": "Here are three kinds of questions. A popular fact like who wrote Pride and Prejudice needs no retrieval: the model already knows it. "
             "A long-tail fact needs one good passage, so cheap dense retrieval is enough. A two-hop question from HotpotQA needs two passages ranked precisely, "
             "so it needs our most expensive pipeline. If we always use the expensive pipeline we over-pay; if we always use the cheap one we fail hard questions. "
             "So the choice must be made per query.",
    "Problem statement": "Our problem statement: build a router that picks the cheapest pipeline that still answers correctly, for every query. "
             "The input is a question, a Wikipedia index and three pipelines. The output is the answer plus exactly what it cost. "
             "Our target is accuracy within about one point of always using the best pipeline, at much lower cost.",
    "Objectives": "We have four objectives. First, build three pipelines of rising cost over one shared index. Second, compare two routing designs: classifying the question up front, "
             "or trying the cheap pipeline first and escalating when confidence is low. Third, measure cost realistically, in dollars and GPU-seconds. "
             "Fourth, test whether a tiny router is good enough, and whether routers still work on new domains.",
    "Retrieval building blocks": "These are the building blocks of our pipelines. RAG combined a retriever with a generator. DPR showed dense retrieval beats BM25 by 9 to 19 points on top-20 accuracy. "
             "BM25 is cheap and strong on rare names. Reciprocal rank fusion combines rankings without training. A cross-encoder reranker roughly doubles BM25's ranking quality, "
             "but needs one model pass per candidate. Each stage adds accuracy and adds cost.",
    "Adaptive retrieval": "Several works decide when to retrieve. Mallen and colleagues retrieve only for less popular entities. FLARE retrieves when the model is unsure of its next tokens. "
             "Self-RAG trains a model to emit retrieve tokens. IRCoT interleaves retrieval with reasoning for multi-hop questions. "
             "Adaptive-RAG is the closest: a small classifier routes between no retrieval, single-step and multi-step, on the same datasets we use. So we must go beyond it.",
    "Cost-aware routing": "Cost-aware routing is established for choosing between language models. FrugalGPT uses a cascade and reports up to 98 percent lower cost. "
             "RouteLLM learns to route between a strong and a weak model. MBA-RAG uses a bandit to pick a retrieval strategy. "
             "A 2025 study found simple uncertainty signals are often as good as complex methods. But almost all of them count cost as LLM calls or steps only.",
    "Datasets and corpus": "We use three standard datasets over Wikipedia. Natural Questions has real search queries, mostly single-hop. "
             "HotpotQA and 2WikiMultiHopQA need two or more passages. We add a small set of our university documents to test transfer to a new domain. "
             "We use about 500 test queries per dataset and separate training queries to create router labels.",
    "Gaps we address": "We address four gaps. Up-front routing and cascades are rarely compared under one cost model. Cost is measured unrealistically. "
             "Nobody checks whether the router itself costs more than it saves. And routers are almost never tested on new domains.",
    "One system": "This is our system. A query goes to the router. The router sends it to one of three pipelines, or, in cascade mode, starts with the cheapest and escalates. "
             "The generator answers, and we score the answer and log every token, every millisecond and the dollar cost. Only the routing decision changes between experiments.",
    "The three pipelines": "Pipeline zero asks the model directly. Pipeline one embeds the query, searches a FAISS index and adds five passages. "
             "Pipeline two combines BM25 and dense search, fuses them, reranks one hundred candidates with a cross-encoder and keeps the best five. "
             "Everything else is shared: the index, the prompt and the generator. We build it with LangChain and log every call.",
    "Two ways to route": "There are two ways to route. An up-front router reads only the question and picks a pipeline: fast and predictable, but it decides blind. "
             "A cascade tries the cheap pipeline first and escalates only if confidence is low. It sees real evidence, but hard questions pay for every stage. "
             "We test three confidence signals: answer probability, agreement between samples, and the retrieval score gap. Changing the thresholds gives a Pareto curve.",
    "Router labels": "We need no manual labels. We run all three pipelines on training questions and label each with the cheapest pipeline that got it right. "
             "Then we train routers of four sizes, from a one-millisecond TF-IDF model to an 8-billion-parameter language model. "
             "Importantly, the router's own cost is added to the total, so an expensive router is penalised.",
    "A realistic cost model": "Our cost model adds up everything a query costs: input and output tokens, embedding calls, GPU time for the reranker and the router, "
             "search time, and the index memory spread over all queries. We report dollars per thousand queries and GPU-seconds per query, next to accuracy.",
    "Experimental design": "We compare fixed policies, random routing, four up-front routers, three cascades and an oracle upper bound. "
             "We measure exact match, F1, tokens, latency, dollars and GPU-seconds. The main result is a Pareto curve against always using the best pipeline, "
             "plus the cost saved at no more than one point of accuracy loss, with confidence intervals, significance tests and an out-of-domain test.",
    "What is new": "What is new? First, a head-to-head comparison of up-front routing and cascades under one cost model. Second, a realistic cost model in dollars and GPU-seconds. "
             "Third, a router-size study that charges each router its own cost. Fourth, out-of-domain transfer, including our university documents. "
             "To be honest about prior work: outcome-based labels come from Adaptive-RAG; our contribution is cost, cascades and transfer.",
    "Key references": "These are our key references, numbered as cited on the slides.",
    "Thank you": "Thank you. We are happy to take your questions.",
}


def note_for(title):
    for k in sorted(NOTES, key=len, reverse=True):
        if title.startswith(k) or (k == "Title" and title.startswith("Title")):
            return NOTES[k]
    raise KeyError(title)


def build():
    d = deck()
    doc = page("RAG Router — Review 1", SLIDE_CSS_CONCISE, d.html())
    (HERE / "RAGRouter_Review1_Slides.html").write_text(doc, encoding="utf-8")
    render_pdf(doc, HERE / "RAGRouter_Review1_Slides.pdf", "rag_router_r1")
    n = len(d.slides)
    tmp = Path(tempfile.mkdtemp())
    shot = tmp / "full.png"
    (tmp / "deck.html").write_text(doc.replace("</head>", "<style>.slide{break-after:auto}</style></head>"), encoding="utf-8")
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={tmp / 'chrome'}",
                        "--force-device-scale-factor=2", "--virtual-time-budget=3000", f"--window-size=1280,{n * 720}",
                        f"--screenshot={shot}", (tmp / "deck.html").as_uri()], capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        subprocess.run(["pkill", "-f", f"user-data-dir={tmp / 'chrome'}"])
    from PIL import Image
    from pptx import Presentation
    from pptx.util import Emu
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(shot)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    for i, (num, title, who) in enumerate(d.assignments()):
        p = tmp / f"s{num:02d}.png"
        im.crop((0, i * 1440, 2560, (i + 1) * 1440)).save(p)
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.shapes.add_picture(str(p), 0, 0, prs.slide_width, prs.slide_height)
        s.notes_slide.notes_text_frame.text = f"Presenter: {who or 'last presenter'}\n\n" + H.unescape(re.sub("<[^>]+>", "", note_for(title)))
    prs.save(HERE / "RAGRouter_Review1_Slides.pptx")
    for num, title, who in d.assignments():
        print(num, title, "—", who)


if __name__ == "__main__":
    build()
