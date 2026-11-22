"""Tests for the cell-level provenance audit and the TRACE vote (no model calls)."""
from finreason.provenance import TableIndex, audit_program, header_years, missing_ans_fix
from finreason.trace import pool_vote, program_weight

TABLE = [["in millions", "2007", "2008", "2009"],
         ["lease obligations ( a )", "$ 144", "$ 117", "$ 94"],
         ["purchase obligations ( bc )", "2329", "462", "362"],
         ["total", "$ 2473", "$ 579", "$ 456"]]
CONTEXT = "| in millions | 2007 | 2008 | 2009 |\n| lease obligations | 144 | 117 | 94 |\n" \
          "| purchase obligations | 2329 | 462 | 362 |\n| total | 2473 | 579 | 456 |"


def kinds(problems):
    return {p.kind for p in problems}


def test_correct_program_passes():
    code = "lease_obligations_2008 = 117\ntotal_2008 = 579\nans = lease_obligations_2008 / total_2008 * 100"
    assert audit_program(code, CONTEXT, "what percentage of total obligations is lease obligations in 2008?",
                         TABLE) == []


def test_wrong_year_column_is_caught():
    code = "lease_obligations_2008 = 144\ntotal_2008 = 579\nans = lease_obligations_2008 / total_2008"
    problems = audit_program(code, CONTEXT, "lease obligations as a share of total in 2008?", TABLE)
    assert "name_year" in kinds(problems)


def test_wrong_row_is_caught_with_the_right_value():
    code = "lease_obligations_2009 = 362\nans = lease_obligations_2009"
    problems = audit_program(code, CONTEXT, "what were lease obligations in 2009?", TABLE)
    assert "name_cell" in kinds(problems)
    assert "94" in next(p.message for p in problems if p.kind == "name_cell")


def test_question_span():
    code = "a = 2329\nb = 462\nans = (b - a) / a * 100"
    problems = audit_program(code, CONTEXT, "percentage change in purchase obligations from 2008 to 2009?",
                             TABLE)
    assert "question_span" in kinds(problems)


def test_repeated_and_spanning_headers():
    table = [["", "", "As of December 31, 2019", "", ""],
             ["", "Amortized Cost", "Gains", "Losses", "Fair Value"],
             ["U.S. government", "99,700", "—", "1,981", "97,719"],
             ["", "", "As of December 31, 2018", "", ""],
             ["", "Amortized Cost", "Gains", "Losses", "Fair Value"],
             ["U.S. government", "97,223", "416", "6,436", "91,203"]]
    index = TableIndex(table)
    years = {c.value: c.years for c in index.cells}
    assert years[416] == {2018} and years[1981] == {2019} and years[99700] == {2019}
    assert header_years("december 312017") == {2017}


def test_missing_ans_fix():
    assert missing_ans_fix("a = 1\ngrowth = a * 2").endswith("ans = growth\n")
    assert missing_ans_fix("ans = 3") is None


def test_pool_vote_prefers_program_value_and_drops_flagged():
    good = {"answer": 21.8826, "is_program": True, "problems": []}
    bad = {"answer": 5.0, "is_program": True, "problems": [("name_cell", 1.0, "x")]}
    cot = {"answer": 21.88, "is_program": False, "problems": []}
    weights = [program_weight(good), program_weight(bad), 1.0]
    chosen, best, total = pool_vote([bad, cot, good], [weights[1], weights[2], weights[0]])
    assert chosen is good and best == 2.0 and total == 2.0
