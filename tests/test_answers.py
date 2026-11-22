from finreason.answers import extract_answer, find_numbers, parse_number, score, to_answer, token_f1


def test_parse_number_formats():
    assert parse_number("$ 5,735") == 5735
    assert parse_number("1,25,000.50") == 125000.5          # Indian digit grouping
    assert parse_number("(3.1)") == -3.1                     # accounting negative
    assert parse_number("-16 ( 16 )") == -16                 # FinQA negative cell
    assert parse_number("₹ 1,412.7 crore") == 1412.7
    assert parse_number("12.98%") == 12.98
    assert parse_number("no numbers here") is None


def test_find_numbers_scale_and_percent():
    numbers = find_numbers("Revenue rose 12.5% to Rs. 3.2 crore")
    assert numbers[0] == {"value": 12.5, "scale": "", "percent": True}
    assert numbers[1] == {"value": 3.2, "scale": "crore", "percent": False}


def test_extract_answer_variants():
    assert extract_answer("so the change is -935.\nAnswer: -21.88") == (-21.88, "answer_line")
    assert extract_answer("**Answer:** 34.04") == (34.04, "answer_line")
    assert extract_answer("Answer: $\\boxed{19.23}$") == (19.23, "answer_line")
    assert extract_answer("Answer: Yes, it increased") == ("yes", "answer_line")
    assert extract_answer("the result is 42") == (42, "last_number")
    assert extract_answer("I cannot tell.") == (None, None)


def test_to_answer():
    assert to_answer(True) == "yes"
    assert to_answer(3) == 3.0
    assert to_answer("12.5%") == 12.5
    assert to_answer("no") == "no"


def test_score_percent_forms():
    question = "what was the percentage change in revenue?"
    assert score(-21.88, -0.21882, question) == (True, True)       # FinQA stores fractions
    assert score(-0.2188, -0.21882, question)[0]
    assert score(17.7, 17.7, "what is the share", "percent") == (True, True)
    assert not score(-25.0, -0.21882, question)[0]


def test_score_tolerance_and_rounding():
    assert score(94.4, 94.0, "what is the net change")[0]          # within 0.5%
    assert not score(95.0, 94.0, "what is the net change")[0]      # 1.1% off
    assert score(95.0, 94.0, "what is the net change", rel_tol=0.02)[0]
    assert not score(26.3, 26.5589, "what was the effective tax rate")[0]
    assert score(-0.1972, -0.2, "percentage change", "percent")[0] # gold written with 1 decimal
    assert score("yes", "yes") == (True, True)
    assert score(None, 5.0) == (False, False)
    assert score(float("inf"), 5.0) == (False, False)


def test_token_f1():
    assert token_f1(34.04, 34.04) == 1.0
    assert token_f1(21.88, 0.2188, "what percentage") == 1.0
    assert token_f1(10.0, 12.0) == 0.0
