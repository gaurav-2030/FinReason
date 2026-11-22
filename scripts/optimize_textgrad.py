"""Optimize the system prompt with TextGrad.

    python scripts/optimize_textgrad.py --model ollama:qwen3:8b --optimizer-model ollama:qwen3:8b
Training questions come from FinQA train, validation questions from FinQA dev.
Saves artifacts/textgrad_<model>.json with the best prompt and the full optimization history.
"""
import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finreason.config import ARTIFACTS, SEED
from finreason.data import load_dataset
from finreason.retrieval import build_context
from finreason.textgrad_opt import optimize_system_prompt


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="ollama:qwen3:8b", help="model whose prompt is optimized")
    parser.add_argument("--optimizer-model", default="ollama:qwen3:8b", help="model that writes feedback")
    parser.add_argument("--train", type=int, default=50)
    parser.add_argument("--val", type=int, default=40)
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--batch", type=int, default=6)
    parser.add_argument("--fmt", default="markdown")
    args = parser.parse_args()

    train = load_dataset("finqa", "train", n=args.train, seed=SEED)
    val = load_dataset("finqa", "dev", n=args.val, seed=SEED)
    train_ctx = [build_context(e, args.fmt)[0] for e in train]
    val_ctx = [build_context(e, args.fmt)[0] for e in val]

    start = time.time()
    prompt, val_acc, history, usage = optimize_system_prompt(
        args.model, args.optimizer_model, train, train_ctx, val, val_ctx,
        steps=args.steps, batch_size=args.batch, seed=SEED)
    slug = re.sub(r"[^A-Za-z0-9.]+", "-", args.model)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS / f"textgrad_{slug}.json"
    json.dump({"system_prompt": prompt, "val_accuracy": val_acc, "task_model": args.model,
               "optimizer_model": args.optimizer_model, "train_size": len(train),
               "val_size": len(val), "seconds": round(time.time() - start), "usage": usage,
               "history": history}, open(path, "w"), indent=2)
    print(f"best validation accuracy {val_acc:.3f}; saved {path}", flush=True)
    print(prompt)


if __name__ == "__main__":
    main()
