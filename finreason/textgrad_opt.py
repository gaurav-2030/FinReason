"""Automated prompt optimization with TextGrad: the system prompt is a trainable variable, an LLM
critiques wrong answers ("textual gradients"), and the optimizer rewrites the prompt."""
import random
import threading
from concurrent.futures import ThreadPoolExecutor

import textgrad as tg
from textgrad.engine import EngineLM

from .answers import allows_percent, extract_answer, score
from .llm import LLM
from .prompts import SYSTEM_PROMPT, user_message

CONSTRAINTS = [
    "The prompt must keep telling the model to end with a final line 'Answer: <number>'.",
    "The prompt must stay general: it must not mention any specific company, question or number.",
]


class LocalEngine(EngineLM):
    """Adapter so TextGrad can call our LLM class (same models, cache and token counting)."""

    def __init__(self, llm):
        self.llm = llm
        self.model_string = llm.spec
        self.prompt_tokens = self.completion_tokens = self.calls = 0
        self._lock = threading.Lock()   # usage counters are updated from several threads

    def generate(self, prompt, system_prompt=None, **kwargs):
        messages = [{"role": "system", "content": system_prompt or self.system_prompt},
                    {"role": "user", "content": prompt}]
        response = self.llm.chat(messages)
        with self._lock:
            self.calls += 1
            self.prompt_tokens += response.prompt_tokens
            self.completion_tokens += response.completion_tokens
        return response.text

    def __call__(self, prompt, **kwargs):
        return self.generate(prompt, **kwargs)


def _gold_text(example):
    if allows_percent(example.question, example.scale) and not isinstance(example.gold, str):
        return f"{example.gold} (if the question asks for a percentage, {example.gold * 100:.4g}%)"
    return str(example.gold)


def accuracy(engine, system_prompt, examples, contexts, workers=4):
    """Accuracy of zero-shot CoT with the given system prompt (questions answered in parallel;
    decoding is greedy, so the result does not depend on the order)."""
    def correct(pair):
        ex, ctx = pair
        output = engine.generate(user_message(ctx, ex.question, "cot"), system_prompt=system_prompt)
        return score(extract_answer(output)[0], ex.gold, ex.question, ex.scale)[0]
    with ThreadPoolExecutor(workers) as pool:
        return sum(pool.map(correct, zip(examples, contexts))) / len(examples)


def optimize_system_prompt(task_spec, optimizer_spec, train, train_ctx, val, val_ctx,
                           steps=6, batch_size=6, seed=42, log=print):
    """Mini-batch TextGrad loop. Only wrongly answered questions produce feedback. After each
    update the new prompt is kept only if validation accuracy does not drop (otherwise revert)."""
    # the critic reads every wrong answer with its report context (about 11,000 tokens per update),
    # so it needs a larger context window and output budget than the task model
    task_engine = LocalEngine(LLM(task_spec))
    backward_engine = LocalEngine(LLM(optimizer_spec, num_ctx=16384, max_tokens=2048))
    tg.set_backward_engine(backward_engine, override=True)
    system_prompt = tg.Variable(
        SYSTEM_PROMPT, requires_grad=True,
        role_description="system prompt that tells a language model how to answer numerical "
                         "questions about financial reports accurately")
    model = tg.BlackboxLLM(task_engine, system_prompt=system_prompt)
    optimizer = tg.TGD(parameters=[system_prompt], constraints=CONSTRAINTS)
    best_prompt = SYSTEM_PROMPT
    best_acc = accuracy(task_engine, best_prompt, val, val_ctx)
    history = [{"step": 0, "prompt": best_prompt, "val_accuracy": best_acc, "kept": True}]
    log(f"step 0: validation accuracy {best_acc:.3f}")
    rng = random.Random(seed)
    for step in range(1, steps + 1):
        batch = rng.sample(range(len(train)), batch_size)
        losses = []
        for i in batch:
            ex = train[i]
            question = tg.Variable(user_message(train_ctx[i], ex.question, "cot"),
                                   requires_grad=False, role_description="question with report context")
            response = model(question)
            answer, _ = extract_answer(response.value)
            if score(answer, ex.gold, ex.question, ex.scale)[0]:
                continue
            loss_fn = tg.TextLoss(
                f"The correct answer to this question is {_gold_text(ex)}. The response above is "
                "wrong. Identify precisely which step went wrong (finding the right numbers, "
                "units and scale, sign, formula, or arithmetic) and explain what general "
                "instruction would have prevented the mistake. Be concise.")
            losses.append(loss_fn(response))
        if not losses:
            log(f"step {step}: every answer in the batch was correct, no update")
            continue
        optimizer.zero_grad()
        tg.sum(losses).backward()
        try:
            optimizer.step()
        except IndexError:   # the optimizer model did not return a usable rewrite: skip this update
            system_prompt.set_value(best_prompt)
            history.append({"step": step, "prompt": best_prompt, "val_accuracy": best_acc, "kept": False,
                            "n_wrong_in_batch": len(losses), "note": "no usable rewrite"})
            log(f"step {step}: {len(losses)} wrong in batch, the optimizer returned no usable prompt, skipped")
            continue
        candidate = system_prompt.value
        acc = accuracy(task_engine, candidate, val, val_ctx)
        kept = acc >= best_acc
        if kept:
            best_prompt, best_acc = candidate, acc
        else:
            system_prompt.set_value(best_prompt)
        history.append({"step": step, "prompt": candidate, "val_accuracy": acc, "kept": kept,
                        "n_wrong_in_batch": len(losses)})
        log(f"step {step}: {len(losses)} wrong in batch, validation accuracy {acc:.3f}, "
            f"{'kept' if kept else 'reverted'}")
    usage = {"task_calls": task_engine.calls, "optimizer_calls": backward_engine.calls,
             "prompt_tokens": task_engine.prompt_tokens + backward_engine.prompt_tokens,
             "completion_tokens": task_engine.completion_tokens + backward_engine.completion_tokens}
    return best_prompt, best_acc, history, usage
