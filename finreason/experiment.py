"""Evaluate one strategy on one question and turn the result into a flat record (one JSONL line)."""
import re

from .answers import score, token_f1
from .errors import classify_error
from .llm import cost_usd
from .retrieval import build_context, recall_at_k


def run_name(dataset, split, n, model, strategy, fmt, context, k, think, perturbed):
    """File name that identifies a run, e.g. finqa_test_n100__ollama-qwen3-8b__cot_fs__markdown__full."""
    strategy = re.sub(r"^(dspy|textgrad):.*/", r"\1-", strategy).replace(".json", "")
    parts = [f"{dataset}{'-perturbed' if perturbed else ''}_{split}_n{n}", model, strategy, fmt,
             context + (str(k) if context == "retrieved" else "")]
    if think:
        parts.append("think")
    return re.sub(r"[^A-Za-z0-9_.\-]+", "-", "__".join(parts))


def evaluate_example(strategy, llm, example, fmt="markdown", mode="full", retriever=None, k=5):
    context, retrieved = build_context(example, fmt=fmt, mode=mode, retriever=retriever, k=k)
    pred = strategy(llm, example, context, fmt)
    correct, exact = score(pred.answer, example.gold, example.question, example.scale)
    retrieved_ids = [uid for uid, _, _ in retrieved] if retrieved else None
    return {
        "uid": example.uid, "dataset": example.dataset, "question": example.question,
        "gold": example.gold, "scale": example.scale, "n_steps": example.n_steps,
        "evidence": example.evidence, "answer": pred.answer, "how": pred.how,
        "correct": bool(correct), "exact_match": bool(exact),
        "f1": token_f1(pred.answer, example.gold, example.question, example.scale),
        "error_category": classify_error(pred, example, correct),
        "n_calls": pred.n_calls, "prompt_tokens": pred.prompt_tokens,
        "completion_tokens": pred.completion_tokens, "latency": round(pred.latency, 3),
        "cost_usd": cost_usd(llm.spec, pred.prompt_tokens, pred.completion_tokens),
        "output": pred.output, "code": pred.code, "sandbox_error": pred.error,
        "extra": pred.extra, "retrieved": retrieved_ids,
        "recall": recall_at_k(retrieved_ids, example.gold_facts) if retrieved_ids else None,
        "meta": example.meta,
    }
