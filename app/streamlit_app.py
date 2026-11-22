"""FinReason web app: ask numerical questions about financial reports and audit every answer
(evidence, code, votes, grounding, prompt), compare prompting strategies, and explore every
experiment result, optimization artifact, robustness test, error and dataset.

    bash scripts/start_app.sh          (or: .venv/bin/python -m streamlit run app/streamlit_app.py)
Pages live in app/views/, the look in app/theme.py and .streamlit/config.toml.
"""
import sys
from pathlib import Path

import streamlit as st

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP.parent))
sys.path.insert(0, str(APP))

import theme  # noqa: E402
from views import (ask, compare, datasets, errors, method, optimization, overview, results,  # noqa: E402
                   robustness)

st.set_page_config(page_title="FinReason", page_icon=str(APP / "assets" / "logo_icon.svg"), layout="wide",
                   initial_sidebar_state="collapsed")
theme.inject_css()
st.logo(str(APP / "assets" / "logo.svg"), size="large", icon_image=str(APP / "assets" / "logo_icon.svg"))

pages = st.navigation([
    st.Page(overview.render, title="Overview", icon=":material/home:", default=True),
    st.Page(ask.render, title="Ask", icon=":material/bolt:", url_path="ask"),
    st.Page(compare.render, title="Compare", icon=":material/compare_arrows:", url_path="compare"),
    st.Page(results.render, title="Results", icon=":material/insights:", url_path="results"),
    st.Page(optimization.render, title="Optimization", icon=":material/tune:", url_path="optimization"),
    st.Page(robustness.render, title="Robustness", icon=":material/shield:", url_path="robustness"),
    st.Page(errors.render, title="Errors", icon=":material/troubleshoot:", url_path="errors"),
    st.Page(datasets.render, title="Data", icon=":material/table_view:", url_path="data"),
    st.Page(method.render, title="Method", icon=":material/account_tree:", url_path="method"),
], position="top")
pages.run()
