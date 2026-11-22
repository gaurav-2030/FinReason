"""Rule-based error taxonomy: assigns every wrong prediction to exactly one error category."""
from .answers import find_numbers, gold_forms
from .finqa_program import numeric_arguments, to_number

CATEGORIES = [
    "no_answer",           # the model produced no parsable answer
    "execution_error",     # Program-of-Thought code failed even after one repair attempt
    "sign_error",          # right magnitude, wrong sign (e.g. increase vs decrease)
    "scale_error",         # off by a power of ten: thousand / lakh / million / crore / billion
    "rounding_near_miss",  # within 5% but outside the 0.5% tolerance
    "no_work_shown",       # wrong, and the output shows no intermediate numbers to diagnose
    "evidence_error",      # at least one gold operand never appears in the model's work
    "reasoning_error",     # all gold operands appear, but the formula or arithmetic is wrong
]
SCALE_FACTORS = [1e2, 1e3, 1e5, 1e6, 1e7, 1e9]


def gold_operands(example):
    """The numbers the correct calculation uses (taken from the gold program or derivation)."""
    if example.dataset == "finqa":
        return [abs(to_number(a, [])) for a in numeric_arguments(example.gold_program)]
    values = [abs(n["value"]) for n in find_numbers(example.gold_program)]
    # drop constants such as *100 for percentages or /2 for an average
    return [v for v in values if v not in (100, 1000) and not (v.is_integer() and v <= 4)]


def _appears(value, numbers):
    """True if value (or value written in thousands / in units) is among the numbers."""
    for n in numbers:
        for factor in (1, 1e3, 1e-3):
            if abs(abs(n) - value * factor) <= max(0.005, 1e-4 * value * factor):
                return True
    return False


def _close(a, b, tol=0.01):
    return b != 0 and abs(a - b) <= tol * abs(b)


def classify_error(pred, example, correct):
    """Return None for a correct prediction, otherwise one category from CATEGORIES."""
    if correct:
        return None
    if pred.answer is None:
        return "execution_error" if pred.code else "no_answer"
    gold = example.gold
    if isinstance(gold, str) or isinstance(pred.answer, str):
        return "reasoning_error"
    forms = [g for g, _ in gold_forms(gold, example.question, example.scale)]
    if any(_close(-pred.answer, g) for g in forms):
        return "sign_error"
    for g in forms:
        for factor in SCALE_FACTORS:
            if _close(abs(pred.answer), abs(g) * factor) or _close(abs(pred.answer), abs(g) / factor):
                return "scale_error"
    if any(_close(pred.answer, g, tol=0.05) for g in forms):
        return "rounding_near_miss"
    operands = gold_operands(example)
    work = find_numbers(pred.code or pred.output)
    numbers = [n["value"] for n in work]
    if len(numbers) <= 1:
        return "no_work_shown"
    if operands and not all(_appears(op, numbers) for op in operands):
        return "evidence_error"
    return "reasoning_error"
