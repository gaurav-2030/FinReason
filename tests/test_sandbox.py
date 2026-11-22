from finreason.sandbox import check_code, extract_code, run_code


def test_runs_simple_code_and_returns_trace():
    result = run_code("a = 3338\nb = 4273\nans = (a - b) / b * 100")
    assert result.ok
    assert round(result.ans, 2) == -21.88
    assert result.trace["a"] == 3338


def test_math_import_allowed():
    assert run_code("import math\nans = math.sqrt(16)").ans == 4.0


def test_blocks_dangerous_code():
    assert check_code("import os") is not None
    assert check_code("open('x.txt')") is not None
    assert check_code("ans = (1).__class__") is not None
    assert not run_code("import subprocess").ok


def test_reports_runtime_errors_and_missing_ans():
    assert "ZeroDivisionError" in run_code("ans = 1 / 0").error
    assert "did not set" in run_code("x = 1").error
    assert "SyntaxError" in run_code("ans = (").error


def test_timeout():
    result = run_code("while True:\n    pass", timeout=2)
    assert not result.ok


def test_extract_code_block():
    text = "Here is the code:\n```python\nans = 2 + 2\n```\nDone."
    assert extract_code(text) == "ans = 2 + 2"
