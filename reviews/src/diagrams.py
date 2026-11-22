"""Hand-drawn SVG diagrams of the FinReason design (architecture, pipeline, VPSC, optimizers, ...)."""
from common import (AMBER, AQUA, CARD, LINE, MUTED, NAVY, TEAL, arrow, box, path_arrow, svg, text)

TEAL_FILL, AMBER_FILL, GREEN_FILL, BLUE_FILL = "#e3f1f2", "#fdf0e1", "#e6f5ee", "#e8f0fb"


def architecture():
    """Six-layer architecture with the modules of each layer."""
    W, label_w, gap = 1160, 150, 12
    layers = [
        ("Presentation", BLUE_FILL, [("Run store", ["results/runs/*.jsonl"]), ("Analysis & figures", ["analyze.py, figures.py"]),
                                     ("Streamlit web app", ["Overview · Ask · Compare · Results", "Optimization · Robustness · Errors"])]),
        ("Evaluation", GREEN_FILL, [("Answer parser & scorer", ["answers.py"]), ("Error taxonomy", ["errors.py"]),
                                    ("Statistics", ["bootstrap CI · McNemar · Holm"]), ("Perturbation test", ["perturb.py"])]),
        ("Optimization", AMBER_FILL, [("DSPy", ["BootstrapFewShot · MIPROv2"]), ("TextGrad", ["textual gradients · TGD"]),
                                      ("Artifacts", ["optimized prompts / programs"])]),
        ("Reasoning", TEAL_FILL, [("Prompt library", ["prompts.py"]), ("Strategy engine", ["8 strategies + VPSC"]),
                                  ("LLM client", ["Ollama / API · cache"]), ("Code sandbox", ["sandbox.py"]),
                                  ("Grounding verifier", ["verify.py"])]),
        ("Context", CARD, [("Table serializer", ["markdown · json · html · text"]), ("Hybrid retriever", ["BM25 + MiniLM/FAISS + RRF"]),
                           ("Context builder", ["full page or top-k"])]),
        ("Data", CARD, [("FinQA", ["JSON · 8,281 Qs"]), ("TAT-QA", ["JSON · arithmetic subset"]),
                        ("Indian annual reports", ["4 PDFs → 44 Qs (ours)"]), ("Loaders", ["data.py → Example"])]),
    ]
    row_h, row_gap = 78, 16
    out = []
    for r, (name, fill, mods) in enumerate(layers):
        y = 8 + r * (row_h + row_gap)
        out.append(f'<rect x="4" y="{y}" width="{W - 8}" height="{row_h}" rx="12" fill="#fbfcfe" stroke="#dde3ec"/>')
        out.append(text(label_w / 2 + 4, y + row_h / 2 + 6, name, fs=16, color=NAVY, weight="700"))
        n = len(mods)
        bw = (W - label_w - 20 - gap * (n - 1)) / n
        for i, (t, lines) in enumerate(mods):
            x = label_w + 6 + i * (bw + gap)
            out.append(box(x, y + 9, bw, row_h - 18, t, lines, fill=fill, stroke="#9fb0c8", fs=14.5, lfs=12))
        if r < len(layers) - 1:
            ya = y + row_h + row_gap
            out.append(arrow(W / 2 + 60, ya - 1, W / 2 + 60, y + row_h + 1, color=TEAL, marker="aht", sw=2))
            out.append(arrow(W / 2 - 60, y + row_h + 1, W / 2 - 60, ya - 1, color="#9fb0c8", sw=1.5, dash="4 3"))
    h = 8 + len(layers) * (row_h + row_gap)
    out.append(text(W / 2 + 70, 8 + row_h + 12, "", fs=10))
    return svg(W, h, "".join(out))


def pipeline():
    """The life of one question, eight stages in two rows."""
    steps = [("1. Load", ["FinQA / TAT-QA / Indian", "→ Example object"]),
             ("2. Context", ["serialize table;", "full page or top-k retrieval"]),
             ("3. Prompt", ["strategy template +", "worked examples"]),
             ("4. LLM call", ["Qwen3 via Ollama / API;", "cache, tokens, latency"]),
             ("5. Execute / parse", ["PoT code → sandbox;", "read 'Answer:' line"]),
             ("6. Score", ["0.5% tolerance, EM, F1", "(answers.score)"]),
             ("7. Diagnose", ["error taxonomy", "(errors.py)"]),
             ("8. Record & analyze", ["JSONL → CIs, McNemar,", "figures, web app"])]
    W, bw, bh, gx = 1160, 262, 92, 34
    out = []
    for i, (t, lines) in enumerate(steps):
        row, col = divmod(i, 4)
        col = col if row == 0 else 3 - col
        x, y = 8 + col * (bw + gx), 10 + row * (bh + 56)
        fill = [BLUE_FILL, TEAL_FILL, TEAL_FILL, TEAL_FILL, AMBER_FILL, GREEN_FILL, GREEN_FILL, BLUE_FILL][i]
        out.append(box(x, y, bw, bh, t, lines, fill=fill, stroke="#9fb0c8", fs=16, lfs=13))
    for i in range(3):
        x = 8 + (i + 1) * (bw + gx)
        out.append(arrow(x - gx + 2, 56, x - 3, 56))
        out.append(arrow(x - 2, 10 + bh + 56 + 46, x - gx + 3, 10 + bh + 56 + 46))
    xr = 8 + 3 * (bw + gx) + bw / 2
    out.append(arrow(xr, 10 + bh + 2, xr, 10 + bh + 54))
    return svg(W, 10 + 2 * bh + 64, "".join(out))


def vpsc():
    """Verified Program Self-Consistency."""
    out = []
    out.append(box(6, 110, 150, 96, "Question", ["+ report page", "(table + text)"], fill=BLUE_FILL, stroke="#9fb0c8"))
    out.append(arrow(158, 158, 196, 158))
    out.append(box(198, 110, 150, 96, "PoT prompt", ["3 worked examples", "as Python code"], fill=TEAL_FILL, stroke="#9fb0c8"))
    out.append(arrow(350, 158, 388, 158))
    labels = ["program 0 · T = 0 (greedy)", "program 1 · T = 0.7", "program 2 · T = 0.7", "program 3 · T = 0.7", "program 4 · T = 0.7"]
    for i, l in enumerate(labels):
        y = 18 + i * 56
        out.append(box(390, y, 206, 44, "", [l], fill="#fff", stroke="#9fb0c8", lfs=12.5))
        out.append(arrow(598, y + 22, 636, y + 22, sw=1.4))
        out.append(box(638, y, 108, 44, "", ["sandbox run"], fill=AMBER_FILL, stroke="#d9b98f", lfs=12.5))
        out.append(arrow(748, y + 22, 784, y + 22, sw=1.4))
        ok = i not in (2,)
        out.append(box(786, y, 120, 44, "", ["grounded ✓" if ok else "ungrounded ✗"], fill=GREEN_FILL if ok else "#fde8e8",
                       stroke="#9cc9b0" if ok else "#e7a3a3", lfs=12.5))
        out.append(arrow(908, y + 22, 944, 158, sw=1.2, color="#9fb0c8"))
    out.append(box(946, 92, 208, 132, "Majority vote", ["over executed + grounded", "programs (if none pass:", "all executed programs)", "→ answer, confidence = votes/5"],
                   fill=TEAL_FILL, stroke=TEAL, fs=15.5, lfs=12))
    out.append(text(851, 300, "every number in the code must appear in the report", fs=11.5, color=MUTED))
    out.append(text(851, 314, "(allowing 0–12, 100, 1000, 10⁵, 10⁶, 10⁷, 10⁹, years, ×100/×1000 rescaling)", fs=11, color=MUTED))
    return svg(1160, 322, "".join(out))


def optimizers():
    """DSPy (left) and TextGrad (right) optimization loops."""
    o = []
    o.append(text(280, 20, "DSPy: compile a Chain-of-Thought program", fs=16, color=NAVY, weight="700"))
    o.append(box(10, 40, 160, 70, "Train set", ["50 FinQA train Qs"], fill=BLUE_FILL, stroke="#9fb0c8"))
    o.append(box(200, 40, 160, 70, "Program", ["ChainOfThought(", "FinancialQA signature)"], fill=TEAL_FILL, stroke="#9fb0c8", lfs=11.5))
    o.append(box(390, 40, 160, 70, "Metric", ["our scorer", "(0.5% tolerance)"], fill=GREEN_FILL, stroke="#9fb0c8"))
    o.append(arrow(172, 75, 198, 75)); o.append(arrow(362, 75, 388, 75))
    o.append(box(10, 140, 255, 112, "BootstrapFewShot", ["run program on train Qs;", "keep up to 3 traces the metric", "marks correct → demos"], fill=AMBER_FILL, stroke="#d9b98f", lfs=12))
    o.append(box(285, 140, 265, 112, "MIPROv2 (light)", ["propose instructions + demo sets;", "Bayesian search, each trial", "scored on 40 FinQA dev Qs"], fill=AMBER_FILL, stroke="#d9b98f", lfs=12))
    o.append(arrow(280, 112, 140, 138)); o.append(arrow(280, 112, 415, 138))
    o.append(box(150, 280, 260, 56, "Compiled program (JSON)", ["instruction + demos → test sets"], fill=BLUE_FILL, stroke="#9fb0c8", fs=14, lfs=12))
    o.append(arrow(140, 254, 230, 278)); o.append(arrow(415, 254, 330, 278))
    o.append(f'<line x1="582" y1="10" x2="582" y2="340" stroke="{LINE}" stroke-width="2"/>')
    X = 600
    o.append(text(X + 280, 20, "TextGrad: optimize the system prompt", fs=16, color=NAVY, weight="700"))
    o.append(box(X + 10, 40, 175, 70, "System prompt", ["trainable variable"], fill=TEAL_FILL, stroke=TEAL))
    o.append(box(X + 215, 40, 150, 70, "Task model", ["Qwen3 answers a", "batch of 6 train Qs"], fill=BLUE_FILL, stroke="#9fb0c8", lfs=12))
    o.append(box(X + 395, 40, 155, 70, "Loss (wrong only)", ["'correct answer is …;", "which step failed?'"], fill="#fde8e8", stroke="#e7a3a3", lfs=12))
    o.append(arrow(X + 187, 75, X + 213, 75)); o.append(arrow(X + 367, 75, X + 393, 75))
    o.append(box(X + 395, 150, 155, 76, "Textual gradient", ["critique written by", "optimizer model (8B)"], fill=AMBER_FILL, stroke="#d9b98f", lfs=12))
    o.append(arrow(X + 472, 112, X + 472, 148))
    o.append(box(X + 190, 150, 175, 76, "TGD step", ["LLM rewrites the prompt", "(constraints: keep 'Answer:',", "stay general)"], fill=AMBER_FILL, stroke="#d9b98f", lfs=11.5))
    o.append(arrow(X + 393, 188, X + 367, 188))
    o.append(box(X + 10, 150, 150, 76, "Validate", ["40 FinQA dev Qs:", "keep if acc. ≥ best,", "else revert"], fill=GREEN_FILL, stroke="#9cc9b0", lfs=12))
    o.append(arrow(X + 188, 188, X + 162, 188))
    o.append(path_arrow(f"M{X + 85},150 L{X + 85},112", color=TEAL, marker="aht"))
    o.append(text(X + 280, 262, "6 steps × batch of 6; best prompt saved to artifacts/textgrad_<model>.json", fs=12, color=MUTED))
    o.append(text(X + 280, 282, "Evaluated exactly like zero-shot CoT: only the system prompt differs.", fs=12, color=MUTED))
    return svg(1160, 345, "".join(o))


def sandbox():
    steps = [("Model output", ["first ```python block"]), ("Static AST check", ["only `import math`;", "no dunders, open, eval, os…"]),
             ("Isolated process", ["python -I (no site, no env)", "code passed on stdin"]),
             ("Restricted builtins", ["whitelist: abs, round, sum…", "print disabled"]),
             ("Resource limits", ["CPU rlimit + 5 s timeout"]), ("Result", ["JSON: ans + numeric", "variable trace"])]
    o, bw, gx = [], 172, 25
    for i, (t, l) in enumerate(steps):
        x = 6 + i * (bw + gx)
        o.append(box(x, 10, bw, 92, t, l, fill=[BLUE_FILL, AMBER_FILL, AMBER_FILL, AMBER_FILL, AMBER_FILL, GREEN_FILL][i], stroke="#9fb0c8", fs=14.5, lfs=11.5))
        if i:
            o.append(arrow(x - gx + 1, 56, x - 2, 56))
    o.append(text(580, 128, "On failure the error message is shown to the model once and the repaired code is run again (PoT).", fs=12.5))
    return svg(1180, 136, "".join(o))


def indian_pipeline():
    o = []
    row1 = [("Annual-report PDFs", ["Titan · Asian Paints", "Marico · Pidilite"]), ("Locate statements", ["P&L, balance sheet,", "10-year highlights"]),
            ("Transcribe rows", ["build_indian_set.py", "numbers as printed"]), ("Check 1", ["all 366 cells found", "on the PDF page"])]
    row2 = [("Write question", ["+ formula in Python", "(no typed answers)"]), ("Gold = run formula", ["in the sandbox"]),
            ("Check 2", ["every formula number is", "in the table / text"]), ("indian_set.jsonl", ["44 Qs + checklist with", "PDF page per question"])]
    bw, gx = 262, 34
    for i, (t, l) in enumerate(row1):
        x = 8 + i * (bw + gx)
        o.append(box(x, 8, bw, 78, t, l, fill=[BLUE_FILL, CARD, CARD, GREEN_FILL][i], stroke="#9fb0c8", lfs=12.5))
        if i:
            o.append(arrow(x - gx + 2, 47, x - 3, 47))
    for i, (t, l) in enumerate(row2):
        x = 8 + (3 - i) * (bw + gx)
        o.append(box(x, 132, bw, 78, t, l, fill=[CARD, AMBER_FILL, GREEN_FILL, BLUE_FILL][i], stroke="#9fb0c8", lfs=12.5))
        if i:
            o.append(arrow(x + bw + gx - 2, 171, x + bw + 3, 171))
    xr = 8 + 3 * (bw + gx) + bw / 2
    o.append(arrow(xr, 88, xr, 130))
    return svg(1160, 216, "".join(o))


def timeline():
    """Project plan across the three reviews (phases, not calendar dates)."""
    phases = [("Problem definition & literature survey", 0, 3, NAVY), ("Dataset acquisition (FinQA, TAT-QA)", 1, 3, TEAL),
              ("Indian annual-report set: collection & checks", 2, 5, TEAL), ("High-level design & core library", 3, 6, TEAL),
              ("Manual prompting strategies + VPSC", 5, 8, AMBER), ("DSPy & TextGrad optimization", 6, 9, AMBER),
              ("Ablations, robustness, 8B model", 7, 10, AMBER), ("Analysis, web app, IEEE report", 9, 12, "#2a78d6")]
    W, left, top, rh = 1160, 400, 40, 34
    cw = (W - left - 10) / 12
    o = []
    for i in range(12):
        o.append(text(left + i * cw + cw / 2, 26, f"W{i + 1}", fs=12, color=MUTED))
        o.append(f'<line x1="{left + i * cw}" y1="32" x2="{left + i * cw}" y2="{top + len(phases) * rh}" stroke="#eef1f6"/>')
    for i, (name, a, b, c) in enumerate(phases):
        y = top + i * rh
        o.append(text(left - 12, y + 21, name, fs=13.5, color="#2a3a55", anchor="end"))
        o.append(f'<rect x="{left + a * cw + 2}" y="{y + 6}" width="{(b - a) * cw - 4}" height="{rh - 12}" rx="6" fill="{c}" opacity=".9"/>')
    for wk, lab in [(3, "Review 1"), (6, "Review 2"), (12, "Review 3")]:
        x = left + wk * cw
        o.append(f'<line x1="{x}" y1="32" x2="{x}" y2="{top + len(phases) * rh + 6}" stroke="{AMBER}" stroke-width="2" stroke-dasharray="5 4"/>')
        o.append(text(x - 4, top + len(phases) * rh + 22, lab, fs=12.5, color=AMBER, weight="700", anchor="end"))
    return svg(W, top + len(phases) * rh + 30, "".join(o))


def deployment():
    o = []
    o.append(f'<rect x="6" y="6" width="820" height="300" rx="14" fill="#fbfcfe" stroke="{NAVY}" stroke-width="1.6"/>')
    o.append(text(20, 30, "Laptop: Apple M4, 24 GB unified memory, macOS · Python 3.13 venv", fs=14, color=NAVY, weight="700", anchor="start"))
    o.append(box(24, 48, 250, 112, "Ollama server :11434", ["experiments · 4 parallel slots", "qwen3:1.7b · qwen3:8b", "(4-bit quantized)"], fill=TEAL_FILL, stroke="#9fb0c8", lfs=12))
    o.append(box(24, 178, 250, 112, "Ollama server :11435", ["web app only · 2 slots", "(questions never wait", "behind experiments)"], fill=TEAL_FILL, stroke="#9fb0c8", lfs=12))
    o.append(box(300, 48, 250, 112, "Experiment runner", ["run_all.sh → run_experiment.py", "3 worker threads, resumable", "optimize_dspy / _textgrad"], fill=AMBER_FILL, stroke="#d9b98f", lfs=12))
    o.append(box(300, 178, 250, 112, "Streamlit app :8501", ["9 pages; Ask runs the full", "pipeline live; reads", "results/ for dashboards"], fill=BLUE_FILL, stroke="#9fb0c8", lfs=12))
    o.append(box(576, 48, 232, 112, "Storage", ["~/.cache/finreason (SQLite", "response cache) · results/", "artifacts/ · data/"], fill=CARD, stroke="#9fb0c8", lfs=12))
    o.append(box(576, 178, 232, 112, "Sandbox processes", ["one short-lived python -I", "per program, 5 s limit"], fill=AMBER_FILL, stroke="#d9b98f", lfs=12))
    o.append(arrow(298, 104, 276, 104)); o.append(arrow(298, 234, 276, 234))
    o.append(arrow(552, 104, 574, 104)); o.append(arrow(552, 234, 574, 234));
    o.append(box(860, 48, 290, 112, "Optional API models", ["OpenAI · Groq · Gemini ·", "OpenRouter · Anthropic", "(--model provider:model)"], fill="#fff", stroke="#9fb0c8", lfs=12))
    o.append(box(860, 178, 290, 112, "Browser", ["opens the app at", "http://localhost:8501"], fill="#fff", stroke="#9fb0c8", lfs=12))
    o.append(arrow(828, 104, 858, 104, dash="5 4", label="HTTPS", ly=92)); o.append(arrow(858, 234, 830, 234, dash="5 4", label="HTTP", ly=226))
    return svg(1160, 312, "".join(o))


def sequence():
    """Sequence of one 'Ask' request in the web app (VPSC strategy)."""
    actors = ["User", "Streamlit app", "Context builder", "Strategy (VPSC)", "LLM client / Ollama", "Sandbox + verifier", "Scorer / taxonomy"]
    W, top = 1160, 30
    xs = [70 + i * (W - 140) / (len(actors) - 1) for i in range(len(actors))]
    o = []
    for x, a in zip(xs, actors):
        o.append(box(x - 74, 4, 148, 34, "", [a], fill=TEAL_FILL, stroke="#9fb0c8", lfs=13))
        o.append(f'<line x1="{x}" y1="40" x2="{x}" y2="420" stroke="#b9c4d6" stroke-dasharray="4 4"/>')
    msgs = [(0, 1, "question + table (dataset / pasted / PDF page)"), (1, 2, "build_context(fmt, mode)"), (2, 1, "serialized context (+ retrieved rows)"),
            (1, 3, "run strategy(llm, example, context)"), (3, 4, "5 × chat(PoT prompt, T, sample_id)"), (4, 3, "5 programs (cached if seen)"),
            (3, 5, "run_code + grounding_check × 5"), (5, 3, "ans, trace, grounded?"), (3, 1, "Prediction: answer, votes, code, tokens"),
            (1, 6, "score() + classify_error()"), (6, 1, "correct? / error category"), (1, 0, "answer card, evidence rows, code, votes, prompt")]
    for i, (a, b, m) in enumerate(msgs):
        y = 66 + i * 29
        back = b < a
        o.append(arrow(xs[a] + (-3 if back else 3), y, xs[b] + (5 if back else -5), y, color=TEAL if back else NAVY, dash="5 3" if back else "",
                       marker="aht" if back else "ah", sw=1.5))
        o.append(text((xs[a] + xs[b]) / 2, y - 5, m, fs=11.5, color="#2a3a55"))
    return svg(W, 428, "".join(o))
