"""Describe the datasets and the evaluation samples (sizes, reasoning steps, evidence source).

    python scripts/dataset_stats.py
"""
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finreason.config import RESULTS, SEED
from finreason.data import load_dataset
from finreason.perturb import perturb_dataset


def describe(name, examples):
    steps = Counter(min(ex.n_steps, 3) for ex in examples)
    evidence = Counter(ex.evidence for ex in examples)
    return {"set": name, "questions": len(examples),
            "1 step": steps[1], "2 steps": steps[2], "3+ steps": steps[3],
            "table": evidence["table"], "text": evidence["text"], "table-text": evidence["table-text"],
            "mean table rows": round(sum(len(ex.table) for ex in examples) / len(examples), 1)}


def main():
    rows = []
    for dataset, split in [("finqa", "train"), ("finqa", "dev"), ("finqa", "test"),
                           ("tatqa", "test"), ("indian", "test")]:
        rows.append(describe(f"{dataset} {split} (full)", load_dataset(dataset, split)))
    for dataset in ["finqa", "tatqa"]:
        rows.append(describe(f"{dataset} test sample n=100", load_dataset(dataset, "test", n=100, seed=SEED)))
    perturbed = perturb_dataset(load_dataset("finqa", "test", n=100, seed=SEED), seed=SEED)
    rows.append(describe("finqa perturbed (from the n=100 sample)", perturbed))
    table = pd.DataFrame(rows)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "dataset_stats.md").write_text(table.to_markdown(index=False) + "\n")
    print(table.to_markdown(index=False))


if __name__ == "__main__":
    main()
