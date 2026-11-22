"""Run one or more prompting strategies on a dataset sample and save one JSON line per question.

Example:
    python scripts/run_experiment.py --dataset finqa --n 100 --model ollama:qwen3:8b \
        --strategy direct,cot_zs,cot_fs,decomp_fs,pot_fs,sc_cot
Runs are resumable: questions already present in the output file are skipped.
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finreason.config import DEFAULT_MODEL, RUNS_DIR, SEED
from finreason.data import load_dataset
from finreason.experiment import evaluate_example, run_name
from finreason.llm import LLM
from finreason.perturb import perturb_dataset
from finreason.retrieval import HybridRetriever
from finreason.strategies import get_strategy


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", default="finqa", choices=["finqa", "tatqa", "indian"])
    parser.add_argument("--split", default="test")
    parser.add_argument("--n", type=int, default=100, help="sample size (0 = whole split)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--strategy", default="cot_fs", help="comma-separated strategy names")
    parser.add_argument("--fmt", default="markdown", choices=["markdown", "json", "html", "text"])
    parser.add_argument("--context", default="full", choices=["full", "retrieved"])
    parser.add_argument("--k", type=int, default=5, help="evidence units kept in retrieved mode")
    parser.add_argument("--think", action="store_true", help="enable the model's thinking mode")
    parser.add_argument("--perturbed", action="store_true", help="numerically perturbed FinQA")
    parser.add_argument("--workers", type=int, default=4,
                        help="questions in parallel (match OLLAMA_NUM_PARALLEL; the web app uses its own server)")
    args = parser.parse_args()

    examples = load_dataset(args.dataset, args.split, n=args.n or None, seed=SEED)
    if args.perturbed:
        examples = perturb_dataset(examples, seed=SEED)
    # thinking models write long hidden reasoning, so they need a larger output budget and context
    llm = LLM(args.model, think=args.think, max_tokens=8192 if args.think else 1024,
              num_ctx=16384 if args.think else 8192)
    retriever = HybridRetriever() if args.context == "retrieved" else None
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    for strategy_name in args.strategy.split(","):
        strategy = get_strategy(strategy_name)
        name = run_name(args.dataset, args.split, args.n, args.model, strategy_name, args.fmt,
                        args.context, args.k, args.think, args.perturbed)
        path = RUNS_DIR / f"{name}.jsonl"
        done = {json.loads(line)["uid"] for line in open(path)} if path.exists() else set()
        todo = [ex for ex in examples if ex.uid not in done]
        print(f"{name}: {len(done)} done, {len(todo)} to go", flush=True)
        start = time.time()
        with open(path, "a") as out, ThreadPoolExecutor(args.workers) as pool:
            futures = [pool.submit(evaluate_example, strategy, llm, ex, args.fmt, args.context,
                                   retriever, args.k) for ex in todo]
            for i, future in enumerate(as_completed(futures), 1):
                record = future.result()
                record.update(strategy=strategy_name, model=args.model, fmt=args.fmt,
                              context=args.context, k=args.k, think=args.think,
                              perturbed=args.perturbed, split=args.split, run=name)
                out.write(json.dumps(record, default=str) + "\n")
                out.flush()
                if i % 10 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)}  {time.time() - start:.0f}s", flush=True)
        records = [json.loads(line) for line in open(path)]
        accuracy = sum(r["correct"] for r in records) / len(records)
        print(f"  accuracy {accuracy:.3f} on {len(records)} questions", flush=True)


if __name__ == "__main__":
    main()
