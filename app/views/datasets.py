"""Datasets: the three test sets, and a browser for our Indian annual-report set that shows each
question next to the PDF page its numbers come from."""
import pandas as pd
import streamlit as st

import core
import theme
from finreason.data import Example
from views.common import table_frame


def stats_table():
    path = core.RESULTS / "dataset_stats.md"
    if not path.exists():
        return None
    lines = [l for l in path.read_text().splitlines() if l.startswith("|") and not l.startswith("|:")]
    head = [h.strip() for h in lines[0].strip("|").split("|")]
    rows = [[c.strip() for c in l.strip("|").split("|")] for l in lines[1:]]
    return pd.DataFrame(rows, columns=head)


def render():
    theme.page_header("Data · three test sets", "The *datasets*",
                      "FinQA and TAT-QA (US company reports) plus our own set of 44 multi-step questions over four "
                      "Indian annual reports, with ₹ crore / lakh units and answers computed from formulas.",
                      core.status_pills())
    rows = core.indian_rows()
    verification = core.results_csv("indian_verification.csv")
    checked = int((verification["gold_matches"] == "yes").sum()) if verification is not None else 0
    theme.kpis([("FinQA [1]", "100", "test questions (seed 42) · 8,281 in the dataset", theme.SERIES[0]),
                ("TAT-QA [2]", "100", "arithmetic test questions · 16,552 in the dataset", theme.SERIES[0]),
                ("Indian set (ours)", str(len(rows)), "Titan · Asian Paints · Marico · Pidilite", theme.GOLD),
                ("Re-verified vs PDF", f"{checked}/{len(rows)}", "operands found on the cited page; gold recomputed",
                 theme.GOOD)])

    theme.section("How the Indian set was built", kicker="pipeline · scripts/build_indian_set.py")
    theme.cards([("1", "Locate statements", "Profit & loss, balance sheet and 10-year highlights pages in each "
                  "annual-report PDF.", ""),
                 ("2", "Transcribe rows", "Rows copied exactly as printed — every table cell must be found on its PDF "
                  "page (check 1).", ""),
                 ("3", "Write question + formula", "Each question has a Python formula over the printed numbers; no "
                  "answer is typed by hand.", ""),
                 ("4", "Gold = run the formula", "The sandbox computes the gold answer; every formula number must be "
                  "in the table or text (check 2).", "")])

    theme.section("Browse the Indian set", "Pick a question to see its table, formula and the actual PDF page.",
                  kicker="audit any gold answer")
    companies = sorted({r["company"] for r in rows})
    c1, c2 = st.columns([1, 3])
    company = c1.selectbox("Company", companies, key="ds_company")
    subset = [r for r in rows if r["company"] == company]
    idx = c2.selectbox("Question", range(len(subset)), key=f"ds_q_{company}",
                       format_func=lambda i: f"{subset[i]['uid']} — {subset[i]['question'][:120]}")
    r = subset[idx]
    chips = [theme.chip(f"gold {core.fmt_number(r['gold'])}", "gold"),
             theme.chip(f"{r['source']} · PDF page {r.get('page')}" + (f" (printed {r['printed_page']})"
                                                                     if r.get("printed_page") else "")),
             theme.chip(f"evidence: {r.get('evidence', 'table')}")]
    if verification is not None:
        v = verification[verification["uid"] == r["uid"]]
        if len(v):
            ok = v.iloc[0]["gold_matches"] == "yes" and v.iloc[0]["all_operands_on_cited_pages"] == "yes"
            chips.append(theme.chip("verified against the PDF" if ok else "verification failed", "good" if ok else "bad",
                                    "✓" if ok else "✕"))
    theme.question(r["uid"], r["question"], "".join(chips))
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        st.caption("Gold formula (run in the sandbox to produce the gold answer)")
        st.code(r["formula"], language="python")
        st.caption("Table given to the model")
        example = Example(uid=r["uid"], dataset="indian", question=r["question"], table=r["table"],
                          texts=r.get("texts", []), gold=r["gold"])
        st.dataframe(table_frame(example), width="stretch")
        if r.get("texts"):
            st.caption("Text")
            st.write("  \n".join(r["texts"]))
    with right:
        png = core.pdf_page_png(r["source"], int(r["page"])) if r.get("page") else None
        if png is None:
            st.info("The source PDF is not in data/indian/reports/, so the page cannot be shown.")
        else:
            st.image(png, caption=f"{r['source']} · PDF page {r['page']}", width="stretch")
    if png is not None:
        with st.expander("Enlarge the PDF page (full width)"):
            st.image(png, width="stretch")

    theme.section("Composition", "Sizes, reasoning steps and evidence source of every split we use.",
                  kicker="results/dataset_stats.md")
    stats = stats_table()
    if stats is not None:
        st.dataframe(stats, width="stretch", hide_index=True)
