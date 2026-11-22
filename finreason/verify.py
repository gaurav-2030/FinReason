"""Grounding verification for model-written programs: every number typed into the code must
appear in the report (or be a harmless constant such as 100 or 1000)."""
import ast

from .answers import find_numbers

# Numbers a program may use without finding them in the report: small counts (years, periods),
# percentage and unit-conversion factors (thousand, lakh, million, crore, billion) and years.
CONSTANTS = set(range(0, 13)) | {100, 1000, 10**5, 10**6, 10**7, 10**9}
SCALE_FACTORS = (1, 100, 0.01, 1000, 0.001)


def code_literals(code):
    """All numeric constants written in the code, e.g. 'x = 3338 * 1.1' -> [3338, 1.1]."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    return [abs(node.value) for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)]


def is_grounded(value, report_numbers):
    """True if value is a constant or appears in the report (possibly rescaled, e.g. 1.1 bn -> 1100)."""
    if value in CONSTANTS or (float(value).is_integer() and 1900 <= value <= 2100):
        return True
    for n in report_numbers:
        for factor in SCALE_FACTORS:
            target = n * factor
            if abs(value - target) <= 1e-6 * max(1.0, abs(target)):
                return True
    return False


def grounding_check(code, context):
    """Return (grounded, ungrounded_literals) for a program, given the context the model saw."""
    report_numbers = {abs(n["value"]) for n in find_numbers(context)}
    missing = [v for v in code_literals(code) if not is_grounded(v, report_numbers)]
    return not missing, missing


# --- VPSC v2: question-program consistency checks ---------------------------------------------
# Grounding only asks "are the numbers in the report?". Most wrong programs pass it: they use real
# report numbers but the wrong operation or the wrong year. These two checks compare the program
# with the question itself.
import re   # noqa: E402

PERCENT_WORDS = re.compile(r"percent|%|\brate\b|ratio|proportion|portion|share|fraction|"
                           r"return on|yield|margin|times|per\b|each|average|mean", re.I)
CHANGE_WORDS = re.compile(r"\b(change|difference|increase|decrease|variation|differ)\b", re.I)
# "2019s" is FinQA's mangled apostrophe ("company 2019s" = "company's"), not a year
YEAR = re.compile(r"(?<![\d.])(19[5-9]\d|20[0-4]\d)(?![\d.]|s\b)")


def _code_without_comments(code):
    return "\n".join(line.split("#", 1)[0] for line in code.splitlines())


def _divides(code):
    """True if the program divides (/ or //) anywhere outside comments and strings."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return "/" in _code_without_comments(code)
    return any(isinstance(node, (ast.BinOp, ast.AugAssign)) and isinstance(node.op, (ast.Div, ast.FloorDiv))
               for node in ast.walk(tree))


def operation_check(question, code):
    """A plain 'what was the change in X' question (no percent/ratio/average wording) is answered
    by a subtraction; a program that divides is computing a percentage or ratio instead."""
    if CHANGE_WORDS.search(question) and not PERCENT_WORDS.search(question) and _divides(code):
        return "divides, but the question asks for a plain change"
    return None


def year_check(question, code):
    """If the question names a span of years (e.g. 'from 2017 to 2018'), the program should not
    use a year outside that span (e.g. a variable named cash_2019)."""
    asked = {int(y) for y in YEAR.findall(question)}
    if len(asked) < 2:   # 'in 2012' alone may legitimately need 2011 for a change
        return None
    used = {int(y) for y in YEAR.findall(_code_without_comments(code))}
    outside = sorted(y for y in used if not min(asked) <= y <= max(asked))
    return f"uses year(s) {outside} outside the question's {min(asked)}-{max(asked)}" if outside else None


def verify_program(code, context, question):
    """All VPSC v2 checks for one executed program. Returns a list of problems (empty = verified)."""
    problems = []
    grounded, missing = grounding_check(code, context)
    if not grounded:
        problems.append(f"numbers not in the report: {missing}")
    for check in (operation_check, year_check):
        if (problem := check(question, code)):
            problems.append(problem)
    return problems
