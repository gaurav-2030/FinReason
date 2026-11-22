"""Hand-written prompts: instructions for each strategy and three worked examples (few-shot).
The worked examples are real FinQA *train* questions, so they never overlap with test data."""
from .data import Example
from .retrieval import build_context

SYSTEM_PROMPT = ("You are a careful financial analyst. Answer questions about a financial report "
                 "using only the table and text provided.")

ANSWER_FORMAT = """Answer format:
- The final answer is a single number. Unless the question asks for another unit, use the same units as the report (if the table says "in millions", answer in millions). Do not write the unit.
- Write percentages as percent numbers (12.5 means 12.5%).
- Use a minus sign for decreases and negative values.
- For yes/no questions, answer yes or no.
- The last line must be: Answer: <number>"""

INSTRUCTIONS = {
    "direct": "Give only the final answer line, with no explanation.",
    "cot": ("Think step by step: find the relevant numbers, write down the calculation, "
            "then compute it."),
    "decomp": ("Solve in four labelled parts:\n"
               "Knowledge: the financial formula or definition needed.\n"
               "Extract: every value needed, with where it comes from and its units.\n"
               "Decompose: the calculation as numbered steps, one arithmetic operation per step.\n"
               "Answer: the final answer."),
    "pot": ("Write Python code that computes the answer. Put each value from the report in a "
            "variable with a descriptive name, compute the result step by step, and store the final "
            "answer in a variable named ans (a number, or the string 'yes' or 'no'). Keep the "
            "report's units unless the question asks otherwise; give percentages as percent "
            "numbers (12.5 means 12.5%). Return only the code in one ```python block."),
}

REPAIR_PROMPT = ("Running your code failed with this error:\n{error}\n"
                 "Fix the code and return only the corrected code in one ```python block.")

EXEMPLARS = [
    {
        "example": Example(
            uid="C/2009/page_248.pdf-4", dataset="finqa",
            question="what was the percentage change in carrying amount reported on the consolidated balance sheet from 2008 to 2009?",
            table=[["in millions of dollars", "december 31 2009", "december 31 2008"],
                   ["carrying amount reported on the consolidated balance sheet", "$ 3338", "$ 4273"],
                   ["aggregate fair value in excess of unpaid principalbalance", "55", "138"],
                   ["balance of non-accrual loans or loans more than 90 days past due", "4", "9"],
                   ["aggregate unpaid principal balance in excess of fair value for non-accrualloans or loans more than 90 days past due", "3", "2"]],
            texts=["certain mortgage loans citigroup has elected the fair value option for certain purchased and originated prime fixed-rate and conforming adjustable-rate first mortgage loans held-for-sale .",
                   "these loans are intended for sale or securitization and are hedged with derivative instruments ."],
            gold=-0.21882),
        "cot": ("The table is in millions of dollars. The carrying amount reported on the consolidated "
                "balance sheet was 3338 at December 31, 2009 and 4273 at December 31, 2008.\n"
                "Percentage change = (2009 value - 2008 value) / 2008 value * 100 "
                "= (3338 - 4273) / 4273 * 100 = -935 / 4273 * 100 = -21.88.\n"
                "Answer: -21.88"),
        "decomp": ("Knowledge: percentage change = (new value - old value) / old value * 100.\n"
                   "Extract:\n"
                   "- carrying amount at December 31, 2009 = 3338 (table, $ millions)\n"
                   "- carrying amount at December 31, 2008 = 4273 (table, $ millions)\n"
                   "Decompose:\n"
                   "1. 3338 - 4273 = -935\n"
                   "2. -935 / 4273 = -0.21882\n"
                   "3. -0.21882 * 100 = -21.88\n"
                   "Answer: -21.88"),
        "pot": ("```python\n"
                "carrying_amount_2009 = 3338  # table, $ millions\n"
                "carrying_amount_2008 = 4273  # table, $ millions\n"
                "change = carrying_amount_2009 - carrying_amount_2008\n"
                "ans = change / carrying_amount_2008 * 100\n"
                "```"),
    },
    {
        "example": Example(
            uid="ADI/2010/page_73.pdf-2", dataset="finqa",
            question="what is the average-share price of the repurchased shares as of october 30 , 2010?",
            table=[["", "restricted stock units outstanding", "weighted- average grant- date fair value per share"],
                   ["restricted stock units outstanding at october 31 2009", "135", "$ 22.19"],
                   ["units granted", "1171", "$ 28.86"],
                   ["restrictions lapsed", "-19 ( 19 )", "$ 24.70"],
                   ["units forfeited", "-22 ( 22 )", "$ 29.10"],
                   ["restricted stock units outstanding at october 30 2010", "1265", "$ 28.21"]],
            texts=["unless terminated earlier by resolution of the company 2019s board of directors , the repurchase program will expire when the company has repurchased all shares authorized under the program .",
                   "as of october 30 , 2010 , the company had repurchased a total of approximately 116.0 million shares of its common stock for approximately $ 3948.2 million under this program .",
                   "an additional $ 51.8 million remains available for repurchase of shares under the current authorized program ."],
            gold=34.03621),
        "cot": ("The text says that as of October 30, 2010 the company had repurchased about 116.0 "
                "million shares for about $3948.2 million. The table is about restricted stock units, "
                "so it is not needed.\n"
                "Average price per share = total amount paid / number of shares = 3948.2 / 116.0 = 34.04.\n"
                "Answer: 34.04"),
        "decomp": ("Knowledge: average price per share = total amount paid / number of shares repurchased.\n"
                   "Extract:\n"
                   "- amount paid for repurchases = 3948.2 (text, $ millions)\n"
                   "- shares repurchased = 116.0 (text, millions of shares)\n"
                   "Decompose:\n"
                   "1. 3948.2 / 116.0 = 34.04\n"
                   "Answer: 34.04"),
        "pot": ("```python\n"
                "amount_paid = 3948.2  # text, $ millions\n"
                "shares_repurchased = 116.0  # text, millions of shares\n"
                "ans = amount_paid / shares_repurchased\n"
                "```"),
    },
    {
        "example": Example(
            uid="IP/2014/page_65.pdf-1", dataset="finqa",
            question="what percentage where brazilian papers net sales of printing papers sales in 2014?",
            table=[["in millions", "2014", "2013", "2012"],
                   ["sales", "$ 5720", "$ 6205", "$ 6230"],
                   ["operating profit ( loss )", "-16 ( 16 )", "271", "599"]],
            texts=["planned maintenance downtime costs are expected to be about $ 16 million lower with an outage scheduled in the 2015 first quarter at our georgetown mill compared with outages at our eastover and riverdale mills in the 2014 fourth quarter .",
                   "brazilian papers net sales for 2014 were $ 1.1 billion compared with $ 1.1 billion in 2013 and $ 1.1 billion in 2012 .",
                   "operating profits for 2014 were $ 177 million ( $ 209 million excluding costs associated with a tax amnesty program ) compared with $ 210 million in 2013 and $ 163 million in 2012 ."],
            gold=0.19231),
        "cot": ("Brazilian papers net sales for 2014 were $1.1 billion (text). The table, in millions, "
                "shows printing papers sales of 5720 in 2014. Both values must be in the same units: "
                "$1.1 billion = 1100 million.\n"
                "Percentage = 1100 / 5720 * 100 = 19.23.\n"
                "Answer: 19.23"),
        "decomp": ("Knowledge: share in percent = part / total * 100, with both values in the same units.\n"
                   "Extract:\n"
                   "- Brazilian papers net sales 2014 = 1.1 (text, $ billions) = 1100 ($ millions)\n"
                   "- printing papers sales 2014 = 5720 (table, $ millions)\n"
                   "Decompose:\n"
                   "1. 1.1 * 1000 = 1100\n"
                   "2. 1100 / 5720 = 0.19231\n"
                   "3. 0.19231 * 100 = 19.23\n"
                   "Answer: 19.23"),
        "pot": ("```python\n"
                "brazil_sales_2014 = 1.1 * 1000  # text says $1.1 billion; convert to $ millions\n"
                "printing_sales_2014 = 5720  # table, $ millions\n"
                "ans = brazil_sales_2014 / printing_sales_2014 * 100\n"
                "```"),
    },
]


# --- VPSC v2: an operation-aware program view -------------------------------------------------
# Error analysis of VPSC v1 showed that most wrong programs were not arithmetic slips but a wrong
# *operation*: all three worked examples above compute a ratio or percentage, so the small model
# answered "what was the change in X" with a percentage change, and averaged only the two end
# years of a range. This view states the operation rules and adds two worked examples (FinQA
# train) that show a plain change and a three-year average.
POT_GUIDE = """First decide which operation the question asks for:
- "change", "difference", "increase" or "decrease" with no word like percent, percentage, rate or % means the plain difference (later value minus earlier value) in the report's units. Do not divide by anything.
- "percentage change", "growth rate" or "% change" means (later - earlier) / earlier * 100.
- "percentage of", "portion", "share" or "ratio" means part / whole (times 100 for a percentage).
- "average" over a range such as 2017-2019 or "from 2011 to 2013" means the mean of every year in the range.
- Use the values for exactly the years and the row the question names."""

GUIDED_EXEMPLARS = [
    {
        "example": Example(
            uid="LMT/2013/page_46.pdf-1", dataset="finqa",
            question="what was the average backlog at year-end of mfc from 2011 to 2013",
            table=[["", "2013", "2012", "2011"],
                   ["net sales", "$ 7757", "$ 7457", "$ 7463"],
                   ["operating profit", "1431", "1256", "1069"],
                   ["backlog at year-end", "15000", "14700", "14400"]],
            texts=["backlog decreased in 2013 compared to 2012 primarily due to lower orders on several programs ."],
            gold=14700.0),
        "pot": ("```python\n"
                "# operation: average over 2011-2013, so use all three years\n"
                "backlog_2013 = 15000  # table\n"
                "backlog_2012 = 14700  # table\n"
                "backlog_2011 = 14400  # table\n"
                "ans = (backlog_2013 + backlog_2012 + backlog_2011) / 3\n"
                "```"),
    },
    {
        "example": Example(
            uid="ORLY/2009/page_77.pdf-4", dataset="finqa",
            question="what is the net change in the balance of accumulated other comprehensive loss from 2008 to 2009?",
            table=[["contract type", "balance in accumulated other comprehensive loss 2009",
                    "balance in accumulated other comprehensive loss 2008"],
                   ["interest rate swaps", "$ 13053", "$ 18874"]],
            texts=["the table below represents unrealized losses related to derivative amounts included in accumulated other comprehensive loss for the years ended december 31 , ( in thousands ) ."],
            gold=-5821.0),
        "pot": ("```python\n"
                "# operation: \"change\" with no percent, so a plain difference (later minus earlier)\n"
                "balance_2009 = 13053  # table, $ thousands\n"
                "balance_2008 = 18874  # table, $ thousands\n"
                "ans = balance_2009 - balance_2008\n"
                "```"),
    },
]


def guided_pot_messages(context, question, fmt="markdown", system=SYSTEM_PROMPT):
    """Program-of-Thought messages with the operation guide: the three original worked examples
    (their code labelled with the operation) followed by the plain-change and average examples."""
    labels = ["# operation: percentage change = (later - earlier) / earlier * 100\n",
              "# operation: average price = amount paid / shares\n",
              "# operation: share in percent = part / whole * 100\n"]
    shots = [(shot["example"], shot["pot"].replace("```python\n", "```python\n" + label, 1))
             for shot, label in zip(EXEMPLARS, labels)]
    shots += [(shot["example"], shot["pot"]) for shot in GUIDED_EXEMPLARS]
    messages = [{"role": "system", "content": system}]
    for example, code in shots:
        shot_context, _ = build_context(example, fmt=fmt, mode="full")
        messages.append({"role": "user", "content": _guided_user(shot_context, example.question)})
        messages.append({"role": "assistant", "content": code})
    messages.append({"role": "user", "content": _guided_user(context, question)})
    return messages


def _guided_user(context, question):
    return f"{context}\n\nQuestion: {question}\n\n{POT_GUIDE}\n\n{INSTRUCTIONS['pot']}"


def user_message(context, question, style):
    if style == "pot":
        return f"{context}\n\nQuestion: {question}\n\n{INSTRUCTIONS['pot']}"
    return f"{context}\n\nQuestion: {question}\n\n{INSTRUCTIONS[style]}\n\n{ANSWER_FORMAT}"


def build_messages(style, context, question, fewshot=False, fmt="markdown", system=SYSTEM_PROMPT):
    """Chat messages for one question. With fewshot=True the three worked examples are shown
    first as earlier user/assistant turns, written in the same table format as the question."""
    messages = [{"role": "system", "content": system}]
    if fewshot:
        for shot in EXEMPLARS:
            shot_context, _ = build_context(shot["example"], fmt=fmt, mode="full")
            messages.append({"role": "user",
                             "content": user_message(shot_context, shot["example"].question, style)})
            messages.append({"role": "assistant", "content": shot[style]})
    messages.append({"role": "user", "content": user_message(context, question, style)})
    return messages
