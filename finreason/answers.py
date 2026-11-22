"""Parse numbers from text (Indian and Western formats) and score answers against the gold value."""
import math
import re
from decimal import ROUND_HALF_UP, Decimal

from .config import REL_TOLERANCE

NUMBER_RE = re.compile(
    r"(?P<sign>[-−–])?\s*(?P<open>\()?\s*(?:rs\.?|inr|usd|₹|\$)?\s*"
    r"(?P<num>\d[\d,]*(?:\.\d+)?|\.\d+)\s*(?P<close>\))?\s*(?P<pct>%)?"
    r"(?:\s*(?P<scale>thousands?|lakhs?|lacs?|millions?|mn|crores?|cr|billions?|bn)\b)?",
    re.IGNORECASE,
)
ANSWER_RE = re.compile(r"answer\s*\**\s*[:：]\s*\**\s*(.+)", re.IGNORECASE)
BOXED_RE = re.compile(r"\\boxed\{([^{}]*)\}")
PERCENT_HINTS = re.compile(r"percent|%|portion|proportion|ratio|rate|share|margin|yield|growth|return",
                           re.IGNORECASE)


def _clean(text):
    """Remove markdown/LaTeX decoration that would confuse the number parser."""
    text = re.sub(r"<think>.*?</think>", " ", text, flags=re.DOTALL)
    for token in ("**", "\\%", "\\$", "\\,", "\\!", "\\left", "\\right", "\\text"):
        text = text.replace(token, "%" if token == "\\%" else " ")
    return text


def find_numbers(text):
    """Return every number in the text as a list of dicts with value, scale word and % flag."""
    found = []
    for m in NUMBER_RE.finditer(_clean(text)):
        digits = m.group("num").replace(",", "")
        value = float(digits)
        if m.group("sign") or (m.group("open") and m.group("close")):
            value = -value
        found.append({"value": value, "scale": (m.group("scale") or "").lower(),
                      "percent": bool(m.group("pct"))})
    return found


def parse_number(text):
    """First number in the text, e.g. '(1,25,000.50)' -> -125000.5, '12.98%' -> 12.98."""
    numbers = find_numbers(text)
    return numbers[0]["value"] if numbers else None


def _yes_no(segment):
    word = segment.strip().lower().strip(".*`'\" ")
    if word.startswith("yes"):
        return "yes"
    if word.startswith("no"):
        return "no"
    return None


def extract_answer(text):
    """Find the final answer in model output. Returns (answer, how) where how is
    'answer_line', 'boxed', 'last_number' or None when nothing could be parsed."""
    text = _clean(text or "")
    lines = ANSWER_RE.findall(text)
    if lines:
        segment = lines[-1]
        boxed = BOXED_RE.findall(segment)
        segment = boxed[-1] if boxed else segment
        word = _yes_no(segment)
        if word:
            return word, "answer_line"
        value = parse_number(segment)
        if value is not None:
            return value, "answer_line"
    boxed = BOXED_RE.findall(text)
    if boxed:
        word = _yes_no(boxed[-1])
        value = word or parse_number(boxed[-1])
        if value is not None:
            return value, "boxed"
    numbers = find_numbers(text)
    if numbers:
        return numbers[-1]["value"], "last_number"
    return None, None


def to_answer(value):
    """Convert a raw value (from code execution or DSPy output) into a float or yes/no."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return _yes_no(value) or parse_number(value)
    return None


def _decimals(x):
    """Number of decimal places the gold value was written with (17.70 -> 1, 273.0 -> 0)."""
    exponent = Decimal(repr(float(x))).normalize().as_tuple().exponent
    return max(0, -exponent)


def _round(x, places):
    return float(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def allows_percent(question, scale=""):
    """Percent questions may be answered as 12.5 (percent) or 0.125 (fraction)."""
    return scale == "percent" or bool(PERCENT_HINTS.search(question or ""))


def gold_forms(gold, question="", scale=""):
    """The gold value plus, for percentage questions, its x100 and /100 forms.
    Each form comes with the number of decimals it was written with.
    FinQA stores 12.5% as 0.125 while TAT-QA stores it as 12.5, so both must be accepted."""
    places = _decimals(gold)
    forms = [(gold, places)]
    if allows_percent(question, scale):
        forms += [(gold * 100, max(0, places - 2)), (gold / 100, places + 2)]
    return forms


def score(pred, gold, question="", scale="", rel_tol=REL_TOLERANCE):
    """Return (execution_correct, exact_match).

    execution_correct: the prediction is within rel_tol (default 0.5%) of the gold value, or
    equals the gold value when rounded to the number of decimals the gold was written with.
    exact_match: prediction and gold agree when both are rounded to 2 decimals.
    """
    if pred is None:
        return False, False
    if isinstance(gold, str) or isinstance(pred, str):
        same = isinstance(gold, str) and isinstance(pred, str) and pred == gold
        return same, same
    if not math.isfinite(pred):
        return False, False
    places = _decimals(gold)
    within_tolerance = rounded_match = exact = False
    for g, d in gold_forms(gold, question, scale):
        if g == 0:
            within_tolerance |= abs(pred) <= 0.005
        else:
            within_tolerance |= abs(pred - g) <= rel_tol * abs(g)
        if places >= 1:
            rounded_match |= _round(pred, d) == _round(g, d)
        exact |= _round(pred, 2) == _round(g, 2)
    return within_tolerance or rounded_match or exact, exact


def _tokens(x):
    if isinstance(x, float):
        return [f"{_round(x, 2):.2f}"]
    return str(x).lower().split()


def token_f1(pred, gold, question="", scale=""):
    """TAT-QA style bag-of-tokens F1 (numbers written with 2 decimals), best over gold forms.
    For a single-number answer this equals exact match; it differs only for multi-token answers."""
    if pred is None or (isinstance(pred, float) and not math.isfinite(pred)):
        return 0.0
    golds = [gold] if isinstance(gold, str) else [g for g, _ in gold_forms(gold, question, scale)]
    best = 0.0
    for g in golds:
        p, t = _tokens(pred), _tokens(g)
        common = sum(min(p.count(tok), t.count(tok)) for tok in set(p))
        if common:
            precision, recall = common / len(p), common / len(t)
            best = max(best, 2 * precision * recall / (precision + recall))
    return best
