"""Measure how often retrieval finds the gold evidence (recall@k) - no language model needed.

    python scripts/eval_retrieval.py
Compares BM25, dense embeddings and the hybrid (RRF) on the full FinQA and TAT-QA test sets.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from finreason.config import RESULTS
from finreason.data import load_dataset
from finreason.retrieval import HybridRetriever, evidence_units, recall_at_k

K_VALUES = [1, 3, 5, 8, 10]


def main():
    retriever = HybridRetriever()
    rows = []
    for dataset in ["finqa", "tatqa"]:
        examples = [ex for ex in load_dataset(dataset, "test") if ex.gold_facts]
        for method in ["bm25", "dense", "hybrid"]:
            recalls = {k: [] for k in K_VALUES}
            for ex in examples:
                ranked = [uid for uid, _, _ in retriever.retrieve(ex.question, evidence_units(ex),
                                                                   k=max(K_VALUES), method=method)]
                for k in K_VALUES:
                    recalls[k].append(recall_at_k(ranked[:k], ex.gold_facts))
            row = {"dataset": dataset, "method": method, "n": len(examples)}
            row.update({f"recall@{k}": sum(v) / len(v) for k, v in recalls.items()})
            rows.append(row)
            print(row, flush=True)
    table = pd.DataFrame(rows)
    table.to_csv(RESULTS / "retrieval_recall.csv", index=False)
    (RESULTS / "retrieval_recall.md").write_text(table.to_markdown(index=False, floatfmt=".3f") + "\n")
    print(table.to_markdown(index=False, floatfmt=".3f"))


if __name__ == "__main__":
    main()
