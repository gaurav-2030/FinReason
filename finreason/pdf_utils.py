"""Turn one page of a financial-report PDF into an Example (table + text) for the web app."""
import re

from .data import Example

NUMBER_TOKEN = r"\(?-?[₹$]?\d[\d,]*(?:\.\d+)?\)?%?|-"
TRAILING_NUMBERS = re.compile(rf"^(?P<label>.*?[A-Za-z)].*?)\s+(?P<nums>(?:(?:{NUMBER_TOKEN})\s*)+)$")


YEAR = re.compile(r"(?<![\d,.])(?:19|20)\d{2}(?:\s*-\s*\d{2})?(?![\d,.])")
DATE = re.compile(r"(?<![\d.])\d{1,2}\.\d{1,2}\.(?:19|20)\d{2}(?![\d.])")   # 31.03.2024


def _is_year(token):
    return bool(YEAR.fullmatch(token.strip("()")))


def _heading_token(token):
    """A number that belongs to a date heading: a year, or a day such as '31,' in 'March 31, 2016'."""
    return _is_year(token) or bool(re.fullmatch(r"\d{1,2},", token))


def year_header(lines):
    """The column years of a statement, read from its heading line, e.g.
    '31st March 2025 31st March 2024' -> ['2025', '2024'], '2023-24 2022-23' -> ['2023-24', '2022-23'].
    Only a heading line counts: two or more different years and no other numbers after its label
    (a line that repeats a year belongs to two statements printed side by side, so it is skipped)."""
    for line in lines:
        years = DATE.findall(line) or [y.replace(" ", "") for y in YEAR.findall(line)]
        match = TRAILING_NUMBERS.match(line.strip())
        trailing = match.group("nums").split() if match else []
        if len(years) >= 2 and len(set(years)) == len(years) and all(_heading_token(t) for t in trailing):
            return years
    return []


def lines_to_table(lines):
    """Statement pages are often not real PDF tables. Treat each line that ends in numbers as a
    row: 'Revenue from operations 19 54,842 47,114' -> ['Revenue from operations', '19', ...].
    When the page has a year heading, the columns are named by year and each row's last numbers
    are placed under the years (earlier numbers, such as note references, go to a Note column)."""
    years = year_header(lines)
    rows = []
    for line in lines:
        match = TRAILING_NUMBERS.match(line.strip())
        if match:
            nums = match.group("nums").split()
            if years and all(_heading_token(t) for t in nums):   # a heading line, not a data row
                continue
            rows.append([match.group("label").strip()] + nums)
    if not rows:
        return []
    if years:
        k = len(years)
        notes = any(len(r) - 1 > k for r in rows)
        out = [["Particulars"] + (["Note"] if notes else []) + years]
        for r in rows:
            label, nums = r[0], r[1:]
            values = ([""] * k + nums)[-k:]                 # right-aligned under the years
            extra = " ".join(nums[:-k]) if len(nums) > k else ""
            out.append([label] + ([extra] if notes else []) + values)
        return out
    width = max(len(r) for r in rows)
    header = ["Particulars"] + [f"column {i}" for i in range(1, width)]
    return [header] + [r + [""] * (width - len(r)) for r in rows]


def _quality(table):
    """Number of rows that have a text label and at least one number: a usable table row."""
    return sum(1 for row in table[1:] if re.search(r"[A-Za-z]", row[0] or "")
               and any(re.search(r"\d", cell or "") for cell in row[1:]))


def page_to_example(pdf_file, page_number, question):
    """Use pdfplumber's detected tables or a line-based table, whichever has more usable rows."""
    import pdfplumber
    with pdfplumber.open(pdf_file) as pdf:
        page = pdf.pages[page_number - 1]
        text = page.extract_text() or ""
        detected = [t for t in page.extract_tables() if t and len(t) > 1]
    lines = [line for line in text.splitlines() if line.strip()]
    candidates = [[[(cell or "").replace("\n", " ") for cell in row] for row in t] for t in detected]
    candidates.append(lines_to_table(lines))
    table = max(candidates, key=_quality)
    texts = [line for line in lines if not TRAILING_NUMBERS.match(line.strip())]
    return Example(uid=f"pdf-page-{page_number}", dataset="upload", question=question,
                   table=table, texts=texts, gold=None)
