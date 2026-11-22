"""Tests for provenance-graph verification (lifting, shapes, typing, template completion)."""
from finreason.pgv import Lifter, question_intent, synthesize, type_check

TABLE = [["in millions", "2017", "2018", "2019"],
         ["revenue", "$ 100", "$ 120", "$ 150"],
         ["operating income", "20", "30", "45"]]


def test_lifting_and_signature_ignore_how_literals_are_typed():
    a = Lifter(TABLE, []).lift("r18 = 120\nr17 = 100\nans = (r18 - r17) / r17 * 100")
    b = Lifter(TABLE, []).lift("ans = (120 / 100 - 1) * 100")
    assert a.shape == b.shape == "pct_change"
    assert a.signature == b.signature


def test_shapes():
    lift = lambda code: Lifter(TABLE, []).lift(code).shape
    assert lift("ans = 150 - 120") == "difference"
    assert lift("ans = 30 / 120 * 100") == "ratio"
    assert lift("ans = (100 + 120 + 150) / 3") == "average"
    assert lift("ans = 100 + 120 + 150") == "sum"
    assert lift("ans = 150") == "single"


def test_intents():
    assert question_intent("what was the percentage change in revenue from 2018 to 2019?") == "pct_change"
    assert question_intent("what was the change in revenue from 2018 to 2019?") == "difference"
    assert question_intent("what is the average revenue from 2017 to 2019?") == "average"
    assert question_intent("what percentage of revenue was operating income in 2019?") == "share"
    assert question_intent("did revenue increase from 2018 to 2019?") == "yesno"
    assert question_intent("by how many percentage points did the margin change?") == "difference"


def test_type_period_and_orientation():
    q = "what was the percentage change in revenue from 2018 to 2019?"
    good = type_check("ans = (150 - 120) / 120 * 100", q, TABLE, [])
    assert good.type_ok and good.period_ok == 1 and good.orientation_ok is True
    backwards = type_check("ans = (120 - 150) / 150 * 100", q, TABLE, [])
    assert backwards.orientation_ok is False
    wrong_op = type_check("ans = 150 - 120", q, TABLE, [])
    assert not wrong_op.type_ok
    wrong_year = type_check("ans = (120 - 100) / 100 * 100", q, TABLE, [])
    assert wrong_year.period_ok < 1


def test_mixed_scale():
    texts = ["international sales were $ 1.1 billion in 2019 ."]
    q = "what percentage of revenue were international sales in 2019?"
    assert type_check("ans = 1.1 / 150 * 100", q, TABLE, texts).mixed_scale
    assert not type_check("ans = 1.1 * 1000 / 150 * 100", q, TABLE, texts).mixed_scale


def test_template_completion_fixes_year_and_operation():
    q = "what was the percentage change in revenue from 2018 to 2019?"
    # the program read the right row but the wrong years and the wrong operation
    out = synthesize("ans = 120 - 100", q, TABLE, [])
    assert len(out) == 1 and abs(out[0][0] - 25.0) < 1e-9
    assert synthesize("ans = 120 - 100", "what was revenue in 2019?", TABLE, []) == []
