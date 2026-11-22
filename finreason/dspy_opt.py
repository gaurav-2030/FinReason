"""Automated prompt optimization with DSPy: a Chain-of-Thought program whose instructions and
few-shot demonstrations are chosen automatically by BootstrapFewShot or MIPROv2."""
import json
import os
import time

import dspy

from .answers import score, to_answer
from .config import OLLAMA_URL, SEED
from .llm import OPENAI_COMPATIBLE
from .strategies import Prediction

# DSPy keeps its own response cache. A cached response carries no token usage and takes no time,
# so with the cache on, the one-time optimization cost and the per-question tokens would read 0.
dspy.configure_cache(enable_disk_cache=False, enable_memory_cache=False)


class FinancialQA(dspy.Signature):
    """Answer a numerical question about a financial report using only the given table and text.
    Keep the report's units unless the question asks for another unit, write percentages as percent numbers (12.5 means 12.5%), use a minus
    sign for decreases, and answer yes or no for yes/no questions."""

    context: str = dspy.InputField(desc="table and text from a financial report")
    question: str = dspy.InputField()
    answer: str = dspy.OutputField(desc="the final answer as a single number (or yes/no), without units")


def make_lm(spec, temperature=0.0, max_tokens=1024, timeout=180):
    """Create a DSPy language model from the same 'provider:model' spec used by finreason.llm.
    A request that takes longer than `timeout` seconds fails (and is retried twice) instead of
    stalling the whole optimization."""
    provider, model = spec.split(":", 1)
    if provider == "ollama":
        return dspy.LM(f"ollama_chat/{model}", api_base=OLLAMA_URL, temperature=temperature,
                       max_tokens=max_tokens, num_ctx=16384, think=False, timeout=timeout, num_retries=2)
    if provider == "anthropic":
        return dspy.LM(f"anthropic/{model}", temperature=temperature, max_tokens=max_tokens)
    base_url, key_var = OPENAI_COMPATIBLE[provider]
    return dspy.LM(f"openai/{model}", api_base=base_url, api_key=os.environ[key_var],
                   temperature=temperature, max_tokens=max_tokens)


def to_dspy_examples(examples, contexts):
    """Wrap our Examples as dspy.Example objects; only context and question are model inputs."""
    return [dspy.Example(context=ctx, question=ex.question, gold=ex.gold, scale=ex.scale)
            .with_inputs("context", "question") for ex, ctx in zip(examples, contexts)]


def metric(example, prediction, trace=None):
    """1 if the program's answer is correct under our scoring rule, else 0."""
    answer = to_answer(getattr(prediction, "answer", None))
    return score(answer, example.gold, example.question, example.scale)[0]


def compile_program(optimizer, trainset, valset, lm):
    """Run a DSPy optimizer and return the compiled program.
    max_labeled_demos=0: demonstrations are only examples the model itself solved correctly
    (bootstrapped), so every demo contains a full reasoning chain in the model's own words."""
    dspy.configure(lm=lm)
    program = dspy.ChainOfThought(FinancialQA)
    if optimizer == "bootstrap":
        teleprompter = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=3,
                                             max_labeled_demos=0)
        return teleprompter.compile(program, trainset=trainset)
    if optimizer == "mipro":
        teleprompter = dspy.MIPROv2(metric=metric, auto="light", num_threads=4, seed=SEED,
                                    max_bootstrapped_demos=3, max_labeled_demos=0)
        return teleprompter.compile(program, trainset=trainset, valset=valset,
                                    minibatch_size=min(40, len(valset)))
    raise ValueError(f"unknown optimizer {optimizer}")


def describe(program):
    """Readable summary of what the optimizer chose: the instruction and the demo questions."""
    predictor = program.predictors()[0]
    return {"instruction": predictor.signature.instructions,
            "demos": [{"question": d.get("question"), "reasoning": d.get("reasoning"),
                       "answer": d.get("answer")} for d in predictor.demos]}


class DSPyStrategy:
    """Runs a saved, compiled DSPy program as a strategy with the same interface as the others."""

    def __init__(self, path):
        meta = json.load(open(str(path).replace(".json", ".meta.json")))
        self.lm = make_lm(meta["lm_spec"])
        self.program = dspy.ChainOfThought(FinancialQA)
        self.program.load(path)

    def __call__(self, llm, example, context, fmt):
        # a copy of the LM has its own empty history, so questions can run in parallel threads
        # and each one counts only its own calls and tokens
        lm, began = self.lm.copy(), time.perf_counter()
        with dspy.context(lm=lm):
            try:
                result = self.program(context=context, question=example.question)
                output = f"{result.reasoning}\nAnswer: {result.answer}"
                answer = to_answer(result.answer)
            except Exception as exc:   # e.g. the model broke DSPy's output format
                output, answer = f"DSPy error: {exc}", None
        pred = Prediction(answer=answer, how="dspy" if answer is not None else None, output=output,
                          latency=time.perf_counter() - began)
        for entry in lm.history:
            usage = entry.get("usage") or {}
            pred.n_calls += 1
            pred.prompt_tokens += usage.get("prompt_tokens", 0) or 0
            pred.completion_tokens += usage.get("completion_tokens", 0) or 0
        return pred
