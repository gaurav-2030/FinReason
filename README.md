# FinReason: numerical reasoning over financial reports

Mini project for UE24AM343AB5, Prompt Engineering and Optimization for Generative AI (PES University).
Team: Gaurav Girish (PES1UG24AM103), Sunay R Hegde (PES1UG24AM903), Dhruvagouda (PES1UG24AM089),
Hanshal Nagesh (PES1UG24AM110).

We measure how prompting strategies and automated prompt optimization change the accuracy, cost and
reliability of small, local LLMs on financial questions like "what was the percentage change in revenue?".
We change only the prompt, never the model.

* **Seven hand-written strategies:** direct answer, zero-shot Chain-of-Thought (CoT), few-shot CoT,
  decomposition (Knowledge → Extract → Decompose → Answer), Program-of-Thought (the model writes Python,
  a sandbox runs it, one repair retry), Self-Consistency (5 CoT samples: 1 greedy + 4 at T = 0.7,
  majority vote) and our method, VPSC.
* **Our method, VPSC (Verified Program Self-Consistency):** sample 5 Python programs (1 greedy + 4 at
  T = 0.7), run each in the sandbox, reject programs that use numbers not found in the report (grounding
  check) and majority-vote the rest. The ablation without the check is `pot_sc` (the same 5 programs).
* **Three automatic optimizers:** DSPy BootstrapFewShot and MIPROv2, and TextGrad — 10 prompt
  configurations in total. Optimizers see only FinQA train (50) and dev (40) questions; their one-time
  cost (minutes, calls, tokens) is measured with caching off.
* **Models:** Qwen3-1.7B and Qwen3-8B running locally in Ollama. API models (OpenAI, Groq, Gemini,
  OpenRouter, Anthropic) are supported through `--model provider:model`.
* **Data:** FinQA (100), TAT-QA (100 arithmetic questions) and 44 questions we wrote over four Indian
  annual reports (Titan, Asian Paints, Marico, Pidilite), with crore/lakh units.
* **Analysis:** execution accuracy with bootstrap 95% CIs, exact match / F1, tokens per question and per
  correct answer, latency, format- and code-failure rates, McNemar tests (Holm-corrected), accuracy by
  reasoning steps and evidence source, an 8-category error taxonomy, a numerical perturbation
  (memorization) test, table-format / retrieval / thinking-mode ablations and VPSC grounding diagnostics.

## The web app

`bash scripts/start_app.sh`, then open http://localhost:8501. Nine pages:

| Page | What it shows |
|---|---|
| **Overview** | The problem, headline findings computed live from `results/`, the literature gaps and how FinReason fills each, and a checklist of every claim in our reviews with its status |
| **Ask** | One question through the full pipeline: stepper, answer card with agreement and grounding flag, highlighted evidence rows, generated code and variable trace, votes with grounding status, and the exact prompt. Input: a benchmark question, a pasted table, or a page of an uploaded PDF |
| **Compare** | Several strategies on the same question and context, in parallel, with cost |
| **Results** | Accuracy with 95% CIs, accuracy vs tokens (Pareto frontier), 1.7B vs 8B, accuracy by steps and evidence, McNemar tests, every metric, report figures |
| **Optimization** | DSPy BootstrapFewShot / MIPROv2 and TextGrad: one-time cost, test accuracy vs hand-written prompts, the chosen instructions and demos, TextGrad's step history |
| **Robustness** | Perturbation test, ablations (table format, retrieval, thinking), retrieval recall, VPSC diagnostics |
| **Errors** | Every wrong answer by error category, with the model's code and output |
| **Data** | The test sets, and a browser for the Indian set that shows each question next to its PDF page |
| **Method** | Pipeline, strategies with their real prompt text, VPSC, sandbox, scoring, references, team |

**Study guide:** `PES1UG24AM103_FinReason_Study_Guide.docx` explains every file (library, scripts, app and
tests) block by block, plus the concepts, results and viva questions.

## Setup

```bash
python3.13 -m venv .venv.nosync && ln -s .venv.nosync .venv     # see the note below
.venv/bin/pip install -r requirements.txt
ollama pull qwen3:8b && ollama pull qwen3:1.7b
OLLAMA_NUM_PARALLEL=4 ollama serve            # in a separate terminal
```

Note: this folder lives on an iCloud-synced Desktop. iCloud evicts rarely-used files, which makes a
virtual environment hang on import, so the environment lives in `.venv.nosync` (iCloud never syncs or
evicts `*.nosync`) and `.venv` is a link to it.

Download the datasets into `data/raw/`:

```bash
mkdir -p data/raw/finqa data/raw/tatqa
for s in train dev test; do curl -L -o data/raw/finqa/$s.json https://raw.githubusercontent.com/czyssrs/FinQA/main/dataset/$s.json; done
for s in train dev test_gold; do curl -L -o data/raw/tatqa/tatqa_dataset_$s.json https://raw.githubusercontent.com/NExTplusplus/TAT-QA/master/dataset_raw/tatqa_dataset_$s.json; done
```

The Indian set is already in `data/indian/indian_set.jsonl`. To rebuild it, put the four report
PDFs in `data/indian/reports/` and run `python scripts/build_indian_set.py`. Every question was
re-checked against the PDF page listed in `data/indian/verification_checklist.csv`
(`results/indian_verification.csv`).

## Running

```bash
.venv/bin/python -m pytest                                   # 57 tests: library, pipeline and every app page
.venv/bin/python scripts/run_experiment.py --dataset finqa --n 100 --model ollama:qwen3:8b --strategy cot_fs,pot_fs
.venv/bin/python scripts/optimize_dspy.py --model ollama:qwen3:1.7b --optimizer bootstrap   # or mipro
.venv/bin/python scripts/optimize_textgrad.py --model ollama:qwen3:1.7b --optimizer-model ollama:qwen3:8b
bash scripts/run_all.sh all                                  # every experiment (~30 h on an M4)
.venv/bin/python scripts/analyze.py                          # tables -> results/*.csv, report.md, figures/
bash scripts/start_app.sh                                    # web app at http://localhost:8501
```

All runs resume where they stopped, and every model response is cached in
`~/.cache/finreason/llm_cache.sqlite`, so re-running a finished experiment is instant.

## Layout

```
finreason/      library: data loading, tables, retrieval, LLM client, prompts, strategies (incl.
                VPSC), grounding verification, answer parsing/scoring, sandbox, FinQA program
                executor, perturbation, error taxonomy, statistics, figures, DSPy and TextGrad
                optimization, PDF parsing
scripts/        command-line entry points (experiments, optimization, analysis, Indian set)
app/            web app: streamlit_app.py (navigation), core.py (data), theme.py (design), views/ (pages)
tests/          pytest tests
data/           raw datasets (downloaded) and the Indian annual-report set
artifacts/      optimized prompts and compiled DSPy programs
results/        one JSONL file per run, summary tables, figures
reviews/        review slides, speaker scripts, notes and the IEEE paper (built by reviews/src/build.py)
```

## Scoring rule

A numeric answer is correct when it is within 0.5% of the gold value, or when it equals the gold
value rounded to the number of decimals the gold was written with. For percentage questions,
12.5 and 0.125 are both accepted, because FinQA stores percentages as fractions. The analysis
also reports accuracy at 1% tolerance and strict 2-decimal exact match.
