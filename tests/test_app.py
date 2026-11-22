"""Headless tests of the web app: every page renders without an exception, and the Ask page runs the
full pipeline (answered from the response cache when the experiments have run)."""
import urllib.request

import pytest
from streamlit.testing.v1 import AppTest

from finreason.config import OLLAMA_URL, ROOT

PAGES = ["overview", "ask", "compare", "results", "optimization", "robustness", "errors", "datasets", "method"]
SCRIPT = f"""
import sys
sys.path.insert(0, {str(ROOT)!r}); sys.path.insert(0, {str(ROOT / 'app')!r})
import theme
from views import {{page}}
theme.inject_css()
{{page}}.render()
"""


def page_app(page):
    return AppTest.from_string(SCRIPT.format(page=page), default_timeout=180)


def ollama_online():
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=1):
            return True
    except OSError:
        return False


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = page_app(page).run()
    assert not at.exception, [e.value for e in at.exception]


def test_results_every_dataset_renders():
    at = page_app("results").run()
    for dataset in ["finqa", "tatqa", "indian"]:
        at.segmented_control(key="res_dataset").set_value(dataset).run()
        assert not at.exception, (dataset, [e.value for e in at.exception])


def test_ask_runs_pipeline():
    if not ollama_online():
        pytest.skip("Ollama is not running")
    at = page_app("ask").run()
    at.selectbox(key="ask_strategy").set_value("pot_fs").run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert "ask_result" in at.session_state
    result = at.session_state["ask_result"]
    assert result["pred"].answer is not None


def test_ask_with_retrieval_and_json_table():
    if not ollama_online():
        pytest.skip("Ollama is not running")
    at = page_app("ask").run()
    at.segmented_control(key="ask_mode").set_value("retrieved").run()
    at.selectbox(key="ask_fmt").set_value("json").run()
    at.selectbox(key="ask_strategy").set_value("cot_zs").run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    result = at.session_state["ask_result"]
    assert result["retrieved"] and len(result["retrieved"]) == 5


def test_compare_runs_strategies():
    if not ollama_online():
        pytest.skip("Ollama is not running")
    at = page_app("compare").run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    rows = at.session_state["cmp_result"]["rows"]
    assert len(rows) == 4 and all(r["answer"] != "error" for r in rows)


def test_paste_table_input():
    at = page_app("ask").run()
    at.segmented_control(key="ask_source").set_value("paste").run()
    assert not at.exception
    assert not at.button[0].disabled


def test_data_page_every_company():
    at = page_app("datasets").run()
    for company in at.selectbox(key="ds_company").options:   # plain strings, so options are the values
        at.selectbox(key="ds_company").set_value(company).run()
        assert not at.exception, (company, [e.value for e in at.exception])


@pytest.mark.parametrize("strategy", ["direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"])
def test_ask_every_strategy(strategy):
    """Every hand-written strategy runs end to end in the app (cached answers once the experiments ran)."""
    if not ollama_online():
        pytest.skip("Ollama is not running")
    at = page_app("ask").run()
    at.selectbox(key="ask_strategy").set_value(strategy).run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    assert at.session_state["ask_result"]["strategy"] == strategy


def test_errors_page_every_selection():
    at = page_app("errors").run()
    for d in range(len(at.selectbox(key="err_dataset").options)):
        at.selectbox(key="err_dataset").select_index(d).run()
        for m in range(len(at.selectbox(key="err_model").options)):
            at.selectbox(key="err_model").select_index(m).run()
            for s in range(len(at.selectbox(key="err_strategy").options)):
                at.selectbox(key="err_strategy").select_index(s).run()
                assert not at.exception, (d, m, s, [e.value for e in at.exception])


def test_optimization_page_both_models():
    at = page_app("optimization").run()
    for model in ["ollama:qwen3:1.7b", "ollama:qwen3:8b"]:
        at.segmented_control(key="opt_model").set_value(model).run()
        assert not at.exception, (model, [e.value for e in at.exception])


def test_ask_optimized_prompt():
    """An optimized DSPy program runs in the app with the model it was compiled for."""
    if not ollama_online():
        pytest.skip("Ollama is not running")
    at = page_app("ask").run()
    options = at.selectbox(key="ask_strategy").options
    dspy = [i for i, o in enumerate(options) if o.startswith("DSPy")]
    if not dspy:
        pytest.skip("no optimized DSPy program yet")
    at.selectbox(key="ask_model").set_value("ollama:qwen3:8b").run()
    at.selectbox(key="ask_strategy").select_index(dspy[0]).run()
    at.button[0].click().run()
    assert not at.exception, [e.value for e in at.exception]
    result = at.session_state["ask_result"]
    assert result["model"] == "ollama:qwen3:1.7b" and result["pred"].n_calls >= 1
