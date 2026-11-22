"""Cell-level provenance audit for model-written programs (used by TRACE).

VPSC v1 asked only "does every number in the program occur somewhere in the report?". Most wrong
programs pass that test: they copy a real number from the wrong row or the wrong year. This module
aligns every operand with the table cell(s) it came from and checks it against two independent
descriptions of what the operand *should* be:

  1. the program's own variable name (PoT prompts ask for descriptive names such as
     ``lease_obligations_2008``): the name points to a row (by its words) and a column (by its year),
     and the literal must equal the value in that cell;
  2. the question: the years of the columns the program reads must lie inside the span of years the
     question asks about.

Each problem is reported with a concrete, checkable explanation (and, where possible, the value the
named cell actually holds), which TRACE turns into targeted repair feedback.
"""
import ast
import re
from dataclasses import dataclass, field

from .answers import find_numbers
from .verify import CONSTANTS, code_literals, is_grounded, operation_check, year_check

SCALE_WORDS = {"thousand": 1e3, "thousands": 1e3, "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5,
               "million": 1e6, "millions": 1e6, "mn": 1e6, "crore": 1e7, "crores": 1e7, "cr": 1e7,
               "billion": 1e9, "billions": 1e9, "bn": 1e9}
YES_NO_Q = re.compile(r"^\s*(did|does|do|is|was|were|are|has|have|had|can|could|will|would|should)\b", re.I)


def grounding_check(code, context):
    """Value-level grounding (as in VPSC) made unit-aware: a number written with a scale word in the
    report ("$16 million") also grounds its expanded form (16000000) in the program."""
    report = set()
    for n in find_numbers(context):
        report.add(abs(n["value"]))
        if n["scale"] in SCALE_WORDS:
            report.add(abs(n["value"]) * SCALE_WORDS[n["scale"]])
    missing = [v for v in code_literals(code) if not is_grounded(v, report)]
    return not missing, missing


def answer_type_problem(question, answer):
    """A yes/no question needs a yes/no answer and any other question a number."""
    if answer is None:
        return None
    yes_no = bool(YES_NO_Q.match(question))
    if yes_no and not isinstance(answer, str):
        return Problem("answer_type", "the question asks for yes or no, but the answer is a number", 1.0)
    if not yes_no and isinstance(answer, str):
        return Problem("answer_type", "the question asks for a number, but the answer is yes/no", 1.0)
    return None

YEAR_RE = re.compile(r"(?<![\d.])(19[5-9]\d|20[0-4]\d)(?![\d.])")
STOPWORDS = {
    "the", "of", "and", "in", "for", "to", "a", "an", "at", "on", "by", "from", "as", "or", "is",
    "value", "amount", "ans", "x", "y", "val", "num", "number", "year", "fy", "end", "s",
    "dec", "december", "march", "june", "september", "sept", "jan", "january", "millions", "million",
    "thousands", "thousand", "billions", "billion", "crore", "crores", "lakh", "lakhs", "usd", "inr",
    "dollars", "rs", "in", "per", "share", "item", "items", "table", "text", "prev", "previous",
    "current", "curr", "new", "old", "start", "beginning", "ending", "begin", "close", "open",
}
SCALE_FACTORS = (1, 100, 0.01, 1000, 0.001, 1e5, 1e-5, 1e7, 1e-7)


def _stem(token):
    return token[:-1] if len(token) > 3 and token.endswith("s") else token


def content_tokens(text):
    """Lower-case word tokens without years, numbers and stopwords, lightly stemmed."""
    words = re.findall(r"[a-z]+", text.lower().replace("_", " "))
    return {_stem(w) for w in words if w not in STOPWORDS and len(w) > 1}


def _cell_value(cell):
    numbers = find_numbers(str(cell))
    if not numbers:
        return None
    value = numbers[0]["value"]
    # FinQA writes negatives as "-16 ( 16 )"; the first number already carries the sign
    return value


def _same(a, b):
    return abs(a - b) <= 1e-6 * max(1.0, abs(b))


def _matches(literal, value):
    """literal equals the cell value up to sign and a unit rescaling (1.1 bn -> 1100 mn, 12% -> 0.12)."""
    if value is None:
        return False
    return any(_same(abs(literal), abs(value) * f) for f in SCALE_FACTORS)


HEADER_YEAR_RE = re.compile(r"(?<![\d.])\d*?(19[5-9]\d|20[0-4]\d)(?![\d.])")


def header_years(text):
    """Years in a header cell; tolerates FinQA's glued dates such as 'december 312017'."""
    return {int(y) for y in HEADER_YEAR_RE.findall(str(text))}


def _is_header_row(row):
    """A row is a (repeated) header if it has text in some value column and no number in any value
    column other than years (e.g. '| (In Millions) | Dec 30, 2017 | Acquisitions |')."""
    cells = [c for c in row[1:] if c.strip()]
    if not cells:
        return False
    for c in cells:
        numbers = [n["value"] for n in find_numbers(c)]
        if any(not (float(v).is_integer() and 1950 <= abs(v) <= 2049) and v not in header_years(c)
               and not header_years(c) for v in numbers):
            return False
    return True


@dataclass
class Cell:
    row: int
    col: int
    row_label: str
    header: str
    value: float
    years: set = field(default_factory=set)
    tokens: set = field(default_factory=set)


class TableIndex:
    """Every numeric cell of a table with its row label, column header and the header's years."""

    def __init__(self, table):
        self.cells = []
        self.rows = {}
        if not table or len(table) < 2:
            return
        width = max(len(r) for r in table)
        col_header = [""] * width          # header text seen so far for each column
        col_years = [set() for _ in range(width)]
        for i, row in enumerate(table):
            row = [str(c) for c in row] + [""] * (width - len(row))
            if i == 0 or _is_header_row(row):
                # real reports repeat headers mid-table and span a year over several columns
                # ("As of December 31, 2018 | | |"): forward-fill years to the right inside the row
                found = [header_years(row[j]) if j else set() for j in range(width)]
                distinct = {frozenset(y) for y in found if y}
                row_years, carry = [set() for _ in range(width)], set()
                for j in range(1, width):
                    if found[j]:
                        carry = row_years[j] = found[j]
                    elif not row[j].strip():
                        # an empty cell under a spanning header: one year in the row covers every
                        # empty column, otherwise the year to the left carries over
                        row_years[j] = set(next(iter(distinct))) if len(distinct) == 1 else carry
                if any(row_years):          # a new header section starts
                    col_years = row_years
                    col_header = list(row)
                else:                       # a second header line ("Amortized | Unrealized")
                    col_header = [(col_header[j] + " " + row[j]).strip() for j in range(width)]
                continue
            label = row[0]
            label_tokens = content_tokens(label)
            self.rows[i] = (label, label_tokens)
            # years named in the row label (e.g. "2003 net revenue") also describe the row's period
            label_years = {int(y) for y in YEAR_RE.findall(label)}
            for j in range(1, width):
                value = _cell_value(row[j])
                if value is None:
                    continue
                years = col_years[j] or label_years
                self.cells.append(Cell(i, j, label, col_header[j], value, years,
                                       label_tokens | content_tokens(col_header[j]),
                                       ))
                self.cells[-1].label_years = label_years

    def cells_with_value(self, literal):
        return [c for c in self.cells if _matches(literal, c.value)]

    def column_years(self):
        return sorted({y for c in self.cells for y in c.years})

    def best_row(self, tokens):
        """Row whose label shares the most words with tokens; None unless the match is clear."""
        if not tokens:
            return None
        scored = []
        for i, (label, label_tokens) in self.rows.items():
            if not label_tokens:
                continue
            overlap = len(tokens & label_tokens)
            if overlap:
                scored.append((overlap / len(tokens), overlap / len(label_tokens), i))
        if not scored:
            return None
        scored.sort(reverse=True)
        best = scored[0]
        if best[0] < 1.0:                           # every word of the name must be in the label
            return None
        if len(scored) > 1 and scored[1][:2] == best[:2]:   # tie: ambiguous
            return None
        return best[2]


def literal_assignments(code):
    """(variable name, literal value, line) for assignments whose right side is a plain number or a
    product/quotient of a number with a unit constant, e.g. ``x = 3338`` or ``y = 1.1 * 1000``."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        value = _literal(node.value)
        if value is not None:
            out.append((node.targets[0].id, value, node.lineno))
    return out


def _literal(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
            and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _literal(node.operand)
        return -inner if inner is not None else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div)):
        left, right = _literal(node.left), _literal(node.right)
        if left is not None and right is not None and right in CONSTANTS:
            return left   # the report value is the one being rescaled
    return None


@dataclass
class Problem:
    kind: str          # ungrounded / name_cell / name_year / question_span / operation / year_name / no_ans
    message: str       # human-readable explanation, also used as repair feedback
    severity: float    # 1.0 = almost certainly wrong, 0.5 = suspicious


def audit_program(code, context, question, table, text=""):
    """All provenance and question-consistency checks for one executed program.
    Returns a list of Problems (empty = the program passes the audit)."""
    problems = []
    grounded, missing = grounding_check(code, context)
    if not grounded:
        problems.append(Problem("ungrounded", f"the numbers {missing} do not appear anywhere in the "
                                "report; use the exact values from the table or text", 1.0))
    if (msg := operation_check(question, code)):
        problems.append(Problem("operation", f"the program {msg} (later value minus earlier value, "
                                "no division)", 0.5))
    if (msg := year_check(question, code)):
        problems.append(Problem("year_name", f"the program {msg}", 0.5))

    index = TableIndex(table)
    if not index.cells:
        return problems
    asked = {int(y) for y in YEAR_RE.findall(question)}
    lo, hi = (min(asked), max(asked)) if len(asked) >= 2 else (None, None)
    text_numbers = [n["value"] for n in find_numbers(text)] if text else []
    for name, literal, _ in literal_assignments(code):
        hits = index.cells_with_value(literal)
        if not hits or (abs(literal) in CONSTANTS and len(hits) > 2):
            continue
        in_text = any(_matches(literal, t) for t in text_numbers)
        name_years = {int(y) for y in YEAR_RE.findall(name.replace("_", " "))}
        tokens = content_tokens(re.sub(r"\d+", " ", name))
        # (1) the name points to a cell (row by its words, column by its year) that holds another
        # value, and the literal itself comes only from rows that match the name less well
        row = index.best_row(tokens) if len(tokens) >= 2 else None
        best_overlap = len(tokens & index.rows[row][1]) if row is not None else 0
        related = [c for c in hits if len(tokens & index.rows[c.row][1]) >= best_overlap]
        if row is not None and len(name_years) == 1 and not related and not in_text:
            year = next(iter(name_years))
            target = [c for c in index.cells if c.row == row and year in c.years]
            if len(target) == 1 and not _matches(literal, target[0].value):
                t = target[0]
                problems.append(Problem(
                    "name_cell", f"`{name} = {_fmt(literal)}`, but the table row '{t.row_label}' in "
                    f"column '{t.header}' holds {_fmt(t.value)}", 1.0))
                continue
        # (2) the literal comes only from columns of other years than the one in its name
        if name_years and not in_text:
            hit_years = set().union(*(c.years | getattr(c, "label_years", set()) for c in hits))
            if hit_years and not (hit_years & name_years):
                where = ", ".join(sorted({f"'{c.row_label}' / '{c.header}'" for c in hits})[:2])
                problems.append(Problem(
                    "name_year", f"`{name} = {_fmt(literal)}` is named for {sorted(name_years)} but "
                    f"that number is in {where}", 1.0))
                continue
        # (3) the literal comes only from columns outside the span of years the question asks about
        if lo is not None and not in_text:
            hit_years = set().union(*(c.years | getattr(c, "label_years", set()) for c in hits))
            if hit_years and all(not lo <= y <= hi for y in hit_years):
                problems.append(Problem(
                    "question_span", f"the question asks about {lo}-{hi} but `{name} = "
                    f"{_fmt(literal)}` comes from a column for {sorted(hit_years)}", 1.0))
    return problems


def _fmt(x):
    return f"{x:g}" if isinstance(x, float) else str(x)


def missing_ans_fix(code):
    """If the program never assigns `ans`, assign the last variable it computed (a common slip of
    small models, e.g. ending with ``growth_rate = ...``). Returns the fixed code or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return None
    targets = [n.targets[0].id for n in tree.body
               if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)]
    if not targets or "ans" in targets:
        return None
    return code.rstrip() + f"\nans = {targets[-1]}\n"
