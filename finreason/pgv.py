"""Provenance-Graph Verification (PGV): programs lifted to typed formulas over report cells.

TRACE's audit inspects literals one at a time. PGV lifts a whole program into a *provenance graph*: a
symbolic formula (sympy) whose leaves are typed references to report evidence - a table cell with its
row label, period and unit, a number from the text with its scale word, or an ungrounded constant.
On that graph we can check properties no literal-level audit can see:

  * intent typing   - the formula's shape (difference, percentage change, ratio/share, sum, average,
                      CAGR, ...) must match the operation the question asks for;
  * period checking - the periods of the leaves must be the periods the question asks about, and a
                      change must be oriented later-minus-earlier (sign errors);
  * unit analysis   - leaves with different scales (text "$1.1 billion" vs a table "in millions")
                      must not be combined without a conversion;
  * structural consensus - two programs that read the same cells with the same formula agree even if
                      they copied the numbers differently; two that agree on a value by coincidence do not.

Everything is deterministic, needs no training or model call, and runs in milliseconds.
"""
import ast
import math
import random
import re
from dataclasses import dataclass, field
from itertools import combinations, permutations

import sympy as sp

from .answers import find_numbers
from .provenance import SCALE_WORDS, TableIndex, YEAR_RE, _matches, content_tokens
from .verify import CONSTANTS

SCALE_HEADER = re.compile(r"in\s+(thousands|millions|billions|crores?|lakhs?)|\((?:\$|rs\.?|inr|₹)?\s*"
                          r"(thousands|millions|billions|crores?|lakhs?)\)|(\$|us\$|rs\.?|₹)\s*'?000", re.I)
SCALE_OF = {"thousand": 3, "thousands": 3, "'000": 3, "million": 6, "millions": 6, "mn": 6, "billion": 9,
            "billions": 9, "bn": 9, "lakh": 5, "lakhs": 5, "lac": 5, "lacs": 5, "crore": 7, "crores": 7, "cr": 7}


# ------------------------------------------------------------------------------- question intent
INTENTS = [  # (intent, pattern), first match wins; developed on the dev / development samples only
    ("yesno", re.compile(r"^\s*(did|does|do|is|was|were|are|has|have|had|can|could|will|would|should)\b", re.I)),
    ("cagr", re.compile(r"\bcagr\b|compound(ed)? annual|annuali[sz]ed growth", re.I)),
    ("difference", re.compile(r"percentage points?|basis points?|change in (the )?(percent|percentage|ratio|rate|margin|share)\b", re.I)),
    ("pct_change", re.compile(r"(percent(age|ual)?|%)\s*(change|increase|decrease|decline|growth|difference|reduction|drop)"
                              r"|percent(age)? of (the )?(change|increase|decrease|decline|growth|reduction)"
                              r"|growth rate|rate of (growth|change|increase|decrease|decline)|\bgrowth\b|"
                              r"(change|increase|decrease|decline)\s+in\s+percent", re.I)),
    ("share", re.compile(r"(percent(age)?|%|portion|proportion|share|fraction)\s+(of|was|is|did|does|do)\b|"
                         r"\bas a (percent(age)?|%|share|portion)", re.I)),
    ("average", re.compile(r"\baverage\b|\bmean\b", re.I)),
    ("ratio", re.compile(r"\bratio\b|\btimes\b|\bmultiple\b|\bper\b|\bmargin\b|\breturn on\b|\byield\b", re.I)),
    ("difference", re.compile(r"\b(change|difference|increase|decrease|decline|variation|differ|net change|"
                              r"how much (more|less|higher|lower)|grew|fell)\b", re.I)),
    ("sum", re.compile(r"\b(sum|combined|aggregate|altogether|in total|total of)\b", re.I)),
]
COMPATIBLE = {  # intent -> formula shapes that can answer it
    "pct_change": {"pct_change", "single", "complex"},
    "difference": {"difference", "diff_of_sums", "single"},
    "ratio": {"ratio", "ratio_of_sums", "single", "complex", "pct_change"},
    "share": {"ratio", "ratio_of_sums", "single"},
    "average": {"average", "single", "difference", "diff_of_sums"},
    "sum": {"sum", "single", "diff_of_sums"},
    "cagr": {"cagr", "complex", "pct_change"},
}


def question_intent(question):
    for intent, pattern in INTENTS:
        if pattern.search(question):
            return intent
    return "other"


def asked_years(question):
    return [int(y) for y in YEAR_RE.findall(question)]


# ------------------------------------------------------------------------------- provenance graph
@dataclass
class Leaf:
    symbol: sp.Symbol
    value: float
    source: str            # "table", "text" or "ungrounded"
    ref: str               # "T[r,c]", "P:<value>" or "U:<value>" - the identity used for structural consensus
    years: set = field(default_factory=set)
    scale: int = 0         # log10 of the unit (6 = millions), 0 if unknown
    percent: bool = False
    row_label: str = ""
    var: str = ""


@dataclass
class Graph:
    expr: object = None            # sympy expression of `ans` over leaf symbols (None if not liftable)
    leaves: list = field(default_factory=list)
    shape: str = "unliftable"
    oriented: object = None        # (later_leaf, earlier_leaf) for difference / pct_change
    signature: str = ""
    converts_scale: bool = False   # the program multiplies or divides by a power of ten
    error: str = ""


class _Unliftable(Exception):
    pass


def _table_scale(table, texts):
    """log10 unit of the table from its header or caption text ('in millions' -> 6)."""
    head = " ".join(str(c) for row in table[:3] for c in row) + " " + " ".join(texts[-3:] + texts[:3])
    m = SCALE_HEADER.search(head)
    if not m:
        return 0
    word = next(g for g in m.groups() if g).lower()
    return 3 if "000" in word or word in ("$", "us$", "rs", "rs.", "₹") else SCALE_OF.get(word, 0)


class Lifter:
    def __init__(self, table, texts):
        self.index = TableIndex(table)
        self.texts = texts
        self.table_scale = _table_scale(table, texts) if table else 0
        self.text_numbers = [n for t in texts for n in find_numbers(t)]
        self.percent_cells = {(c.row, c.col) for c in self.index.cells
                              if "%" in str(table[c.row][c.col]) or "%" in c.header or "percent" in c.header.lower()}

    def leaf(self, value, var, leaves):
        tokens = content_tokens(re.sub(r"\d+", " ", var))
        var_years = {int(y) for y in YEAR_RE.findall(var.replace("_", " "))}
        hits = self.index.cells_with_value(value)
        if hits:
            def score(c):
                return (len(tokens & self.index.rows[c.row][1]), len(var_years & c.years), -c.row)
            c = max(hits, key=score)
            ref, src, years, label = f"T[{c.row},{c.col}]", "table", set(c.years), c.row_label
            scale, pct = (0 if (c.row, c.col) in self.percent_cells else self.table_scale), \
                (c.row, c.col) in self.percent_cells
        else:
            text = [n for n in self.text_numbers if _matches(value, n["value"])
                    or (n["scale"] in SCALE_WORDS and _matches(value, n["value"] * SCALE_WORDS[n["scale"]]))]
            if text:
                n = text[0]
                ref, src, years, label = f"P:{abs(n['value']):g}", "text", var_years, ""
                scale, pct = SCALE_OF.get(n["scale"], 0), n["percent"]
            else:
                ref, src, years, label, scale, pct = f"U:{abs(value):g}", "ungrounded", var_years, "", 0, False
        for existing in leaves:            # the same evidence used twice is one leaf
            if existing.ref == ref and math.isclose(existing.value, value, rel_tol=1e-9):
                return existing.symbol
        sym = sp.Symbol(f"L{len(leaves)}", positive=True)
        leaves.append(Leaf(sym, value, src, ref, years, scale, pct, label, var))
        return sym

    def lift(self, code):
        self._converts = False
        g = Graph()
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            g.error = f"syntax: {exc.msg}"
            return g
        env, leaves, last = {}, [], None
        try:
            for stmt in tree.body:
                if isinstance(stmt, (ast.Import, ast.ImportFrom)) or (
                        isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)):
                    continue
                if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                    target = stmt.targets[0]
                    if isinstance(target, ast.Name):
                        env[target.id] = self._expr(stmt.value, env, leaves, target.id, top=True)
                        last = target.id
                        continue
                    if isinstance(target, ast.Tuple) and isinstance(stmt.value, ast.Tuple) \
                            and len(target.elts) == len(stmt.value.elts):
                        for t, v in zip(target.elts, stmt.value.elts):
                            if not isinstance(t, ast.Name):
                                raise _Unliftable("tuple target")
                            env[t.id] = self._expr(v, env, leaves, t.id, top=True)
                            last = t.id
                        continue
                if isinstance(stmt, ast.AugAssign) and isinstance(stmt.target, ast.Name):
                    name = stmt.target.id
                    cur = env.get(name)
                    if cur is None:
                        raise _Unliftable("augassign before assign")
                    ctx = {ast.Mult: "mul", ast.Div: "div", ast.FloorDiv: "div", ast.Add: "add",
                           ast.Sub: "add"}.get(type(stmt.op), "other")
                    env[name] = self._binop(stmt.op, cur, self._expr(stmt.value, env, leaves, name, ctx=ctx))
                    last = name
                    continue
                raise _Unliftable(type(stmt).__name__)
        except (_Unliftable, TypeError, ValueError, ZeroDivisionError, RecursionError) as exc:
            g.error = str(exc) or type(exc).__name__
            return g
        ans = env.get("ans", env.get(last) if last else None)
        if ans is None or isinstance(ans, (str, list)) or not hasattr(ans, "free_symbols"):
            g.error = "no numeric ans"
            return g
        g.expr = ans
        used = ans.free_symbols
        g.leaves = [l for l in leaves if l.symbol in used]
        g.converts_scale = self._converts
        g.shape, g.oriented = classify_shape(ans, g.leaves)
        g.signature = signature(ans, g.leaves)
        return g

    _converts = False

    def _binop(self, op, a, b):
        if isinstance(a, list) or isinstance(b, list):
            raise _Unliftable("list arithmetic")
        if isinstance(op, ast.Add):
            return a + b
        if isinstance(op, ast.Sub):
            return a - b
        if isinstance(op, ast.Mult):
            return a * b
        if isinstance(op, (ast.Div, ast.FloorDiv)):
            if b == 0:
                raise ZeroDivisionError
            return a / b
        if isinstance(op, ast.Pow):
            return a ** b
        raise _Unliftable(type(op).__name__)

    def _expr(self, node, env, leaves, var, top=False, ctx="top"):
        """ctx tells a constant where it sits: 'top' (whole right side), 'mul' (factor), 'div' (divisor),
        'add' (term) or 'other'. Unit factors (x100, /1000) and small divisors (/3 for an average) are
        constants; a value that is added or subtracted, or divided by, and occurs in the report is evidence."""
        if isinstance(node, ast.Constant):
            v = node.value
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                if isinstance(v, str):
                    return v
                raise _Unliftable("constant")
            v = float(v)
            in_report = bool(self.index.cells_with_value(abs(v))) or \
                any(_matches(abs(v), n["value"]) for n in self.text_numbers)
            unit = abs(v) in (100, 1000, 1e5, 1e6, 1e7, 1e9, 0.01, 0.001)
            small = v.is_integer() and 0 <= abs(v) <= 12
            year = v.is_integer() and 1900 <= v <= 2100
            if ctx == "mul" and (unit or small):
                is_constant = True
            elif ctx == "div" and (small or (unit and not in_report)):
                is_constant = True
            elif ctx in ("add", "other", "top") and (unit or small or year) and not in_report:
                is_constant = True
            elif ctx == "add" and small and abs(v) <= 1:
                is_constant = True          # the "- 1" of a growth rate
            else:
                is_constant = False
            if is_constant:
                if unit and abs(v) != 100:
                    self._converts = True
                return sp.Rational(str(v)) if not v.is_integer() else sp.Integer(int(v))
            sym = self.leaf(abs(v), var, leaves)
            return -sym if v < 0 else sym
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise _Unliftable(f"unknown name {node.id}")
            return env[node.id]
        if isinstance(node, ast.UnaryOp):
            inner = self._expr(node.operand, env, leaves, var, top, ctx)
            if isinstance(node.op, ast.USub):
                return -inner
            if isinstance(node.op, ast.UAdd):
                return inner
            raise _Unliftable("unary")
        if isinstance(node, ast.BinOp):
            if isinstance(node.op, ast.Mult):
                lc = rc = "mul"
            elif isinstance(node.op, (ast.Div, ast.FloorDiv)):
                lc, rc = "other", "div"
            elif isinstance(node.op, (ast.Add, ast.Sub)):
                lc = rc = "add"
            else:
                lc = rc = "other"
            return self._binop(node.op, self._expr(node.left, env, leaves, var, ctx=lc),
                               self._expr(node.right, env, leaves, var, ctx=rc))
        if isinstance(node, (ast.List, ast.Tuple)):
            return [self._expr(e, env, leaves, var, ctx="add") for e in node.elts]
        if isinstance(node, ast.Call):
            fname = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else "")
            args = [self._expr(a, env, leaves, var, ctx=ctx) for a in node.args[:1]]
            if fname in ("round", "float", "int") and args:
                return args[0]
            if fname == "abs" and args:
                return sp.Abs(args[0])
            if fname == "sqrt" and args:
                return sp.sqrt(args[0])
            if fname in ("sum",) and args and isinstance(args[0], list):
                return sp.Add(*args[0])
            if fname == "len" and args and isinstance(args[0], list):
                return sp.Integer(len(args[0]))
            if fname in ("max", "min"):
                vals = [self._expr(a, env, leaves, var) for a in node.args]
                vals = vals[0] if len(vals) == 1 and isinstance(vals[0], list) else vals
                return (sp.Max if fname == "max" else sp.Min)(*vals)
            if fname == "pow" and len(node.args) == 2:
                return self._expr(node.args[0], env, leaves, var) ** self._expr(node.args[1], env, leaves, var)
            raise _Unliftable(f"call {fname}")
        raise _Unliftable(type(node).__name__)


# ------------------------------------------------------------------------------- formula shapes
_RNG = random.Random(0)
_DRAWS = [[_RNG.uniform(1.5, 9.5) for _ in range(12)] for _ in range(2)]


def _num(expr, syms, draw):
    try:
        return complex(expr.subs({s: draw[i] for i, s in enumerate(syms)}).evalf())
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _proportional(expr, tmpl, syms):
    """True if expr / tmpl is the same non-zero constant for two random draws of the leaves."""
    ratios = []
    for draw in _DRAWS:
        a, b = _num(expr, syms, draw), _num(tmpl, syms, draw)
        if a is None or b is None or abs(b) < 1e-12 or abs(a.imag) > 1e-9:
            return False
        ratios.append(a.real / b.real)
    return abs(ratios[0]) > 1e-12 and abs(ratios[0] - ratios[1]) <= 1e-7 * abs(ratios[0])


def classify_shape(expr, leaves):
    syms = [l.symbol for l in leaves][:12]
    m = len(syms)
    if m == 0:
        return "constant", None
    if m == 1:
        return "single", None
    if m == 2:
        a, b = syms
        for x, y in ((a, b), (b, a)):
            if _proportional(expr, (x - y) / y, syms):
                return "pct_change", (x, y)
        for x, y in ((a, b), (b, a)):
            if _proportional(expr, x / y, syms):
                return "ratio", None
        if _proportional(expr, a - b, syms):
            r = _num(expr, syms, _DRAWS[0]).real / (_DRAWS[0][0] - _DRAWS[0][1])
            return "difference", ((a, b) if r > 0 else (b, a))
        if _proportional(expr, a + b, syms):
            return _sum_or_average(expr, syms)
        for x, y in ((a, b), (b, a)):
            for n in range(1, 31):
                if _proportional(expr, (x / y) ** sp.Rational(1, n) - 1, syms):
                    return "cagr", (x, y)
        return "complex", None
    if _proportional(expr, sp.Add(*syms), syms):
        return _sum_or_average(expr, syms)
    if m <= 5:
        for k in range(1, m):
            for top in combinations(syms, k):
                rest = [s for s in syms if s not in top]
                if _proportional(expr, sp.Add(*top) - sp.Add(*rest), syms):
                    return "diff_of_sums", None
                if _proportional(expr, sp.Add(*top) / sp.Add(*rest), syms):
                    return "ratio_of_sums", None
    return "complex", None


def _sum_or_average(expr, syms):
    r = _num(expr, syms, _DRAWS[0]).real / sum(_DRAWS[0][:len(syms)])
    return ("average" if abs(r - 1 / len(syms)) < 1e-6 else "sum"), None


def signature(expr, leaves):
    """Canonical formula with leaves named by their evidence (cell / text value): equal signatures mean
    the same computation on the same evidence, regardless of how literals were typed."""
    names = {l.symbol: sp.Symbol(l.ref.replace("[", "_").replace(",", "_").replace("]", "").replace(":", "_")
                                 .replace(".", "p")) for l in leaves}
    try:
        return str(sp.nsimplify(sp.cancel(expr.subs(names)), rational=True))
    except Exception:   # sympy can fail on exotic expressions; fall back to the raw form
        return str(expr.subs(names))


# ------------------------------------------------------------------------------- typed checks
@dataclass
class Typing:
    intent: str
    shape: str
    liftable: bool
    type_ok: bool
    period_ok: float          # share of dated leaves whose period the question asks about (1 if n/a)
    orientation_ok: object    # True/False for changes with dated leaves, None otherwise
    mixed_scale: bool
    n_leaves: int
    n_table: int
    n_text: int
    n_ungrounded: int
    signature: str
    refs: list


def type_check(code, question, table, texts):
    lifter = Lifter(table, texts)
    g = lifter.lift(code)
    intent = question_intent(question)
    years = asked_years(question)
    if g.expr is None:
        return Typing(intent, "unliftable", False, intent in ("other", "yesno"), 1.0, None, False,
                      0, 0, 0, 0, "", [])
    type_ok = intent in ("other", "yesno") or g.shape == "constant" or g.shape in COMPATIBLE.get(intent, {g.shape})
    dated = [l for l in g.leaves if l.years]
    if years and dated:
        lo, hi = min(years), max(years)
        inside = [l for l in dated if any((lo <= y <= hi) if len(years) > 1 else (y in years or y == lo - 1)
                                          for y in l.years)]
        period_ok = len(inside) / len(dated)
    else:
        period_ok = 1.0
    orientation_ok = None
    if g.oriented and intent in ("pct_change", "difference"):
        later, earlier = (next(l for l in g.leaves if l.symbol == s) for s in g.oriented)
        if len(later.years) == 1 and len(earlier.years) == 1 and later.years != earlier.years:
            orientation_ok = max(later.years) > max(earlier.years)
    scales = {l.scale for l in g.leaves if l.scale and not l.percent and l.source in ("table", "text")}
    mixed = len(scales) > 1 and not g.converts_scale
    return Typing(intent, g.shape, True, type_ok, period_ok, orientation_ok, mixed, len(g.leaves),
                  sum(l.source == "table" for l in g.leaves), sum(l.source == "text" for l in g.leaves),
                  sum(l.source == "ungrounded" for l in g.leaves), g.signature,
                  [l.ref for l in g.leaves])


# ------------------------------------------------------------------------------- template completion
def synthesize(code, question, table, texts):
    """Neuro-symbolic template completion. The program tells us WHICH evidence (the table row its leaves
    come from); the question's typed intent and years tell us WHICH operation over WHICH periods. We
    instantiate the intent's formula over the exact cells of that row and return
    [(answer, description)]. No model call; returns [] when the evidence or intent is ambiguous."""
    intent = question_intent(question)
    years = sorted(set(asked_years(question)))
    if intent not in ("pct_change", "difference", "average", "sum") or len(years) < 2:
        return []
    lifter = Lifter(table, texts)
    g = lifter.lift(code)
    if g.expr is None:
        return []
    rows = {int(l.ref[2:].split(",")[0]) for l in g.leaves if l.source == "table"}
    if len(rows) != 1 or any(l.source != "table" for l in g.leaves):
        return []
    row = rows.pop()
    cells = [c for c in lifter.index.cells if c.row == row and len(c.years) == 1]
    by_year = {}
    for c in cells:
        by_year.setdefault(next(iter(c.years)), []).append(c)
    if any(len(v) > 1 for v in by_year.values()):     # several columns per year: ambiguous
        return []
    lo, hi = years[0], years[-1]
    label = lifter.index.rows[row][0]
    if intent in ("pct_change", "difference"):
        if len(years) != 2 or lo not in by_year or hi not in by_year:
            return []
        new, old = by_year[hi][0].value, by_year[lo][0].value
        if intent == "difference":
            return [(new - old, f"{label}: {hi} - {lo}")]
        if old == 0:
            return []
        return [((new - old) / old * 100, f"{label}: ({hi} - {lo}) / {lo} * 100")]
    span = [y for y in by_year if lo <= y <= hi]
    if len(span) < 2:
        return []
    vals = [by_year[y][0].value for y in sorted(span)]
    if intent == "average":
        return [(sum(vals) / len(vals), f"{label}: mean over {sorted(span)}")]
    return [(sum(vals), f"{label}: sum over {sorted(span)}")]
