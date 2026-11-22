"""Build data/indian/indian_set.jsonl: questions over real Indian annual reports.

Every table below is transcribed from the company's published PDF (file and page recorded).
Gold answers are NOT typed by hand: each question has a formula that is executed in the
sandbox, and the script checks that every number in the formula appears in the table or text.
All questions start with verified=False; a team member sets it to True after checking the
numbers against the PDF page listed in data/indian/verification_checklist.csv.

    python scripts/build_indian_set.py
"""
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader

from finreason.answers import find_numbers, parse_number
from finreason.config import DATA_INDIAN
from finreason.sandbox import run_code

# Numbers allowed in formulas without appearing in the report: unit conversions
# (1 crore = 100 lakh = 10 million = 0.01 billion), percentages, averages and year counts.
FORMULA_CONSTANTS = {1, 2, 5, 9, 10, 100}

TITAN_PL = {
    "source": "titan_ar_2024-25.pdf", "pdf_page": 275, "printed_page": 273,
    "company": "Titan Company Limited",
    "title": "Standalone statement of profit and loss of Titan Company Limited for the year ended 31st March 2025.",
    "header": ["Particulars (₹ in crore)", "Year ended 31st March 2025", "Year ended 31st March 2024"],
    "rows": [
        ["Revenue from operations", "54,842", "47,114"],
        ["Other income", "493", "510"],
        ["Total income", "55,335", "47,624"],
        ["Cost of raw materials and components consumed", "43,905", "33,556"],
        ["Purchase of stock-in-trade", "6,372", "5,535"],
        ["Changes in inventories of finished goods, stock-in-trade and work-in-progress", "(6,537)", "(2,149)"],
        ["Employee benefits expense", "1,717", "1,503"],
        ["Finance costs", "767", "480"],
        ["Depreciation and amortisation expense", "537", "447"],
        ["Other expenses", "4,093", "3,645"],
        ["Total expenses", "50,854", "43,017"],
        ["Profit before tax", "4,481", "4,607"],
        ["Current tax", "1,117", "1,072"],
        ["Deferred tax", "29", "(9)"],
        ["Total tax expense", "1,146", "1,063"],
        ["Profit for the year", "3,335", "3,544"],
        ["Basic earnings per equity share of ₹ 1 (₹)", "37.60", "39.94"],
        ["Diluted earnings per equity share of ₹ 1 (₹)", "37.58", "39.92"],
    ],
}

TITAN_BS = {
    "source": "titan_ar_2024-25.pdf", "pdf_page": 274, "printed_page": 272,
    "company": "Titan Company Limited",
    "title": "Standalone balance sheet of Titan Company Limited as at 31st March 2025.",
    "header": ["Particulars (₹ in crore)", "As at 31st March 2025", "As at 31st March 2024"],
    "rows": [
        ["Property, plant and equipment", "1,474", "1,380"],
        ["Right-of-use assets", "1,449", "1,225"],
        ["Investments (non-current)", "6,386", "6,178"],
        ["Total non-current assets", "10,631", "10,169"],
        ["Inventories", "24,517", "16,874"],
        ["Investments (current)", "1,337", "1,635"],
        ["Trade receivables", "984", "937"],
        ["Cash and cash equivalents", "243", "272"],
        ["Bank balances other than cash and cash equivalents", "889", "533"],
        ["Other current assets", "1,625", "1,290"],
        ["Total current assets", "30,444", "22,693"],
        ["Total assets", "41,075", "32,862"],
        ["Equity share capital", "89", "89"],
        ["Other equity", "16,722", "14,368"],
        ["Total equity", "16,811", "14,457"],
        ["Borrowings (non-current)", "420", "3,139"],
        ["Total non-current liabilities", "2,619", "5,043"],
        ["Borrowings (current)", "7,483", "2,670"],
        ["Gold on loan", "7,043", "4,938"],
        ["Trade payables - micro and small enterprises", "158", "166"],
        ["Trade payables - other creditors", "1,314", "777"],
        ["Total current liabilities", "21,645", "13,362"],
        ["Total equity and liabilities", "41,075", "32,862"],
    ],
}

ASIAN_PL = {
    "source": "asianpaints_fs_2023-24.pdf", "pdf_page": 12, "printed_page": 321,
    "company": "Asian Paints Limited",
    "title": "Standalone statement of profit and loss of Asian Paints Limited for the year ended 31st March, 2024.",
    "header": ["Particulars (₹ in crores)", "Year 2023-24", "Year 2022-23"],
    "rows": [
        ["Revenue from sale of products", "30,635.29", "29,883.09"],
        ["Revenue from sale of services", "92.42", "70.03"],
        ["Other operating revenue", "122.41", "125.28"],
        ["Other income", "824.56", "518.01"],
        ["Total income", "31,674.68", "30,596.41"],
        ["Cost of materials consumed", "13,418.08", "14,790.95"],
        ["Purchases of stock-in-trade", "3,444.33", "3,836.33"],
        ["Changes in inventories of finished goods, stock-in-trade and work-in-progress", "356.98", "(299.74)"],
        ["Employee benefits expense", "1,747.89", "1,513.89"],
        ["Other expenses", "4,852.45", "4,416.49"],
        ["Total expenses", "23,819.73", "24,257.92"],
        ["Earning before interest, tax, depreciation and amortisation (EBITDA)", "7,854.95", "6,338.49"],
        ["Finance costs", "115.42", "93.06"],
        ["Depreciation and amortisation expense", "734.49", "755.83"],
        ["Profit before tax", "7,005.04", "5,489.60"],
        ["Total tax expense", "1,683.49", "1,389.42"],
        ["Profit after tax", "5,321.55", "4,100.18"],
        ["Basic earnings per equity share (₹)", "55.50", "42.76"],
    ],
}

ASIAN_BS = {
    "source": "asianpaints_fs_2023-24.pdf", "pdf_page": 11, "printed_page": 320,
    "company": "Asian Paints Limited",
    "title": "Standalone balance sheet of Asian Paints Limited as at 31st March, 2024.",
    "header": ["Particulars (₹ in crores)", "As at 31.03.2024", "As at 31.03.2023"],
    "rows": [
        ["Property, plant and equipment", "3,750.20", "3,487.58"],
        ["Right-of-use asset", "1,519.03", "1,080.94"],
        ["Capital work-in-progress", "2,560.93", "978.04"],
        ["Total non-current assets", "11,428.69", "8,654.11"],
        ["Inventories", "5,074.76", "5,321.79"],
        ["Investments (current)", "3,095.47", "2,597.37"],
        ["Trade receivables", "3,633.45", "3,462.61"],
        ["Cash and cash equivalents", "325.96", "156.44"],
        ["Total current assets", "14,553.21", "13,875.73"],
        ["Total assets", "25,981.90", "22,529.84"],
        ["Equity share capital", "95.92", "95.92"],
        ["Other equity", "18,329.17", "15,489.64"],
        ["Total equity", "18,425.09", "15,585.56"],
        ["Total non-current liabilities", "1,335.80", "1,112.82"],
        ["Trade payables - micro and small enterprises", "191.02", "95.69"],
        ["Trade payables - other creditors", "3,047.81", "2,950.17"],
        ["Total current liabilities", "6,221.01", "5,831.46"],
        ["Total equity and liabilities", "25,981.90", "22,529.84"],
    ],
}

MARICO_PL = {
    "source": "marico_ar_fy25.pdf", "pdf_page": 170, "printed_page": 337,
    "company": "Marico Limited",
    "title": "Consolidated statement of profit and loss of Marico Limited for the year ended 31st March, 2025.",
    "header": ["Particulars (₹ in crore)", "Year ended 31st March, 2025", "Year ended 31st March, 2024"],
    "rows": [
        ["Revenue from operations", "10,831", "9,653"],
        ["Other income", "208", "142"],
        ["Total income", "11,039", "9,795"],
        ["Cost of materials consumed", "4,572", "3,941"],
        ["Purchases of stock-in-trade", "960", "752"],
        ["Changes in inventories of finished goods, stock-in-trade and work-in progress", "(144)", "55"],
        ["Employee benefits expense", "831", "743"],
        ["Finance costs", "53", "73"],
        ["Depreciation and amortization expense", "178", "158"],
        ["Other expenses", "2,473", "2,136"],
        ["Total expenses", "8,923", "7,858"],
        ["Profit before tax", "2,116", "1,937"],
        ["Current tax", "480", "353"],
        ["Deferred tax charge / (credit)", "(22)", "82"],
        ["Tax expense", "458", "435"],
        ["Profit for the year", "1,658", "1,502"],
        ["Net profit attributable to owners", "1,629", "1,481"],
        ["Net profit attributable to non-controlling interests", "29", "21"],
        ["Basic earnings per share (₹)", "12.59", "11.46"],
    ],
}

MARICO_BS = {
    "source": "marico_ar_fy25.pdf", "pdf_page": 170, "printed_page": 336,
    "company": "Marico Limited",
    "title": "Consolidated balance sheet of Marico Limited as at 31st March, 2025.",
    "header": ["Particulars (₹ in crore)", "As at 31st March, 2025", "As at 31st March, 2024"],
    "rows": [
        ["Goodwill", "857", "863"],
        ["Total non-current assets", "3,255", "3,418"],
        ["Inventories", "1,235", "1,336"],
        ["Investments (current)", "1,375", "259"],
        ["Trade receivables", "1,271", "1,069"],
        ["Cash and cash equivalents", "321", "228"],
        ["Total current assets", "5,083", "4,003"],
        ["Total assets", "8,338", "7,421"],
        ["Equity attributable to owners", "3,975", "3,832"],
        ["Non-controlling interests", "291", "337"],
        ["Total equity", "4,266", "4,169"],
        ["Borrowings (current)", "379", "383"],
        ["Total current liabilities", "2,461", "2,444"],
        ["Total liabilities", "4,072", "3,252"],
        ["Total equity and liabilities", "8,338", "7,421"],
    ],
}

MARICO_10Y = {
    "source": "marico_ar_fy25.pdf", "pdf_page": 253, "printed_page": 502,
    "company": "Marico Limited",
    "title": "10-year financial highlights of Marico Limited (consolidated). Net profit excludes one-offs and extraordinary items.",
    "header": ["Year ended March 31 (₹ in crore)", "2016", "2017", "2018", "2019", "2020",
               "2021", "2022", "2023", "2024", "2025"],
    "rows": [
        ["Income from operations", "6,024", "5,936", "6,333", "7,334", "7,315", "8,048", "9,512", "9,764", "9,653", "10,831"],
        ["EBITDA", "1,051", "1,159", "1,138", "1,326", "1,469", "1,591", "1,681", "1,810", "2,026", "2,139"],
        ["Profit before tax (PBT)", "1,029", "1,149", "1,117", "1,257", "1,374", "1,523", "1,601", "1,743", "1,937", "2,116"],
        ["Net profit attributable to owners of the company", "711", "799", "814", "926", "1,043", "1,162", "1,225", "1,280", "1,470", "1,593"],
        ["Net worth", "2,017", "2,326", "2,523", "2,975", "3,023", "3,240", "3,348", "3,799", "3,832", "3,975"],
        ["EBITDA margin (%)", "17.5", "19.5", "18.0", "18.1", "20.1", "19.8", "17.7", "18.5", "21.0", "19.7"],
        ["Earning per share (EPS) (₹)", "5.5", "6.2", "6.3", "7.2", "8.1", "9.0", "9.5", "10.1", "11.5", "12.6"],
        ["Dividend per share (₹)", "3.4", "3.5", "4.3", "4.8", "6.8", "7.5", "9.3", "4.5", "9.5", "10.5"],
    ],
}

PIDILITE_PL = {
    "source": "pidilite_consolidated_fs_2024-25.pdf", "pdf_page": 5, "printed_page": 233,
    "company": "Pidilite Industries Limited",
    "title": "Consolidated statement of profit and loss of Pidilite Industries Limited for the year ended 31st March 2025.",
    "header": ["Particulars (₹ in crores)", "For the year ended 31st March 2025", "For the year ended 31st March 2024"],
    "rows": [
        ["Revenue from operations", "13,140.31", "12,382.99"],
        ["Other income", "247.22", "139.65"],
        ["Total income", "13,387.53", "12,522.64"],
        ["Cost of materials consumed", "5,393.15", "5,102.56"],
        ["Purchases of stock-in-trade", "741.89", "765.34"],
        ["Changes in inventories of finished goods, stock-in-trade and work-in-progress", "(138.76)", "126.12"],
        ["Employee benefits expense", "1,741.62", "1,465.07"],
        ["Finance costs", "50.35", "51.19"],
        ["Depreciation, amortisation and impairment expense", "358.48", "340.66"],
        ["Other expenses", "2,389.90", "2,216.63"],
        ["Total expenses", "10,536.63", "10,067.57"],
        ["Exceptional items", "24.92", "71.67"],
        ["Profit before tax", "2,822.70", "2,379.35"],
        ["Total tax expense", "726.53", "631.93"],
        ["Profit for the year", "2,096.17", "1,747.42"],
        ["Profit attributable to owners of the company", "2,076.24", "1,729.38"],
        ["Basic earnings per equity share (₹)", "40.82", "34.01"],
    ],
}

PIDILITE_BS = {
    "source": "pidilite_consolidated_fs_2024-25.pdf", "pdf_page": 5, "printed_page": 232,
    "company": "Pidilite Industries Limited",
    "title": "Consolidated balance sheet of Pidilite Industries Limited as at 31st March 2025.",
    "header": ["Particulars (₹ in crores)", "As at 31st March 2025", "As at 31st March 2024"],
    "rows": [
        ["Total non-current assets", "6,549.48", "6,267.54"],
        ["Inventories", "1,685.09", "1,414.90"],
        ["Investments (current)", "3,161.96", "1,870.16"],
        ["Trade receivables", "1,811.15", "1,674.69"],
        ["Cash and cash equivalents", "323.94", "515.14"],
        ["Total current assets", "7,461.99", "5,836.41"],
        ["Total assets", "14,011.47", "12,103.95"],
        ["Equity attributable to owners of the company", "9,754.46", "8,407.16"],
        ["Non-controlling interests", "203.30", "209.85"],
        ["Total equity", "9,957.76", "8,617.01"],
        ["Total non-current liabilities", "763.86", "689.36"],
        ["Borrowings (current)", "147.18", "131.15"],
        ["Total current liabilities", "3,289.85", "2,797.58"],
        ["Total liabilities", "4,053.71", "3,486.94"],
        ["Total equity and liabilities", "14,011.47", "12,103.95"],
    ],
}

# (table, question, formula, scale of the answer, extra text sentences)
QUESTIONS = [
    (TITAN_PL, "What was the percentage growth in revenue from operations from the year ended 31st March 2024 to the year ended 31st March 2025?",
     "(54842 - 47114) / 47114 * 100", "percent", []),
    (TITAN_PL, "What was the profit before tax margin (profit before tax as a percentage of revenue from operations) for the year ended 31st March 2025?",
     "4481 / 54842 * 100", "percent", []),
    (TITAN_PL, "What was the effective tax rate (total tax expense as a percentage of profit before tax) for the year ended 31st March 2025?",
     "1146 / 4481 * 100", "percent", []),
    (TITAN_PL, "By how much did finance costs increase from the year ended 31st March 2024 to the year ended 31st March 2025, in ₹ crore?",
     "767 - 480", "crore", []),
    (TITAN_PL, "What was the profit for the year ended 31st March 2025 expressed in ₹ lakh?",
     "3335 * 100", "lakh", []),
    (TITAN_PL, "What was the percentage change in profit for the year from the year ended 31st March 2024 to the year ended 31st March 2025?",
     "(3335 - 3544) / 3544 * 100", "percent", []),
    (TITAN_PL, "What were employee benefits expense and other expenses together as a percentage of total expenses for the year ended 31st March 2025?",
     "(1717 + 4093) / 50854 * 100", "percent", []),
    (TITAN_PL, "Did profit before tax increase in the year ended 31st March 2025 compared with the year ended 31st March 2024?",
     "'yes' if 4481 > 4607 else 'no'", "", []),
    (TITAN_BS, "What was the current ratio (total current assets divided by total current liabilities) as at 31st March 2025?",
     "30444 / 21645", "", []),
    (TITAN_BS, "What was the debt-to-equity ratio as at 31st March 2025, where debt is non-current borrowings plus current borrowings?",
     "(420 + 7483) / 16811", "", []),
    (TITAN_BS, "By what percentage did inventories increase from 31st March 2024 to 31st March 2025?",
     "(24517 - 16874) / 16874 * 100", "percent", []),
    (TITAN_BS, "What was the value of inventories as at 31st March 2025 in ₹ billion?",
     "24517 / 100", "billion", []),
    (TITAN_BS, "What was the return on average equity for the year ended 31st March 2025, i.e. profit for the year divided by the average of opening and closing total equity, in percent?",
     "3335 / ((16811 + 14457) / 2) * 100", "percent",
     ["Profit for the year ended 31st March 2025 as per the standalone statement of profit and loss was ₹ 3,335 crore."]),
    (ASIAN_PL, "What was the total revenue from operations (sale of products, sale of services and other operating revenue) in 2023-24?",
     "30635.29 + 92.42 + 122.41", "crore", []),
    (ASIAN_PL, "What was the EBITDA margin in 2023-24, defined as EBITDA as a percentage of total income?",
     "7854.95 / 31674.68 * 100", "percent", []),
    (ASIAN_PL, "What was the percentage growth in profit after tax from 2022-23 to 2023-24?",
     "(5321.55 - 4100.18) / 4100.18 * 100", "percent", []),
    (ASIAN_PL, "What was the interest coverage ratio (EBITDA divided by finance costs) in 2023-24?",
     "7854.95 / 115.42", "", []),
    (ASIAN_PL, "What was cost of materials consumed as a percentage of revenue from sale of products in 2022-23?",
     "14790.95 / 29883.09 * 100", "percent", []),
    (ASIAN_PL, "What was the profit after tax for 2023-24 in ₹ million?",
     "5321.55 * 10", "million", []),
    (ASIAN_PL, "By how much did basic earnings per share change from 2022-23 to 2023-24, in ₹?",
     "55.50 - 42.76", "", []),
    (ASIAN_BS, "What was the current ratio as at 31.03.2024?",
     "14553.21 / 6221.01", "", []),
    (ASIAN_BS, "By what percentage did capital work-in-progress increase from 31.03.2023 to 31.03.2024?",
     "(2560.93 - 978.04) / 978.04 * 100", "percent", []),
    (ASIAN_BS, "What were total trade payables (micro and small enterprises plus other creditors) as at 31.03.2024, in ₹ lakh?",
     "(191.02 + 3047.81) * 100", "lakh", []),
    (ASIAN_BS, "What percentage of total assets was financed by total equity as at 31.03.2024?",
     "18425.09 / 25981.90 * 100", "percent", []),
    (ASIAN_BS, "What was the return on average total equity for 2023-24, i.e. profit after tax divided by the average of opening and closing total equity, in percent?",
     "5321.55 / ((18425.09 + 15585.56) / 2) * 100", "percent",
     ["Profit after tax for the year 2023-24 as per the standalone statement of profit and loss was ₹ 5,321.55 crores."]),
    (MARICO_PL, "What was the percentage growth in revenue from operations in the year ended 31st March, 2025 over the previous year?",
     "(10831 - 9653) / 9653 * 100", "percent", []),
    (MARICO_PL, "What was the gross margin for the year ended 31st March, 2025, i.e. revenue from operations minus (cost of materials consumed + purchases of stock-in-trade + changes in inventories), as a percentage of revenue from operations?",
     "(10831 - (4572 + 960 - 144)) / 10831 * 100", "percent", []),
    (MARICO_PL, "What percentage of the profit for the year ended 31st March, 2025 was attributable to non-controlling interests?",
     "29 / 1658 * 100", "percent", []),
    (MARICO_PL, "What was the change in the deferred tax line from the year ended 31st March, 2024 to the year ended 31st March, 2025 (2025 value minus 2024 value), in ₹ crore?",
     "-22 - 82", "crore", []),
    (MARICO_PL, "What was the profit for the year ended 31st March, 2025 in ₹ billion?",
     "1658 / 100", "billion", []),
    (MARICO_BS, "What was the ratio of total liabilities to total equity as at 31st March, 2025?",
     "4072 / 4266", "", []),
    (MARICO_BS, "By what percentage did current investments grow from 31st March, 2024 to 31st March, 2025?",
     "(1375 - 259) / 259 * 100", "percent", []),
    (MARICO_10Y, "What was the compound annual growth rate (CAGR) of income from operations from the year ended March 31, 2016 to the year ended March 31, 2025, in percent?",
     "((10831 / 6024) ** (1 / 9) - 1) * 100", "percent", []),
    (MARICO_10Y, "What was the average dividend per share over the five years ended March 31, 2021 to March 31, 2025, in ₹?",
     "(7.5 + 9.3 + 4.5 + 9.5 + 10.5) / 5", "", []),
    (MARICO_10Y, "What was the dividend payout ratio (dividend per share as a percentage of EPS) for the year ended March 31, 2023?",
     "4.5 / 10.1 * 100", "percent", []),
    (MARICO_10Y, "By how much did net worth grow from March 31, 2016 to March 31, 2025, in ₹ crore?",
     "3975 - 2017", "crore", []),
    (MARICO_10Y, "What was the net profit attributable to owners of the company for the year ended March 31, 2025, in ₹ lakh?",
     "1593 * 100", "lakh", []),
    (PIDILITE_PL, "What was the percentage growth in profit for the year from the year ended 31st March 2024 to the year ended 31st March 2025?",
     "(2096.17 - 1747.42) / 1747.42 * 100", "percent", []),
    (PIDILITE_PL, "What was employee benefits expense as a percentage of revenue from operations for the year ended 31st March 2025?",
     "1741.62 / 13140.31 * 100", "percent", []),
    (PIDILITE_PL, "What was the operating EBITDA for the year ended 31st March 2025, i.e. revenue from operations minus (total expenses excluding finance costs and depreciation, amortisation and impairment), in ₹ crores?",
     "13140.31 - (10536.63 - 50.35 - 358.48)", "crore", []),
    (PIDILITE_PL, "What was the effective tax rate (total tax expense as a percentage of profit before tax) for the year ended 31st March 2024?",
     "631.93 / 2379.35 * 100", "percent", []),
    (PIDILITE_BS, "What was the quick ratio as at 31st March 2025, i.e. (total current assets minus inventories) divided by total current liabilities?",
     "(7461.99 - 1685.09) / 3289.85", "", []),
    (PIDILITE_BS, "What was the percentage change in cash and cash equivalents from 31st March 2024 to 31st March 2025?",
     "(323.94 - 515.14) / 515.14 * 100", "percent", []),
    (PIDILITE_BS, "What were total assets as at 31st March 2025 in ₹ million?",
     "14011.47 * 10", "million", []),
]


def report_numbers(table, texts):
    values = set()
    for row in table:
        for cell in row[1:]:
            v = parse_number(cell)
            if v is not None:
                values.add(abs(v))
    for sentence in texts:
        values |= {abs(n["value"]) for n in find_numbers(sentence)}
    return values


def gold_facts(table, texts, operands):
    facts = []
    for i, row in enumerate(table[1:], start=1):
        cells = {abs(v) for v in (parse_number(c) for c in row[1:]) if v is not None}
        if cells & operands:
            facts.append(f"table_{i}")
    for j, sentence in enumerate(texts):
        if {abs(n["value"]) for n in find_numbers(sentence)} & operands:
            facts.append(f"text_{j}")
    return facts


def check_against_pdf(specs):
    """Every transcribed cell must literally appear in the text of its PDF page."""
    for spec in specs:
        reader = PdfReader(DATA_INDIAN / "reports" / spec["source"])
        page_text = " ".join(reader.pages[spec["pdf_page"] - 1].extract_text().split())
        for row in spec["rows"]:
            for cell in row[1:]:
                assert cell in page_text, (spec["source"], spec["pdf_page"], row[0], cell)


def build():
    check_against_pdf({id(q[0]): q[0] for q in QUESTIONS}.values())
    records, checklist = [], []
    company_count = {}
    for spec, question, formula, scale, extra in QUESTIONS:
        result = run_code(f"ans = {formula}")
        assert result.ok, (question, result.error)
        gold = result.ans if isinstance(result.ans, str) else round(float(result.ans), 4)
        table = [spec["header"]] + spec["rows"]
        unit = "₹ crores" if "crores" in spec["header"][0] else "₹ crore"
        texts = [spec["title"], f"All amounts are in {unit} unless stated otherwise."] + extra
        literal_formula = re.sub(r"'[^']*'", "", formula)
        operands = {abs(float(x)) for x in re.findall(r"\d+(?:\.\d+)?", literal_formula)}
        missing = operands - report_numbers(table, texts) - FORMULA_CONSTANTS
        assert not missing, (question, missing)
        key = spec["company"].split()[0].lower()
        company_count[key] = company_count.get(key, 0) + 1
        uid = f"{key}-{company_count[key]:02d}"
        facts = gold_facts(table, texts, operands - FORMULA_CONSTANTS)
        evidence = "table-text" if any(f.startswith("text") for f in facts) else "table"
        records.append({"uid": uid, "company": spec["company"], "source": spec["source"],
                        "page": spec["pdf_page"], "printed_page": spec["printed_page"],
                        "question": question, "table": table, "texts": texts, "gold": gold,
                        "formula": formula, "scale": scale, "evidence": evidence,
                        "gold_facts": facts, "verified": False})
        checklist.append({"uid": uid, "company": spec["company"], "pdf_file": spec["source"],
                          "pdf_page": spec["pdf_page"], "printed_page": spec["printed_page"],
                          "question": question, "formula": formula, "gold": gold,
                          "numbers_match_pdf (yes/no)": "", "checked_by": ""})
    DATA_INDIAN.mkdir(parents=True, exist_ok=True)
    with open(DATA_INDIAN / "indian_set.jsonl", "w", encoding="utf-8") as out:
        for r in records:
            out.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(DATA_INDIAN / "verification_checklist.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=list(checklist[0]))
        writer.writeheader()
        writer.writerows(checklist)
    print(f"wrote {len(records)} questions from {len(company_count)} companies")


if __name__ == "__main__":
    build()
