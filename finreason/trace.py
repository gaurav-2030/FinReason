"""TRACE: Table-grounded Repair, Audit, Consensus and Escalation.

The successor of VPSC. VPSC v1 sampled five programs from one prompt and filtered them by value-level
grounding; on our data the five programs agree with each other 91-99% of the time and the correct
answer is among them for only 57% of FinQA questions, so a filter has nothing to choose from. TRACE
attacks the three causes in turn:

  * Audit    - every program is checked at cell level (finreason.provenance): the operand named
               ``revenue_2019`` must be the value in the revenue row and the 2019 column, the columns
               read must match the years the question asks about, the operation must match the
               question, and every number must occur in the report.
  * Repair   - a program that fails the audit is not just discarded: the audit's findings (with the
               value the named cell actually holds) are returned to the model once as targeted
               feedback. This breaks the correlated errors that voting cannot fix.
  * Consensus- candidates come from diverse views (operation-guided and plain program prompts,
               chain-of-thought and decomposition) and are pooled with a 1% tolerance; only audited
               programs and text paths vote, and the pooled weight gives a calibrated confidence used
               for abstention.
  * Escalation- the cheap path (one guided program + one chain-of-thought) is accepted when the
               program passes the audit and both agree; only the remaining questions pay for the other
               views and repairs.

``trace`` always computes every view and logs each candidate with its own cost, so the adaptive
policy and all ablations can be replayed exactly from the log; ``trace_adaptive`` stops early online.
"""
from .answers import to_answer
from .config import SC_TEMPERATURE
from .prompts import build_messages, guided_pot_messages
from .provenance import answer_type_problem, audit_program, missing_ans_fix
from .sandbox import extract_code, run_code
from .strategies import Prediction, _same_answer, text_strategy

REPAIR_AUDIT_PROMPT = (
    "An automatic audit of your program against the report found these problems:\n{problems}\n"
    "Re-read the table and the question. Take every value from the row and column for exactly what "
    "the question asks, use the operation the question asks for, and store the result in ans. "
    "Return only the corrected code in one ```python block.")

# Default vote weights (chosen on the FinQA/TAT-QA dev splits, see scripts/trace_replay.py)
W_PROGRAM = 1.0        # a program that passes the audit
W_FLAGGED = 0.0        # a program with an audit problem (severity 1)
W_SOFT = 0.5           # a program with only a suspicious (severity 0.5) finding
W_TEXT = 0.75         # a chain-of-thought / decomposition answer (frozen on dev: flat 0.69-0.70 grid)


def _usage(response):
    return {"calls": 1, "prompt_tokens": response.prompt_tokens,
            "completion_tokens": response.completion_tokens, "latency": response.latency}


def _execute(code):
    """Run a program; if it never sets ans, assign its last computed variable and run again."""
    result = run_code(code)
    if not result.ok and "did not set" in result.error and (fixed := missing_ans_fix(code)):
        fixed_result = run_code(fixed)
        if fixed_result.ok:
            return fixed, fixed_result, True
    return code, result, False


def _program_candidate(view, messages, response, context, example):
    code, result, fixed = _execute(extract_code(response.text))
    text = "\n".join(example.texts)
    answer = to_answer(result.ans) if result.ok else None
    problems = audit_program(code, context, example.question, example.table, text) if result.ok else []
    if (p := answer_type_problem(example.question, answer)):
        problems.append(p)
    return {"view": view, "is_program": True, "answer": answer,
            "code": code, "output": response.text, "trace": result.trace if result.ok else {},
            "error": result.error, "ans_fixed": fixed,
            "problems": [(p.kind, p.severity, p.message) for p in problems],
            "messages": messages, "cost": _usage(response)}


def program_weight(c, w_program=W_PROGRAM, w_flagged=W_FLAGGED, w_soft=W_SOFT):
    if c["answer"] is None:
        return 0.0
    severities = [s for _, s, _ in c["problems"]]
    if not severities:
        return w_program
    return w_flagged if max(severities) >= 1.0 else w_soft


def pool_vote(candidates, weights):
    """Pool agreeing answers (1% tolerance); the heaviest pool wins. Returns (chosen, best_weight,
    total_weight). The winning value is taken from an audited program when the pool has one."""
    pools = []
    for c, w in zip(candidates, weights):
        if c["answer"] is None or w <= 0:
            continue
        for pool in pools:
            if _same_answer(c["answer"], pool["members"][0][0]["answer"]):
                pool["members"].append((c, w))
                pool["weight"] += w
                break
        else:
            pools.append({"members": [(c, w)], "weight": w})
    if not pools:
        return None, 0.0, 0.0
    best = max(pools, key=lambda p: p["weight"])
    members = sorted(best["members"], key=lambda m: (not m[0]["is_program"], -m[1]))
    return members[0][0], best["weight"], sum(p["weight"] for p in pools)


def trace_strategy(llm, example, context, fmt, adaptive=False, repair=True):
    question = example.question
    pred = Prediction(how="trace")
    cot = text_strategy("cot", fewshot=True)
    decomp = text_strategy("decomp", fewshot=True)

    def add(cost):
        pred.n_calls += cost["calls"]
        pred.prompt_tokens += cost["prompt_tokens"]
        pred.completion_tokens += cost["completion_tokens"]
        pred.latency += cost["latency"]

    def program(view, messages, temperature, sample_id):
        response = llm.chat(messages, temperature=temperature, sample_id=sample_id)
        c = _program_candidate(view, messages, response, context, example)
        add(c["cost"])
        return c

    def text_path(view, runner, temperature, sample_id):
        s = runner(llm, example, context, fmt, temperature=temperature, sample_id=sample_id)
        p = answer_type_problem(question, s.answer)
        c = {"view": view, "is_program": False, "answer": s.answer, "output": s.output,
             "problems": [(p.kind, p.severity, p.message)] if p else [], "cost": {"calls": s.n_calls, "prompt_tokens": s.prompt_tokens,
                                      "completion_tokens": s.completion_tokens, "latency": s.latency}}
        add(c["cost"])
        return c

    # Stage 1: the cheap path
    guided = guided_pot_messages(context, question, fmt)
    p_guided = program("pot_guided", guided, 0.0, 0)
    c_greedy = text_path("cot", cot, 0.0, 0)
    stage1 = [p_guided, c_greedy]
    early = (p_guided["answer"] is not None and not p_guided["problems"]
             and c_greedy["answer"] is not None and _same_answer(p_guided["answer"], c_greedy["answer"]))
    stage1_cost = {k: p_guided["cost"][k] + c_greedy["cost"][k] for k in p_guided["cost"]}

    candidates = list(stage1)
    if not (adaptive and early):
        # Stage 2: diverse views
        candidates.append(program("pot_plain", build_messages("pot", context, question, True, fmt), 0.0, 0))
        candidates.append(program("pot_guided_t", guided, SC_TEMPERATURE, 1))
        candidates.append(text_path("cot_t", cot, SC_TEMPERATURE, 1))
        candidates.append(text_path("decomp", decomp, 0.0, 0))
        # Repair: greedy programs that fail the audit get the audit findings back once
        if repair:
            for parent in [c for c in candidates if c["view"] in ("pot_guided", "pot_plain")]:
                hard = [m for _, s, m in parent["problems"] if s >= 1.0]
                if parent["answer"] is None and parent["error"]:
                    hard = [f"the program failed to run: {parent['error']}"]
                if not hard:
                    continue
                messages = parent["messages"] + [
                    {"role": "assistant", "content": parent["output"]},
                    {"role": "user", "content": REPAIR_AUDIT_PROMPT.format(
                        problems="\n".join(f"- {m}" for m in hard))}]
                fixed = program(parent["view"] + "_repair", messages, 0.0, 0)
                fixed["parent"] = parent["view"]
                candidates.append(fixed)

    if adaptive and early:
        chosen, best_w, total_w = p_guided, 2.0, 2.0
    else:
        weights = [program_weight(c) if c["is_program"] else (0.0 if c["problems"] else W_TEXT)
                   for c in candidates]
        # a repaired program replaces its parent's vote
        repaired = {c.get("parent") for c in candidates if c.get("parent") and program_weight(c) > 0}
        weights = [0.0 if c["view"] in repaired else w for c, w in zip(candidates, weights)]
        chosen, best_w, total_w = pool_vote(candidates, weights)
        if chosen is None:   # nothing audited and no text answer: any program that ran
            chosen = next((c for c in candidates if c["answer"] is not None), None)
    if chosen is not None:
        pred.answer, pred.output = chosen["answer"], chosen["output"]
        if chosen["is_program"]:
            pred.code, pred.trace = chosen["code"], chosen["trace"]
        pred.extra["chosen_view"] = chosen["view"]
    else:
        pred.output, pred.code, pred.error = p_guided["output"], p_guided["code"], p_guided["error"]
    pred.extra.update(
        confidence=(best_w / total_w) if total_w else 0.0, early_exit=early,
        stage1_cost=stage1_cost,
        candidates=[{k: c.get(k) for k in ("view", "is_program", "answer", "problems", "cost",
                                            "ans_fixed", "parent", "error", "code")}
                    for c in candidates])
    return pred


def trace_adaptive(llm, example, context, fmt):
    return trace_strategy(llm, example, context, fmt, adaptive=True)
