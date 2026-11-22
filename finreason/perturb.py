"""Numerical perturbation test: change the numbers a FinQA question depends on, recompute the gold
answer with the gold program, and check whether the model still answers correctly. A model that
memorized the original answer (instead of reasoning) will fail on the perturbed version."""
import random
import re
from dataclasses import replace

from .finqa_program import execute, numeric_arguments


def _decimals(text):
    return len(text.split(".")[1]) if "." in text else 0


def _forms(literal):
    """Ways a literal can be written in the report: '1234.5' and '1,234.5'."""
    whole, _, frac = literal.partition(".")
    return {literal, f"{int(whole):,}" + (f".{frac}" if frac else "")}


def _replace_all(text, new_values, hits):
    """Replace every listed number in one pass (so a new value is never replaced again)."""
    lookup = {form: lit for lit in new_values for form in _forms(lit)}
    pattern = re.compile(r"(?<![\d.,])(?:" + "|".join(
        re.escape(f) for f in sorted(lookup, key=len, reverse=True)) + r")(?![\d]|\.\d)")

    def swap(match):
        literal = lookup[match.group(0)]
        hits[literal] += 1
        return new_values[literal]
    return pattern.sub(swap, text)


def perturb_example(example, rng):
    """Return a perturbed copy of a FinQA example, or None if it cannot be perturbed safely."""
    program = example.gold_program
    if example.dataset != "finqa" or isinstance(example.gold, str) or "table_" in program:
        return None
    literals = sorted(set(numeric_arguments(program)))
    if not literals or any("%" in a or a.startswith("-") for a in literals):
        return None
    new_values = {}
    for literal in literals:
        value = float(literal.replace(",", ""))
        if value.is_integer() and 1900 <= value <= 2100:   # probably a year, not an amount
            return None
        factor = rng.uniform(0.7, 0.9) if rng.random() < 0.5 else rng.uniform(1.1, 1.3)
        places = _decimals(literal)
        new = round(value * factor, places)
        if new == value:
            new = value + 10 ** -places
        new_values[literal] = f"{new:.{places}f}"
    hits = {literal: 0 for literal in new_values}
    table = [[_replace_all(cell, new_values, hits) for cell in row] for row in example.table]
    texts = [_replace_all(sentence, new_values, hits) for sentence in example.texts]
    if not all(hits.values()):   # a number is not written in the report, so we cannot change it
        return None
    new_program = re.sub(
        r"(?<=[(,\s])(" + "|".join(re.escape(lit) for lit in new_values) + r")(?=[,)\s])",
        lambda m: new_values[m.group(1)], program)
    try:
        new_gold = execute(new_program, table)
    except (ZeroDivisionError, ValueError, OverflowError):
        return None
    return replace(example, uid=example.uid + "#perturbed", table=table, texts=texts,
                   gold=float(new_gold), gold_program=new_program,
                   meta={**example.meta, "original_uid": example.uid, "original_gold": example.gold})


def perturb_dataset(examples, seed=42):
    """Perturbed versions of all examples that can be perturbed (same seed -> same output)."""
    rng = random.Random(seed)
    perturbed = [perturb_example(ex, rng) for ex in examples]
    return [p for p in perturbed if p is not None]
