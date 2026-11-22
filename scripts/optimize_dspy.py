"""Compile the DSPy Chain-of-Thought program with BootstrapFewShot or MIPROv2.

    python scripts/optimize_dspy.py --model ollama:qwen3:8b --optimizer bootstrap
    python scripts/optimize_dspy.py --model ollama:qwen3:8b --optimizer mipro
Training questions come from FinQA train and validation questions from FinQA dev, so the
test sets are never seen during optimization. Saves artifacts/dspy_<optimizer>_<model>.json.
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
from finreason.dspy_opt import compile_program, describe, make_lm, metric, to_dspy_examples
from finreason.retrieval import build_context


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", default="ollama:qwen3:8b")
    parser.add_argument("--optimizer", default="bootstrap", choices=["bootstrap", "mipro"])
    parser.add_argument("--train", type=int, default=50)
    parser.add_argument("--val", type=int, default=40)
    parser.add_argument("--fmt", default="markdown")
    args = parser.parse_args()

    train = load_dataset("finqa", "train", n=args.train, seed=SEED)
    val = load_dataset("finqa", "dev", n=args.val, seed=SEED)
    to_dspy = lambda exs: to_dspy_examples(exs, [build_context(e, args.fmt)[0] for e in exs])
    trainset, valset = to_dspy(train), to_dspy(val)

    lm = make_lm(args.model)
    start = time.time()
    program = compile_program(args.optimizer, trainset, valset, lm)
    compile_seconds = time.time() - start
    compile_calls = len(lm.history)
    usage = [h.get("usage") or {} for h in lm.history]

    val_correct = 0
    for ex in valset:
        try:
            val_correct += metric(ex, program(**ex.inputs()))
        except Exception:   # a malformed model output counts as wrong
            pass
    slug = re.sub(r"[^A-Za-z0-9.]+", "-", args.model)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    path = ARTIFACTS / f"dspy_{args.optimizer}_{slug}.json"
    program.save(str(path))
    meta = {"lm_spec": args.model, "optimizer": args.optimizer, "train_size": len(train),
            "val_size": len(val), "val_accuracy": val_correct / len(valset),
            "compile_seconds": round(compile_seconds), "compile_lm_calls": compile_calls,
            "compile_prompt_tokens": sum(u.get("prompt_tokens", 0) or 0 for u in usage),
            "compile_completion_tokens": sum(u.get("completion_tokens", 0) or 0 for u in usage),
            "program": describe(program)}
    json.dump(meta, open(str(path).replace(".json", ".meta.json"), "w"), indent=2)
    print(json.dumps({k: v for k, v in meta.items() if k != "program"}, indent=2))
    print(f"saved {path}")


if __name__ == "__main__":
    main()
