"""Tests for tables, prompts, perturbation, error taxonomy, statistics and retrieval."""
import json
import random

from finreason.answers import score
from finreason.data import Example, load_dataset
from finreason.errors import classify_error
from finreason.metrics import bootstrap_ci, holm, mcnemar
from finreason.perturb import perturb_dataset, perturb_example
from finreason.prompts import EXEMPLARS, build_messages
from finreason.retrieval import HybridRetriever, build_context, evidence_units, recall_at_k
from finreason.sandbox import extract_code, run_code
from finreason.strategies import Prediction
from finreason.tables import serialize

TABLE = [["in millions", "2014", "2013"], ["sales", "$ 5720", "$ 6205"], ["profit", "-16 ( 16 )", "271"]]


def test_all_table_formats():
    assert serialize(TABLE, "markdown").splitlines()[0] == "| in millions | 2014 | 2013 |"
    assert json.loads(serialize(TABLE, "json"))[0] == {"in millions": "sales", "2014": "$ 5720", "2013": "$ 6205"}
    assert "<td>$ 5720</td>" in serialize(TABLE, "html")
    assert serialize(TABLE, "text").splitlines()[0] == "sales: 2014 = $ 5720; 2013 = $ 6205."


def test_exemplars_are_correct():
    """Every hand-written worked example must itself give the right answer."""
    for shot in EXEMPLARS:
        ex = shot["example"]
        assert score(run_code(extract_code(shot["pot"])).ans, ex.gold, ex.question)[0]
        assert shot["cot"].strip().endswith(shot["decomp"].strip().splitlines()[-1])


def test_fewshot_messages_structure():
    messages = build_messages("cot", "Table: ...", "what is x?", fewshot=True)
    assert [m["role"] for m in messages] == ["system"] + ["user", "assistant"] * 3 + ["user"]


def test_perturbation_recomputes_gold():
    ex = Example(uid="x", dataset="finqa", question="what is the change?",
                 table=[["", "2015", "2014"], ["net revenue", "$ 5829", "$ 5735"]], texts=[],
                 gold=94.0, gold_program="subtract(5829, 5735)")
    p = perturb_example(ex, random.Random(0))
    new_2015, new_2014 = (float(c.replace("$ ", "")) for c in p.table[1][1:])
    assert p.gold == new_2015 - new_2014
    assert p.gold != 94.0


def test_perturbation_covers_most_of_finqa():
    examples = load_dataset("finqa", "test", n=100)
    assert len(perturb_dataset(examples)) >= 50


def test_error_categories():
    ex = Example(uid="x", dataset="finqa", question="what is the change?", table=TABLE, texts=[],
                 gold=94.0, gold_program="subtract(5829, 5735)")
    assert classify_error(Prediction(answer=94.0), ex, True) is None
    assert classify_error(Prediction(answer=-94.0, output="5829 5735"), ex, False) == "sign_error"
    assert classify_error(Prediction(answer=94000.0, output="x"), ex, False) == "scale_error"
    assert classify_error(Prediction(answer=97.0, output="x"), ex, False) == "rounding_near_miss"
    assert classify_error(Prediction(answer=50.0, output="5829 - 5779 = 50"), ex, False) == "evidence_error"
    assert classify_error(Prediction(answer=50.0, output="5829 and 5735 so 50"), ex, False) == "reasoning_error"
    assert classify_error(Prediction(answer=None, code="ans ="), ex, False) == "execution_error"


def test_statistics():
    a = [1] * 30 + [0] * 10 + [1] * 5
    b = [1] * 30 + [1] * 10 + [0] * 5
    assert mcnemar(a, b)[:2] == (5, 10)
    lo, hi = bootstrap_ci([1, 0] * 50)
    assert lo < 0.5 < hi
    assert holm([0.01, 0.04, 0.03]) == [0.03, 0.06, 0.06]


def test_hybrid_retrieval_finds_gold_rows():
    ex = load_dataset("finqa", "test")[0]
    retrieved = HybridRetriever().retrieve(ex.question, evidence_units(ex), k=5)
    assert recall_at_k([u for u, _, _ in retrieved], ex.gold_facts) == 1.0
    context, _ = build_context(ex, mode="retrieved", retriever=HybridRetriever(), k=5)
    assert context.startswith("Table:")


def test_indian_set_is_consistent():
    """Every Indian question loads, and its gold answer equals its formula."""
    examples = load_dataset("indian")
    assert len(examples) == 44
    for ex in examples:
        result = run_code(f"ans = {ex.gold_program}")
        if isinstance(ex.gold, str):
            assert result.ans == ex.gold
        else:
            assert abs(result.ans - ex.gold) < 1e-3


def test_lines_to_table():
    from finreason.pdf_utils import lines_to_table
    table = lines_to_table(["Revenue from operations 19 54,842 47,114", "Statement of profit and loss",
                            "Changes in inventories (6,537) (2,149)"])
    assert table[1] == ["Revenue from operations", "19", "54,842", "47,114"]
    assert table[2][:3] == ["Changes in inventories", "(6,537)", "(2,149)"]


def test_grounding_verification():
    from finreason.verify import code_literals, grounding_check
    context = "Table:\n| item | 2015 | 2014 |\n|---|---|---|\n| net revenue | $ 5829 | $ 5735 |\nText:\nsales were $ 1.1 billion"
    assert sorted(code_literals("a = 5829\nans = (a - 5735) / 5735 * 100")) == [100, 5735, 5735, 5829]
    assert grounding_check("ans = (5829 - 5735) / 5735 * 100", context) == (True, [])
    assert grounding_check("ans = 1.1 * 1000 / 5829", context)[0]          # unit conversion is fine
    assert grounding_check("ans = (5829 - 5753) / 5753", context) == (False, [5753, 5753])  # misread


def test_vpsc2_question_checks():
    """VPSC v2: a plain 'change' must not divide, and a program must stay inside the asked years."""
    from finreason.verify import operation_check, verify_program, year_check
    q = "What was the change in Distributions payable between 2018 and 2019?"
    assert operation_check(q, "a = 5978\nb = 10066\nans = (a - b) / b * 100")
    assert operation_check(q, "a = 5978\nb = 10066\nans = a - b") is None
    assert operation_check("What was the percentage change in sales?", "ans = (5 - 4) / 4 * 100") is None
    assert operation_check("What was the average change in sales?", "ans = (5 - 4) / 2") is None
    assert year_check("What was the change in cash between 2017 and 2018?", "cash_2019 = 1\ncash_2018 = 2\nans = cash_2019 - cash_2018")
    assert year_check("What was the change in cash between 2017 and 2018?", "cash_2018 = 1  # 2019 column\nans = cash_2018") is None
    assert year_check("what was the growth rate in 2012?", "a_2011 = 1\nans = a_2011") is None   # one year named
    assert year_check("did the company 2019s expense rise from 2004 to 2005?", "x_2004 = 1\nans = x_2004") is None
    context = "Table:\n| item | 2019 | 2018 |\n|---|---|---|\n| payable | 5978 | 10066 |"
    assert verify_program("ans = 5978 - 10066", context, q) == []
    assert len(verify_program("ans = (5978 - 10060) / 10060", context, q)) == 2   # ungrounded + divides


def test_vpsc2_vote():
    """Verified programs and CoT answers pool within 1%; the pooled value comes from a program."""
    from finreason.strategies import verified_hybrid_vote
    cands = [{"answer": -40.6, "weight": 0.0, "is_program": True},     # rejected by the verifier
             {"answer": -4088.0, "weight": 1.0, "is_program": True},
             {"answer": 21.8826, "weight": 1.0, "is_program": True},
             {"answer": 21.88, "weight": 1.0, "is_program": False},
             {"answer": -4088.0, "weight": 1.0, "is_program": False}]
    chosen, pools = verified_hybrid_vote(cands)
    assert chosen["answer"] == -4088.0 and len(pools) == 2           # tie -> pool seen first
    chosen, _ = verified_hybrid_vote(cands[:1] + cands[2:4])
    assert chosen["answer"] == 21.8826                                 # exact program value wins
    assert verified_hybrid_vote(cands[:1]) == (None, [])


def test_pdf_page_to_example():
    """The app's PDF input: one statement page becomes a table the model can read."""
    from finreason.config import DATA_INDIAN
    from finreason.pdf_utils import page_to_example
    pdf = DATA_INDIAN / "reports" / "titan_ar_2024-25.pdf"
    if not pdf.exists():
        import pytest
        pytest.skip("Indian report PDFs are not present")
    ex = page_to_example(pdf, 275, "What was the revenue growth?")
    labels = [row[0].lower() for row in ex.table]
    assert any("revenue from operations" in label for label in labels)
    # the year heading names the columns, and values sit under the right year
    assert ex.table[0] == ["Particulars", "Note", "2025", "2024"]
    assert ex.table[1] == ["I. Revenue from operations", "19", "54,842", "47,114"]
    total = next(row for row in ex.table if row[0].startswith("III. Total income"))
    assert total[2:] == ["55,335", "47,624"]   # a row without a note is right-aligned
    asian = page_to_example(DATA_INDIAN / "reports" / "asianpaints_fs_2023-24.pdf", 11, "q")
    assert asian.table[0][-2:] == ["31.03.2024", "31.03.2023"]   # date headings


def test_llm_rejects_empty_server_reply(monkeypatch):
    """An empty reply that processed no tokens (a server failure) is retried and never cached."""
    import pytest
    from finreason import llm as llm_module
    monkeypatch.setattr(llm_module.time, "sleep", lambda s: None)
    client = llm_module.LLM("ollama:test-model", use_cache=False)
    monkeypatch.setattr(client, "_call", lambda *a: ("", 0, 0))
    with pytest.raises(RuntimeError):
        client.chat([{"role": "user", "content": "hi"}])
