"""Prompting strategies. Each strategy takes (llm, example, context, fmt) and returns a Prediction."""
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from .answers import extract_answer, to_answer
from .config import ROOT, SC_SAMPLES, SC_TEMPERATURE
from .prompts import REPAIR_PROMPT, SYSTEM_PROMPT, build_messages
from .sandbox import extract_code, run_code
from .verify import grounding_check


@dataclass
class Prediction:
    answer: object = None     # float, "yes"/"no", or None if nothing could be parsed
    how: str = None           # answer_line / boxed / last_number / code / vote / dspy, or None
    output: str = ""          # the model's final raw output
    code: str = ""            # generated Python code (Program-of-Thought only)
    trace: dict = field(default_factory=dict)   # variables computed by the code
    error: str = ""           # sandbox error message, if the code failed
    n_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency: float = 0.0
    extra: dict = field(default_factory=dict)

    def add_usage(self, response):
        self.n_calls += 1
        self.prompt_tokens += response.prompt_tokens
        self.completion_tokens += response.completion_tokens
        self.latency += response.latency


def text_strategy(style, fewshot, system=SYSTEM_PROMPT):
    """Direct / Chain-of-Thought / decomposition: one call, then read the 'Answer:' line."""
    def run(llm, example, context, fmt, temperature=0.0, sample_id=0):
        messages = build_messages(style, context, example.question, fewshot, fmt, system)
        response = llm.chat(messages, temperature=temperature, sample_id=sample_id)
        pred = Prediction(output=response.text)
        pred.add_usage(response)
        pred.answer, pred.how = extract_answer(response.text)
        return pred
    return run


def program_of_thought(llm, example, context, fmt, fewshot=True, repair=True):
    """The model writes Python; the sandbox runs it. If the code fails, the error is shown to
    the model once so it can repair the code."""
    messages = build_messages("pot", context, example.question, fewshot, fmt)
    response = llm.chat(messages)
    pred = Prediction(output=response.text)
    pred.add_usage(response)
    pred.code = extract_code(response.text)
    result = run_code(pred.code)
    if not result.ok and repair:
        messages += [{"role": "assistant", "content": response.text},
                     {"role": "user", "content": REPAIR_PROMPT.format(error=result.error)}]
        response = llm.chat(messages)
        pred.add_usage(response)
        pred.extra["first_error"] = result.error
        pred.output, pred.code = response.text, extract_code(response.text)
        result = run_code(pred.code)
    pred.trace, pred.error = result.trace, result.error
    if result.ok:
        pred.answer, pred.how = to_answer(result.ans), "code"
    return pred


def _vote_key(answer):
    return answer if isinstance(answer, str) else round(answer, 2)


def self_consistency(llm, example, context, fmt, samples=SC_SAMPLES):
    """Sample several few-shot CoT reasoning paths and take a majority vote: sample 0 is the greedy
    path (temperature 0, the same answer as few-shot CoT), the others use temperature 0.7."""
    cot = text_strategy("cot", fewshot=True)
    pred = Prediction(how="vote")
    votes = []
    for i in range(samples):
        temperature = 0.0 if i == 0 else SC_TEMPERATURE
        sample = cot(llm, example, context, fmt, temperature=temperature, sample_id=i)
        pred.n_calls += sample.n_calls
        pred.prompt_tokens += sample.prompt_tokens
        pred.completion_tokens += sample.completion_tokens
        pred.latency += sample.latency
        votes.append(sample)
    valid = [s for s in votes if s.answer is not None]
    if valid:
        counts = Counter(_vote_key(s.answer) for s in valid)
        winner, n_votes = counts.most_common(1)[0]   # ties go to the answer seen first
        chosen = next(s for s in valid if _vote_key(s.answer) == winner)
        pred.answer, pred.output = chosen.answer, chosen.output
        pred.extra["agreement"] = n_votes / samples
    pred.extra["votes"] = [s.answer for s in votes]
    return pred


def program_consistency(llm, example, context, fmt, samples=SC_SAMPLES, verify=True):
    """Our method, Verified Program Self-Consistency (VPSC): sample several programs, run each,
    keep only programs whose numbers are grounded in the report, then take a majority vote.
    With verify=False this is plain Program-of-Thought self-consistency (the ablation)."""
    messages = build_messages("pot", context, example.question, True, fmt)
    pred = Prediction(how="verified_vote" if verify else "vote")
    runs = []
    for i in range(samples):
        temperature = 0.0 if i == 0 else SC_TEMPERATURE   # sample 0 is the greedy program
        response = llm.chat(messages, temperature=temperature, sample_id=i)
        pred.add_usage(response)
        code = extract_code(response.text)
        result = run_code(code)
        grounded, missing = grounding_check(code, context) if result.ok else (False, [])
        runs.append({"code": code, "output": response.text, "result": result, "grounded": grounded,
                     "missing": missing, "answer": to_answer(result.ans) if result.ok else None})
    executed = [r for r in runs if r["answer"] is not None]
    pool = [r for r in executed if r["grounded"]] if verify else executed
    if verify and not pool:   # no program passed verification: fall back to every executed one
        pool = executed
    if pool:
        counts = Counter(_vote_key(r["answer"]) for r in pool)
        winner, n_votes = counts.most_common(1)[0]
        chosen = next(r for r in pool if _vote_key(r["answer"]) == winner)
        pred.answer, pred.output, pred.code = chosen["answer"], chosen["output"], chosen["code"]
        pred.trace = chosen["result"].trace
        pred.extra["agreement"] = n_votes / samples
    else:
        pred.output, pred.code, pred.error = runs[0]["output"], runs[0]["code"], runs[0]["result"].error
    pred.extra.update(votes=[r["answer"] for r in runs], grounded=[r["grounded"] for r in runs],
                      ungrounded_numbers=[r["missing"] for r in runs], n_executed=len(executed))
    return pred


def _same_answer(a, b, rel_tol=0.01):
    """Two answers agree if both are the same yes/no, or numbers within 1% (chain-of-thought rounds
    its answers, e.g. 21.88 for a program's 21.8826...)."""
    if isinstance(a, str) or isinstance(b, str):
        return a == b
    if b == 0:
        return abs(a) <= 0.005
    return abs(a - b) <= rel_tol * abs(b) or round(a, 2) == round(b, 2)


def verified_hybrid_vote(candidates):
    """candidates: dicts with answer, weight and is_program, in tie-break order. Answers that agree
    are pooled; the pool with the largest total weight wins, and its value is taken from a verified
    program when it has one (programs are exact, chain-of-thought answers are rounded)."""
    pools = []
    for c in candidates:
        if c["answer"] is None or c["weight"] <= 0:
            continue
        for pool in pools:
            if _same_answer(c["answer"], pool["members"][0]["answer"]):
                pool["members"].append(c)
                pool["weight"] += c["weight"]
                break
        else:
            pools.append({"members": [c], "weight": c["weight"]})
    if not pools:
        return None, []
    best = max(pools, key=lambda p: p["weight"])   # ties go to the pool seen first
    chosen = next((m for m in best["members"] if m["is_program"]), best["members"][0])
    return chosen, pools


def vpsc_v2(llm, example, context, fmt):
    """VPSC v2 (Verified Program Self-Consistency with diverse views). Five calls, as in v1:
      - 3 programs: the original few-shot prompt (greedy) and the operation-aware prompt
        (greedy + one sample at T=0.7), so the programs no longer share one prompt;
      - 2 chain-of-thought paths (greedy + one sample at T=0.7) as an independent second modality.
    Each executed program is verified three ways (numbers grounded in the report, operation matches
    the question, years inside the question's span); only verified programs vote. Agreeing answers
    are pooled with a 1% tolerance and the heaviest pool wins. If no program passes, the
    chain-of-thought paths decide."""
    from .prompts import guided_pot_messages
    from .verify import verify_program
    question = example.question
    pred = Prediction(how="verified_hybrid_vote")
    views = [("guided", guided_pot_messages(context, question, fmt), 0.0, 0),
             ("guided", guided_pot_messages(context, question, fmt), SC_TEMPERATURE, 1),
             ("original", build_messages("pot", context, question, True, fmt), 0.0, 0)]
    candidates, programs = [], []
    for view, messages, temperature, sample_id in views:
        response = llm.chat(messages, temperature=temperature, sample_id=sample_id)
        pred.add_usage(response)
        code = extract_code(response.text)
        result = run_code(code)
        answer = to_answer(result.ans) if result.ok else None
        problems = verify_program(code, context, question) if result.ok else ["did not run"]
        run = {"answer": answer, "weight": 0.0 if problems else 1.0, "is_program": True, "view": view,
               "code": code, "output": response.text, "result": result, "problems": problems}
        programs.append(run)
        candidates.append(run)
    cot = text_strategy("cot", fewshot=True)
    cots = []
    for sample_id in range(2):
        temperature = 0.0 if sample_id == 0 else SC_TEMPERATURE
        sample = cot(llm, example, context, fmt, temperature=temperature, sample_id=sample_id)
        pred.n_calls += sample.n_calls
        pred.prompt_tokens += sample.prompt_tokens
        pred.completion_tokens += sample.completion_tokens
        pred.latency += sample.latency
        run = {"answer": sample.answer, "weight": 1.0, "is_program": False, "view": "cot",
               "output": sample.output}
        cots.append(run)
        candidates.append(run)
    chosen, pools = verified_hybrid_vote(candidates)
    if chosen is None:   # nothing verified and no CoT answer: fall back to any program that ran
        executed = [p for p in programs if p["answer"] is not None]
        chosen = executed[0] if executed else None
    if chosen is not None:
        pred.answer, pred.output = chosen["answer"], chosen["output"]
        if chosen["is_program"]:
            pred.code, pred.trace = chosen["code"], chosen["result"].trace
        pred.extra["agreement"] = (max(p["weight"] for p in pools) / 5) if pools else 0.0
        pred.extra["chosen_view"] = chosen["view"]
    else:
        pred.output, pred.code, pred.error = programs[0]["output"], programs[0]["code"], programs[0]["result"].error
    pred.extra.update(
        votes=[c["answer"] for c in candidates],
        views=[c["view"] for c in candidates],
        verified=[c["weight"] > 0 for c in programs],
        problems=[c.get("problems", []) for c in programs],
        grounded=[not any(p.startswith("numbers not in") for p in c["problems"]) for c in programs],
        n_executed=sum(p["answer"] is not None for p in programs))
    return pred


STRATEGIES = {
    "direct": text_strategy("direct", fewshot=False),
    "cot_zs": text_strategy("cot", fewshot=False),
    "cot_fs": text_strategy("cot", fewshot=True),
    "decomp_fs": text_strategy("decomp", fewshot=True),
    "pot_fs": program_of_thought,
    "sc_cot": self_consistency,
    "pot_sc": lambda llm, example, context, fmt: program_consistency(llm, example, context, fmt,
                                                                      verify=False),
    "vpsc": program_consistency,
    "vpsc2": vpsc_v2,
}


def _artifact_path(name):
    """'dspy:artifacts/x.json' -> absolute path (relative paths are relative to the project root)."""
    path = Path(name.split(":", 1)[1])
    return path if path.is_absolute() else ROOT / path


def get_strategy(name):
    """Look up a strategy. 'textgrad:<file>' uses a system prompt optimized by TextGrad;
    'dspy:<file>' uses a program compiled by DSPy."""
    if name.startswith("textgrad:"):
        artifact = json.load(open(_artifact_path(name)))
        return text_strategy("cot", fewshot=False, system=artifact["system_prompt"])
    if name.startswith("dspy:"):
        from .dspy_opt import DSPyStrategy
        return DSPyStrategy(str(_artifact_path(name)))
    if name.startswith("trace"):
        from . import trace
        return {"trace": trace.trace_strategy, "trace_adaptive": trace.trace_adaptive}[name]
    return STRATEGIES[name]
