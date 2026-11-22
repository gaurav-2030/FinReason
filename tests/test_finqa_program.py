import pytest

from finreason.data import count_operations, load_dataset
from finreason.finqa_program import execute, numeric_arguments, parse_program


def test_parse_and_execute():
    program = "subtract(5829, 5735), divide(#0, 5735)"
    assert parse_program(program)[1] == ("divide", ["#0", "5735"])
    assert execute(program) == pytest.approx(94 / 5735)


def test_constants_percent_and_greater():
    assert execute("multiply(1.1, const_1000)") == pytest.approx(1100)
    assert execute("multiply(8.75%, const_100)") == pytest.approx(8.75)
    assert execute("greater(5, 3)") == "yes"


def test_table_operations():
    table = [["", "2019", "2018"], ["sales", "$ 10", "$ 30"]]
    assert execute("table_average(sales, none)", table) == 20
    assert execute("table_max(sales, none)", table) == 30


def test_numeric_arguments():
    assert numeric_arguments("subtract(5829, 5735), divide(#0, const_100)") == ["5829", "5735"]


def test_reproduces_every_finqa_test_answer():
    for ex in load_dataset("finqa", "test"):
        result = execute(ex.gold_program, ex.table)
        if isinstance(ex.gold, str):
            assert result == ex.gold
        else:
            assert result == pytest.approx(ex.gold, rel=1e-3, abs=1e-3)


def test_count_operations():
    assert count_operations("6,332-6,059") == 1
    assert count_operations("((17,718-17,236)/17,236) * 100") == 3
    assert count_operations("-5 + 3") == 1
