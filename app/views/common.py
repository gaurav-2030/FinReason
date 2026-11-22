"""Pieces shared by the Ask and Compare pages: inference settings, the three input sources,
evidence highlighting and a live timer for model calls."""
import csv
import io
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import streamlit as st

import core
import theme
from finreason.answers import find_numbers
from finreason.data import Example
from finreason.pdf_utils import page_to_example
from finreason.verify import CONSTANTS

PASTE_TABLE = ("Particulars (₹ in crore),FY2025,FY2024\n"
               "Revenue from operations,\"54,842\",\"47,114\"\n"
               "Other income,493,406\n"
               "Profit before tax,\"4,481\",\"4,607\"\n"
               "Changes in inventories,\"(6,537)\",\"(2,149)\"")


def settings(key):
    """Model, table format and context controls in one row; returns (model, fmt, mode, k)."""
    c1, c2, c3, c4 = st.columns([1.1, 1, 1.1, 1], vertical_alignment="bottom")
    model = c1.selectbox("Model", core.model_options(), format_func=core.model_name, key=f"{key}_model",
                         help="Qwen3-1.7B answers in seconds; Qwen3-8B is more accurate but several times slower.")
    fmt = c2.selectbox("Table format", ["markdown", "json", "html", "text"], key=f"{key}_fmt",
                       help="How the table is written into the prompt (one of our ablations).")
    mode = c3.segmented_control("Context", ["full", "retrieved"], default="full", required=True, key=f"{key}_mode",
                                format_func=lambda v: {"full": "Full page", "retrieved": "Top-k retrieved"}.get(v, v),
                                help="Full page, or only the rows/sentences found by hybrid BM25 + MiniLM retrieval.")
    k = c4.slider("Evidence units (k)", 2, 12, 5, key=f"{key}_k", disabled=mode != "retrieved")
    return model, fmt, mode, k


def choose_example(key):
    """Three input sources: a benchmark question, a pasted table, or one page of an uploaded PDF."""
    source = st.segmented_control(
        "Input", ["dataset", "paste", "pdf"], default="dataset", required=True, key=f"{key}_source",
        format_func=lambda v: {"dataset": "Benchmark question", "paste": "Paste a table",
                               "pdf": "Upload a PDF page"}.get(v, v))
    if source == "dataset":
        left, right = st.columns([1, 3.2])
        dataset = left.selectbox("Dataset", core.DATASETS, index=2, format_func=core.dataset_label,
                                 key=f"{key}_dataset")
        examples = core.get_examples(dataset)
        i = right.selectbox("Question", range(len(examples)), key=f"{key}_question_{dataset}",
                            format_func=lambda i: f"{examples[i].uid} — {examples[i].question[:130]}")
        return examples[i]
    if source == "paste":
        left, right = st.columns([1.5, 1])
        table_csv = left.text_area("Table as CSV (first row is the header)", PASTE_TABLE, height=170,
                                   key=f"{key}_csv")
        text = right.text_area("Text around the table (one sentence per line)", "All amounts are in ₹ crore.",
                               height=170, key=f"{key}_text")
        question = st.text_input("Question", "What was the profit before tax margin in FY2025, in percent?",
                                 key=f"{key}_q")
        table = [row for row in csv.reader(io.StringIO(table_csv)) if any(c.strip() for c in row)]
        if not question.strip() or len(table) < 2:
            st.info("Enter a table with a header row and at least one data row, and a question.")
            return None
        return Example(uid="pasted table", dataset="pasted", question=question.strip(), table=table,
                       texts=[t for t in text.splitlines() if t.strip()], gold=None)
    left, mid, right = st.columns([2, .8, 3], vertical_alignment="bottom")
    pdf = left.file_uploader("Annual-report PDF", type="pdf", key=f"{key}_pdf")
    page = mid.number_input("Page", min_value=1, value=1, key=f"{key}_page",
                            help="The page number as shown by your PDF viewer (not the printed number).")
    question = right.text_input("Question", key=f"{key}_pdfq", placeholder="e.g. What was the revenue growth in FY25?")
    if pdf is None or not question.strip():
        st.info("Upload a PDF, pick the page that holds the statement, and type a question.")
        return None
    try:
        example = page_to_example(pdf, int(page), question.strip())
    except IndexError:
        st.error(f"The PDF has fewer than {page} pages.")
        return None
    except Exception as exc:   # damaged or encrypted PDFs
        st.error(f"Could not read this PDF page: {exc}")
        return None
    if not example.table:
        st.warning("No table rows with numbers were found on this page; the model will see only its text.")
    return example


def table_frame(example):
    header = [str(c).strip() or f"column {j}" for j, c in enumerate(example.table[0])]
    seen = {}
    unique = []
    for h in header:   # duplicate column names are not allowed in a DataFrame display
        seen[h] = seen.get(h, 0) + 1
        unique.append(h if seen[h] == 1 else f"{h} ({seen[h]})")
    width = len(unique)
    rows = [[str(c) for c in r][:width] + [""] * (width - len(r)) for r in example.table[1:]]
    df = pd.DataFrame(rows, columns=unique)
    df.index = range(1, len(df) + 1)
    return df


def evidence_rows(example, pred, retrieved):
    """Rows whose numbers the model used (amber) and rows chosen by retrieval (blue)."""
    used = {abs(n["value"]) for n in find_numbers(pred.code or pred.output)} - CONSTANTS
    used_rows, retrieved_rows = set(), set()
    for i, row in enumerate(example.table[1:], start=1):
        cells = {abs(n["value"]) for cell in row[1:] for n in find_numbers(str(cell))}
        if cells & used:
            used_rows.add(i)
    for uid, _, _ in retrieved or []:
        if uid.startswith("table_"):
            retrieved_rows.add(int(uid.split("_")[1]))
    return used_rows, retrieved_rows


def styled_table(example, used_rows=(), retrieved_rows=()):
    df = table_frame(example)

    def colour(row):
        if row.name in used_rows:
            return ["background-color: rgba(214,180,106,.20); color: #f3dfae; font-weight: 600"] * len(row)
        if row.name in retrieved_rows:
            return ["background-color: rgba(57,135,229,.16); color: #b9d4f6"] * len(row)
        return [""] * len(row)
    return df.style.apply(colour, axis=1)


def run_with_timer(fn, label, sub):
    """Run fn in a worker thread and show a live elapsed-time counter until it finishes."""
    box = st.empty()
    start = time.perf_counter()
    with ThreadPoolExecutor(1) as pool:
        future = pool.submit(fn)
        while not future.done():
            box.markdown(theme.timer(label, sub, time.perf_counter() - start), unsafe_allow_html=True)
            time.sleep(0.2)
    box.empty()
    return future.result(), time.perf_counter() - start


def offline_notice():
    if not core.ollama_online():
        st.error("Ollama is not reachable, so new questions cannot be answered. Start it with "
                 "`bash scripts/start_app.sh` (or `ollama serve`). Results pages still work.", icon="⚠️")
        return True
    return False
