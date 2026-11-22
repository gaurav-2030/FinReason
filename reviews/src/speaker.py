"""Speaker scripts: what each presenter says on each slide, for all three reviews.
Scripts are keyed by slide-title prefix; numbers are computed from the runs, so they always match the slides."""
import re

import concise as C
import data
import review3 as R
from common import NOTES_CSS, TEAM, notes_head, page, table

S, L = data.SMALL, data.LARGE
P, acc, SL, ML = R.P, R.acc, data.strategy_label, data.model_label
FIRST = {name: name.split()[0] for name, _ in TEAM}


def pc(x):
    return f"{P(x, 0)} percent" if x is not None else "pending"


def direct_max():
    return max(acc(d, S, "direct") or 0 for d in data.DATASETS)


# ============================================================================================
# Review 1
# ============================================================================================
R1 = {
    "Title & introductions": lambda: (
        "Good morning, everyone. We are Gaurav, Sunay, Dhruvagouda and Hanshal. Our project is called FinReason. "
        "It is about one simple question: can AI models answer number questions about company annual reports correctly? "
        "For example: by how much did a company's revenue grow this year? "
        "Large language models, like ChatGPT, are very good with words. But they often make mistakes with numbers. "
        "In this project we test different ways of asking the model — we call these prompting strategies — and we find out which way works best. "
        "Here is our plan for today. I will explain the problem, why it matters, and our problem statement. "
        "Sunay will give our objectives, the literature, three foundational and three latest 2025 to 2026 papers with the gaps we address, and our pipeline. "
        "Hanshal will explain our seven prompting strategies with real prompts and code. "
        "Finally, Dhruvagouda will cover automatic prompt optimization, our experimental design and what is new in our work."),
    "Numerical questions": lambda: (
        "Let me start with a real example. This table is from Titan's annual report. All the amounts are in rupees crore. "
        "The question is: what was the growth in revenue from FY24 to FY25? "
        "A person answers this in four steps. First, find the right row, revenue from operations, and the two year columns. "
        "Second, read the numbers correctly — 54,842 and 47,114 — with the right unit. Be careful: a number in brackets, like 6,537, means minus 6,537. "
        "Third, pick the right formula: new value minus old value, divided by the old value, times 100. "
        "Fourth, do the calculation: the answer is 16.40 percent. "
        "If the model makes a mistake in any one of these four steps — one wrong digit, one wrong unit, or one wrong sign — the final answer is wrong. "
        "And the worst part is that the model still sounds confident. That is the problem we are working on."),
    "LLMs read finance": lambda: (
        "Why does this matter? Look at these three numbers from other researchers. "
        "First, on a well-known test called FinQA, the best computer model scored 61 percent. Human finance experts scored 91 percent. That is a big gap. "
        "Second, on another test called FinanceBench, GPT-4-Turbo got 81 percent of the questions wrong or refused to answer. So even big models struggle. "
        "Third, there is good news. When the model writes a small Python program instead of plain text, accuracy on FinQA goes up by 24 points. "
        "So how we ask the model makes a big difference. "
        "We also want to use small models that run on our own laptop. Financial data is private, and companies do not want to send it to outside servers. "
        "Changing the prompt is free and fast. That is why we focus on prompting."),
    "Problem statement": lambda: (
        "So here is our problem statement in one sentence: we want to find which prompting methods, and which automatic prompt-improvement methods, "
        "make AI models accurate, reliable and cheap when answering number questions about financial reports. "
        "Look at the three boxes. The input is one page of a report — a table and some text — plus a question. "
        "The output is the answer, and also the rows and the calculation that were used, so a person can check it. "
        "What we do not do: we do not retrain or fine-tune any model, and we do not search through whole 300-page reports. "
        "We keep the model fixed and change only the prompt. Then we measure how accuracy, cost and reliability change."),
    "Objectives": lambda: (
        "We have four objectives. "
        "One: compare seven prompting strategies, including our own method, VPSC. For example, asking for the answer directly, asking the model to think step by step, "
        "asking it many times and taking a vote, and asking it to write Python code. "
        "Two: test tools that improve the prompt automatically. These are DSPy and TextGrad. We want to know if they beat prompts written by hand. "
        "Three: compare a small model with 1.7 billion parameters and a bigger one with 8 billion parameters. We look at accuracy and also at cost. "
        "Four: study the mistakes the models make, check that the results are robust, and test the models on Indian annual reports, "
        "which use crore and lakh. Very few studies have looked at Indian reports, and we found none that tests multi-step calculations on them."),
    "Financial QA benchmarks": lambda: (
        "Now our literature survey. A benchmark is a standard set of test questions that everyone uses. These are the main ones for finance. "
        "FinQA has 8,281 questions written by finance experts. Each question comes with the exact steps to solve it. The best model got 61 percent, experts got 91. "
        "TAT-QA has about 16,500 questions on tables and text from annual reports. The best model got 50 percent exact matches, humans got 84. "
        "FinanceBench showed that even GPT-4-Turbo fails most questions about real company filings. "
        "And the EEDP paper tested many language models on four financial datasets. It also proposed a prompt that first extracts the numbers and then breaks the "
        "calculation into steps. Our decomposition strategy is based on this idea. "
        "Very recently, in 2026, two Indian benchmarks also appeared. IndFin-Bench asks mostly look-up questions about Indian company filings, "
        "and IndiaFinBench uses regulatory text from SEBI and RBI. Neither focuses on multi-step calculations from annual reports, which is what our Indian set does. "
        "The key point: even the best systems are about 30 points below human experts."),
    "Prompting strategies": lambda: (
        "These are the prompting strategies other researchers proposed. "
        "Chain-of-Thought means asking the model to explain its steps before giving the answer. Just adding the sentence 'let's think step by step' "
        "raised accuracy on a maths test from 10 to 41 percent. "
        "Self-Consistency means asking the same question several times and taking the most common answer, like a vote. It added about 18 points. "
        "Program-of-Thought means the model writes a small Python program, and the computer does the calculation. On FinQA this went from 40 to 64 percent. "
        "Decomposition means breaking a hard problem into smaller steps. "
        "So writing code is better than writing text for calculations. But plain Program-of-Thought trusts whatever numbers the model writes into the code. "
        "Two recent works do check numbers. VeriFin checks each number against the company's official structured data, called XBRL, using a logic solver. "
        "DCRC trains a special model to audit the evidence first. Both work well, but they need structured data, a solver, or extra training. "
        "Our idea is a much lighter check that needs none of these."),
    "Automatic prompt optimization": lambda: (
        "Writing good prompts by hand takes time. So some tools try to find good prompts automatically. "
        "DSPy builds the prompt for you. It tries the model on training questions and keeps the examples the model got right. It beat normal prompts by over 25 percent. "
        "MIPROv2 is part of DSPy. It searches over many instructions and examples to find the best mix, and gained up to 13 percent. "
        "TextGrad uses one model as a teacher. The teacher looks at wrong answers, explains what went wrong, and rewrites the prompt. "
        "Finally, GSM-Symbolic showed that if you change only the numbers in a maths question, models do worse. This suggests they sometimes memorize answers. "
        "The gap: we found no study that compares these tools with strong hand-written prompts on financial table questions."),
    "Main and latest papers": lambda: (
        "This slide shows the six papers our project builds on: three foundational ones at the top and three of the latest, from 2025 and 2026, below. "
        "FinQA defines our task; its fine-tuned model reached 61 percent against 91 for experts, but it needs fine-tuning and covers only US reports. We use prompting only and add Indian reports. "
        "Program-of-Thought lets Python do the arithmetic, from 40 to 64 percent on FinQA, but it trusts every number in the code. Our VPSC rejects numbers that are not in the report. "
        "EEDP found most errors come from extracting numbers, but compared only hand-written prompts. We add DSPy and TextGrad and a memorization test. "
        "Now the latest work. FinanceReasoning, ACL 2025, is a harder benchmark; even OpenAI o1 writing Python reaches only 89 percent, and it uses only very large models. We test small local models. "
        "VeriFin, 2026, checks each number with XBRL data and a logic solver and accepted no wrong claims, but it needs XBRL, which Indian annual-report PDFs do not have. VPSC checks the plain table. "
        "IndiaFinBench, 2026, is the newest Indian benchmark, but it uses SEBI and RBI regulatory text and tests models zero-shot only. Our Indian set has multi-step calculations from annual reports, and we compare seven strategies on it."),
    "Gaps we address": lambda: (
        "From our survey, we found four gaps. "
        "Gap one: studies rarely report accuracy, cost and statistical tests together, so it is hard to compare methods fairly. "
        "Gap two: we found no study that compares automatic prompt tools with hand-written prompts for financial calculations. "
        "Gap three: the main test sets use American company reports. The new Indian benchmarks test look-up questions or regulatory text, "
        "not multi-step calculations with crore, lakh, Indian digit grouping like 1,00,000, and brackets for negative numbers. "
        "Gap four: the tools that check a model's numbers need structured XBRL data, a logic solver or extra training. "
        "Plain Program-of-Thought has no light-weight check. "
        "Our project addresses these four gaps."),
    "One pipeline": lambda: (
        "This picture shows our approach. Every question goes through the same eight steps. "
        "Step one, load the question. Step two, turn the table into text the model can read. Step three, build the prompt using one strategy. "
        "Step four, the model answers. Step five, if the model wrote code, we run it in a safe sandbox. "
        "Step six, we check if the answer is correct. Step seven, if it is wrong, we find out why. Step eight, we save everything for analysis. "
        "The important idea is this: the questions, the model and the checking are always the same. Only the prompting strategy changes. "
        "So if the results are different, we know the strategy caused it. That makes our comparison fair."),
    "Our seven prompting strategies": lambda: (
        "We compare seven prompting strategies, from the simplest to our own method. "
        "Direct asks only for the answer; it is our baseline. Zero-shot Chain-of-Thought adds one instruction: think step by step. "
        "Few-shot Chain-of-Thought also shows three worked examples, taken from the FinQA training set so they never overlap with test questions. "
        "Decomposition, based on the EEDP paper, forces four labelled parts: the formula, the extracted values, the steps and the answer. "
        "Program-of-Thought asks for Python code, and our sandbox runs it. Self-Consistency samples five answers and takes a vote. "
        "VPSC, our method, samples five programs and keeps only those whose numbers are really in the report. "
        "Each strategy targets a different kind of error, shown in the last column. On top of these, three automatic optimizers give ten configurations in total."),
    "Text-based strategies": lambda: (
        "Here is one question asked in four different ways. The question is the revenue growth from FY24 to FY25. "
        "With Direct, the model gives only a number, so we cannot see or check how it got it. "
        "With zero-shot Chain-of-Thought, it writes the two numbers and the calculation before the answer. "
        "Few-shot Chain-of-Thought shows it worked examples first, so it copies the right format, units and rounding. "
        "Decomposition is the most structured: formula first, then each value with its year and unit, then one operation per step. "
        "All four use the same answer rules, so only the reasoning instruction differs. The key point: the more structure we ask for, the more clearly we can see where each number came from, so errors become visible."),
    "Code-based strategies": lambda: (
        "Now the code-based strategies. In Program-of-Thought the model writes Python with a named variable for each value, "
        "and the sandbox computes the answer. So the computer, not the model, does the arithmetic. If the code fails, we send the error back once so the model can fix it. "
        "VPSC builds on this. We sample five programs, run each one, and check every number written in the code. "
        "If a number such as 54,482 does not appear in the report, that program is dropped. The remaining programs vote. "
        "Our ablation, PoT Self-Consistency, uses the same five programs without the check, so any difference comes from the verification alone."),
    "Optimizing the prompts": lambda: (
        "Besides hand-written prompts, we test three automatic optimizers. "
        "DSPy BootstrapFewShot chooses the worked examples: it keeps examples the model solved correctly on training questions. "
        "MIPROv2 also rewrites the instruction, searching over instruction and example combinations. "
        "TextGrad lets a language model criticise the wrong answers and rewrite the system prompt, and we keep the new prompt only if dev accuracy does not drop. "
        "In their papers, DSPy improved over few-shot prompting by more than 25 percent, MIPROv2 by up to 13 percent, and TextGrad raised GPT-4o from 51 to 55 percent on a science test. "
        "We use only 50 training and 40 dev FinQA questions, the same scorer as our experiments, and we report their one-time token cost. "
        "Our question: can these automatic tools beat carefully written prompts on financial tables?"),
    "Experimental design": lambda: (
        "This is our full experimental design. The factors are ten prompt configurations, two local Qwen3 models, three datasets, "
        "four table formats, full page versus retrieved rows, and thinking mode on or off. "
        "We measure accuracy, exact match and F1, tokens per question and per correct answer, latency, and how often the format or code fails. "
        "For analysis we use 95 percent confidence intervals, McNemar tests against few-shot Chain-of-Thought, accuracy by number of steps and evidence source, "
        "an eight-category error taxonomy, and a test where we change the numbers to detect memorization."),
    "What is new": lambda: (
        "What is new in our project? Four things. "
        "First, our own method called VPSC. The model writes five programs. We run all five. Then we check every number in each program. "
        "If a program uses a number that is not in the report, we throw it away. Then the remaining programs vote on the answer. "
        "It is related to recent checkers like VeriFin and DCRC, but it is much lighter: it needs no structured data, no solver and no training. "
        "Second, a new test set of 44 calculation questions that we wrote ourselves, from the annual reports of Titan, Asian Paints, Marico and Pidilite. "
        "These use crore and lakh, and unlike the recent Indian benchmarks, every question needs a multi-step calculation. "
        "Third, a fair head-to-head comparison of hand-written prompts and automatic prompt tools, with cost and statistical tests. "
        "Fourth, a web app that shows exactly how every answer was found — the rows used, the code and the votes."),
    "Key references": lambda: (
        "These are our most important references. "
        "FinQA and TAT-QA give us our test questions. FinanceBench and the EEDP paper show how language models perform on financial questions. "
        "Chain-of-Thought, Self-Consistency and Program-of-Thought are the prompting strategies we compare. "
        "DSPy, MIPROv2 and TextGrad are the automatic prompt tools. GSM-Symbolic gave us the idea for our memorization test. "
        "The Qwen3 report describes the models we use. "
        "And several very recent works are the closest to ours: FinanceReasoning, a 2025 benchmark for financial calculations; IndFin-Bench and IndiaFinBench for Indian data; and VeriFin and DCRC for checking a model's numbers. "
        "Every number on our slides comes from these papers, and the full list is in our report."),
    "Thank you & Q&A": lambda: (
        "To sum up. AI models are good with words but make mistakes with numbers in financial reports. "
        "We will find out which ways of prompting fix this, how much they cost, and whether they work on Indian reports too. "
        "We will also test our own checking method, VPSC. Thank you for listening. We are happy to answer your questions."),
}


# ============================================================================================
# Review 2
# ============================================================================================
def r2_first():
    lo, hi = R.reasoning_range(S)
    return (f"Here are our first results, with the small 1.7 billion parameter model. The numbers are the percentage of questions answered correctly. "
            f"Look at the first row. When we ask for the answer directly, with no working, the model gets at most {pc(direct_max())}. It is almost always wrong. "
            f"Now look at the other rows. As soon as we ask the model to show its reasoning, accuracy jumps to between {pc(lo)} and {pc(hi)}. "
            f"Program-of-Thought, where the model writes code, is the best on FinQA with {pc(acc('finqa', S, 'pot_fs'))}, and on our Indian set with "
            f"{pc(acc('indian', S, 'pot_fs'))}. On TAT-QA, step-by-step reasoning with examples is best, with {pc(acc('tatqa', S, 'cot_fs'))}. "
            "So even a small model becomes useful when we prompt it well. We will show the full analysis in Review 3.")


R2 = {
    "Title & introductions": lambda: (
        "Good morning, everyone. We are Gaurav, Sunay, Dhruvagouda and Hanshal, and our project is FinReason. "
        "A quick reminder: in Review 1 we explained the problem. AI models often make mistakes with numbers in financial reports, "
        "and we want to find the best way to prompt them. We also surveyed the research papers. "
        "Today we show two things: how we designed our system, and how we collected and checked our data. "
        "I will explain the overall design. Sunay will explain the prompting strategies and the data. Hanshal will explain our VPSC method, "
        "the automatic prompt tools and how we score answers. Dhruvagouda will explain the safety sandbox and our progress so far."),
    "Six layers": lambda: (
        "Our system is built in six layers, like floors of a building. Let me go from the bottom up. "
        "The data layer loads our three datasets and puts every question into the same format. "
        "The context layer turns each table into text that the model can read, and can pick out the most useful rows. "
        "The reasoning layer is the heart of the system. It has the prompts, the strategies, the connection to the model, the safe sandbox for running code, "
        "and our grounding checker. "
        "The optimization layer runs the automatic prompt tools, DSPy and TextGrad. "
        "The evaluation layer checks every answer, finds the type of mistake and does the statistics. "
        "And the top layer saves every answer and shows the results in charts and in our web app."),
    "How one question flows": lambda: (
        "Now let me follow one question through the system, step by step. Take the Titan revenue question. "
        "First, we load the question with its table and text. "
        "Second, we turn the table into text, for example as a Markdown table. "
        "Third, we build the prompt for the chosen strategy, for example 'write Python code'. "
        "Fourth, the model answers. We use Qwen3, which runs on our own laptop through a program called Ollama. "
        "Fifth, if the model wrote code, we run it in a safe sandbox. If not, we read the line that starts with 'Answer'. "
        "Sixth, we check if the answer is correct. Seventh, if it is wrong, we find out why. "
        "Eighth, we save everything as one line in a file. The experiments and the web app both use exactly these steps."),
    "Key modules": lambda: (
        "The code is split into modules. Each module has one job. "
        "data.py loads the three datasets. tables.py turns tables into text, and retrieval.py finds the most useful rows. "
        "prompts.py and strategies.py contain all the prompts and strategies. Every strategy works the same way from the outside, "
        "so it is easy to add a new one. "
        "llm.py talks to the model. It also saves every answer in a cache, so if an experiment stops, we can restart it without losing work. "
        "sandbox.py runs the model's code safely, and verify.py checks the numbers in the code. "
        "Finally, answers.py, errors.py and metrics.py check the answers, sort the mistakes into types, and calculate the statistics."),
    "Strategies compared": lambda: (
        "These are the strategies we compare. Let me explain each one simply. "
        "Direct: we ask for the answer only, with no working. "
        "Chain-of-Thought: we ask the model to think step by step — with no examples, or with three worked examples. "
        "Decomposition: the model first writes the formula, then lists the numbers, then does one step at a time. "
        "Program-of-Thought: the model writes Python code and the computer calculates. "
        "Self-Consistency: we ask five times and take a vote. "
        "VPSC is our own method, and DSPy and TextGrad are the automatically improved prompts. "
        "To keep it fair, all strategies use the same instructions, the same answer format and the same worked examples. Only the strategy changes."),
    "Three datasets": lambda: (
        "We use three datasets. "
        "FinQA comes from American company earnings reports. We use 100 test questions, picked at random but fixed, so every strategy gets the same questions. "
        "TAT-QA comes from annual reports. We use 100 questions that need calculation. "
        "And our own Indian set has 44 questions. "
        "Look at the charts. The left chart shows how many calculation steps each question needs. Most FinQA questions need one step. "
        "TAT-QA and the Indian set have many more questions with three or more steps, so they are harder. "
        "The right chart shows where the numbers are: mostly in the table, but sometimes in the text, or in both."),
    "How we built and checked it": lambda: (
        "This slide shows how we built the Indian set, step by step. "
        "We downloaded the official annual reports of Titan, Asian Paints, Marico and Pidilite. "
        "We found the profit and loss statement and the balance sheet, and we copied the rows exactly as printed. "
        "For every question, we wrote a formula. The correct answer is calculated by running the formula. We never typed an answer by hand, so there are no typing mistakes. "
        "We also added automatic checks. All 366 numbers we copied must appear on the original PDF page, or the program stops with an error. "
        "And for this review, we checked all 44 questions again against the PDF pages ourselves. All 44 passed."),
    "VPSC: Verified": lambda: (
        "This is our own method, VPSC, which stands for Verified Program Self-Consistency. Let me explain it with the picture. "
        "We give the model the question and ask it to write a Python program — not once, but five times. "
        "The first program is the model's best guess. The other four are a little more varied. "
        "We run all five programs in the sandbox. "
        "Then comes our new step: the grounding check. We look at every number inside each program. If a program uses a number that is not in the report, "
        "it is probably made up, so we throw that program away. "
        "Then the programs that are left vote, and the most common answer wins. "
        "To test if the check really helps, we also run the same five programs without the check. Then we compare."),
    "DSPy and TextGrad design": lambda: (
        "These are the two automatic prompt tools. "
        "On the left is DSPy. We give it 50 training questions. It runs the model on them and keeps the examples the model solved correctly. "
        "Those examples are then put into the prompt. The MIPROv2 version also tries different instructions and keeps the best combination. "
        "On the right is TextGrad. Here, the instruction text itself is improved. The model answers a few questions. "
        "When an answer is wrong, a bigger model acts like a teacher: it explains the mistake and rewrites the instruction. "
        "We keep the new instruction only if it does better on a separate set of practice questions. "
        "Very important: both tools only use training questions. They never see our test questions, so the test stays fair."),
    "Scoring rule": lambda: (
        "This is how we decide if an answer is correct. "
        "An answer is correct if it is within half a percent of the true answer. So small rounding differences are fine. "
        "For percentages, we accept both forms. For example, 12.5 and 0.125 are both correct for 12.5 percent, because one dataset writes percentages as fractions. "
        "Our answer reader understands the rupee and dollar signs, Indian grouping like 1,00,000, brackets for negative numbers, and words like crore and lakh. "
        "To compare two strategies fairly, we use a statistical test called McNemar's test. It looks only at the questions where one strategy was right and the other was wrong. "
        "We use the same scoring everywhere, so all results can be compared."),
    "Sandbox: running": lambda: (
        "When the model writes code, we cannot trust it. The code could try to read our files or run forever. So we run it in a sandbox, which is a safe, closed box. "
        "It has four layers of protection. "
        "First, before running, we check the code. Only the math library is allowed. Anything touching files, the internet or the system is blocked. "
        "Second, every program runs in its own separate Python process, away from our main program. "
        "Third, only safe built-in functions are available. "
        "Fourth, there is a time limit of five seconds. If the code takes longer, we stop it. "
        "If the code has an error, we show the error to the model once, and it gets one chance to fix it."),
    "Project status": lambda: (
        "Now our progress. On the left is what is done. "
        f"The software library is complete, with {data.code_stats()[0]} modules. The web app works. We have {data.code_stats()[2]} automatic tests, and all of them pass. "
        "All three datasets are ready and checked. We measured how well our retrieval finds the right rows. "
        "And all experiments with the small 1.7 billion parameter model are finished. "
        "On the right is what comes next, for Review 3. "
        "We will finish the experiments with the bigger 8 billion parameter model, get the results of the automatic prompt tools, "
        "do the final analysis, write the IEEE paper and prepare a live demo."),
    "First results": r2_first,
    "Thank you & Q&A": lambda: (
        "To sum up today. We built one fair pipeline where only the prompt changes. We run the model's code safely. "
        "We built and checked a new Indian dataset. And our first results show that good prompting makes even a small model useful. "
        "Thank you for listening. We are happy to answer your questions."),
}


# ============================================================================================
# Review 3
# ============================================================================================
def status_text():
    rows = R.status_rows()
    todo = [r[0] for r in rows if not r[1].startswith("✓")]
    big = [r for r in rows if r[2] != "n/a"]
    big_done = sum(1 for r in big if r[2].startswith("✓"))
    txt = ("This table shows which experiments are finished. Each row is one group of experiments. "
           f"With the small 1.7 billion parameter model, {len(rows) - len(todo)} out of {len(rows)} groups are complete")
    txt += (f". Still running: {', '.join(todo)}. " if todo else ". ")
    txt += (f"The bigger 8 billion parameter model is much slower, so {big_done} of its {len(big)} groups are complete so far. "
            "Its results will appear on these slides as soon as its main experiments finish."
            if big_done < len(big) else "All experiments with the 8 billion parameter model are complete as well.")
    return txt + " Everything you see in this review comes straight from these finished experiments."


def ablation_text(th, r0):
    parts = ["On this slide we changed one thing at a time, to see what else affects accuracy."]
    fm = {f: acc("finqa", S, "cot_fs", fmt=f) for f in ["markdown", "json", "html", "text"]}
    if all(v is not None for v in fm.values()):
        names = {"markdown": "Markdown", "json": "JSON", "html": "HTML", "text": "plain row text"}
        hi_f, lo_f = max(fm, key=fm.get), min(fm, key=fm.get)
        parts.append(f"First, the table format — how we write the table for the model. On FinQA, {names[hi_f]} worked best with {pc(fm[hi_f])}, "
                     f"and {names[lo_f]} worked worst with {pc(fm[lo_f])}. So the way the table is written matters.")
    rt, full = acc("finqa", S, "pot_fs", context="retrieved"), acc("finqa", S, "pot_fs")
    if rt is not None:
        parts.append(f"Second, we tried giving the model only the five most relevant rows instead of the whole page. On FinQA this "
                     f"{'lowered' if rt < full else 'changed'} accuracy from {pc(full)} to {pc(rt)}"
                     + (", because sometimes a needed number was left out." if rt < full else "."))
    if th is not None:
        tp = C.thinking_p(S)
        parts.append(f"Third, Qwen3 has a 'thinking mode', where it thinks for longer before answering. It raised accuracy from {pc(r0.accuracy)} to {pc(th.accuracy)}"
                     + (", and this difference is statistically significant" if tp is not None and tp < 0.05 else "")
                     + f". But it used about {th.total_tokens / r0.total_tokens:.0f} times the text and took about {th.latency_s / r0.latency_s:.0f} times longer. "
                     "So it helps, but it is slow.")
    return " ".join(parts)


def vpsc_text(dg):
    if dg.empty:
        return "This is our method, VPSC. Its results are still being computed."
    fl, wrong = int(dg.flagged_questions.sum()), int(dg.flagged_questions.sum() - dg.flagged_correct.sum())
    same = all(acc(d, S, "vpsc") == acc(d, S, "pot_sc") for d in dg.dataset)
    txt = ("Now our own method, VPSC. Remember: the model writes five programs, and we throw away any program that uses a number not found in the report. "
           f"Here is what happened. Out of {int(dg.executed.sum())} programs that ran, the check threw away {int(dg.ungrounded.sum())}. "
           f"These came from {fl} questions. ")
    if same:
        txt += ("Look at the first two columns. VPSC got the same accuracy as voting without the check. Why? Because this small model usually writes the same "
                "program five times. So when one program is bad, all five are bad, and throwing them away does not change the vote. ")
    else:
        txt += "Compared with voting without the check, VPSC changed some answers — the table shows the effect for each dataset. "
    if fl and wrong == fl:
        txt += (f"But here is the useful part: all {fl} answers that the check flagged were wrong. So when the check fires, we know the answer cannot be trusted. "
                "We can use it as a warning light for the user.")
    return txt


def findings_text(lo, hi, vc, dg, pm, th, r0):
    parts = ["Let me sum up our key findings in simple words.",
             f"One: showing the working is essential. Asking for the answer directly gets at most {pc(direct_max())}. Asking for reasoning gets {pc(lo)} to {pc(hi)}.",
             f"Two: {R.single_sentence(S)}."]
    fs = R.five_sentence(S)
    if fs:
        parts.append(f"Three: asking five times and voting is not worth it for a small model — {fs}.")
    parts.append(f"Four: the main problem is picking the right numbers. About {100 * vc.get('evidence_error', 0):.0f} percent of mistakes come from using a wrong or missing number.")
    if not dg.empty and dg.flagged_questions.sum() and dg.flagged_correct.sum() == 0:
        parts.append("Five: our VPSC check is a reliable warning light — every answer it flagged was wrong.")
    if not pm.empty:
        parts.append("Six: " + ("when we change the numbers, accuracy does not drop significantly, so the model is not just remembering answers"
                                if all(r.p_value >= 0.05 for r in pm.itertuples()) else "when we change the numbers, accuracy drops, so the model partly remembers answers")
                     + ("; and the methods also work on Indian reports." if (acc("indian", S, "pot_fs") or 0) >= (acc("finqa", S, "pot_fs") or 1) else "."))
    if th is not None and th.n >= 100:
        parts.append(f"And finally, thinking mode helps a lot — {pc(r0.accuracy)} to {pc(th.accuracy)} — but it is much slower.")
    return " ".join(parts)


def r3_scripts():
    lo, hi = R.reasoning_range(S)
    dg = data.vpsc_diagnostics(S)
    es = R.error_shares(S)
    vc = es[0] if es else {}
    mult = R.five_sample_multiplier(S)
    pt = data.perturbation()
    pm = pt[pt.model == S] if not pt.empty else pt
    th = data.cell("finqa", S, "cot_zs", think=True)
    r0 = data.cell("finqa", S, "cot_zs")
    opts = data.optimized_strategies(S)
    fr = {d: ", then ".join(SL(r.strategy) for r in R.frontier(S, d)) for d in ["finqa", "tatqa"]}
    has8 = R.has_model(L)

    def main(m):
        names = {"finqa": "FinQA", "tatqa": "TAT-QA", "indian": "the Indian set"}
        ds = [d for d in data.DATASETS if acc(d, m, "direct") is not None]   # datasets with finished runs
        b = {d: R.best(d, m) for d in ds}
        best_txt = " ".join(f"On {names[d]} the best is {SL(b[d].strategy)} with {pc(b[d].accuracy)}." for d in ds if b[d] is not None)
        return (f"This is our main result, for the {ML(m)} model. Each bar shows the percentage of questions answered correctly. "
                "The thin black line on each bar shows the uncertainty — the true value is very likely inside that range. "
                f"Look at the top bar, Direct. It is very short: {', '.join(pc(acc(d, m, 'direct')) for d in ds)} on {', '.join(names[d] for d in ds)}. "
                "Without showing its working, the model almost always fails. "
                "Every other strategy is much higher. "
                f"{best_txt} "
                + ("But notice that the good strategies are close to each other. Our statistical test shows that none of these differences is significant. "
                   "So the big win is to ask for reasoning at all." if not R.any_significant(m, R.REASONING)
                   else "Some of these differences are statistically significant, as shown in our report."))

    opt_txt = ("This slide is for the automatic prompt tools, DSPy and TextGrad. Their experiments run last, and they are still running. "
               "When they finish, this slide will show whether the automatically improved prompts beat our hand-written prompts, "
               "and how much time and computing it cost to improve them.")
    if opts:
        parts = [f"{SL(s)} got {pc(acc('finqa', S, s))} on FinQA, compared with {pc(acc('finqa', S, 'cot_fs'))} for our hand-written prompt with examples"
                 for s in opts]
        opt_txt = ("These are the results of the automatic prompt tools. " + "; ".join(parts) + ". "
                   "Our report also lists how much time and computing each tool needed to improve the prompt.")

    sc = {
        "Title & introductions": (
            "Good morning, everyone. We are Sunay, Gaurav, Dhruvagouda and Hanshal, and this is our final review of FinReason. "
            "As a reminder, our question is: which way of prompting an AI model gives correct answers to number questions about financial reports? "
            "Today we show our results and a live demo. "
            "I will remind you of our setup and show the main results. Gaurav will look deeper into the results. Hanshal will cover the automatic prompt tools "
            "and our robustness tests. And Dhruvagouda will show the live demo and conclude."),
        "What we compared": (
            "First, a quick reminder of how we tested. Every question goes through the same eight steps, as shown in this picture. "
            "The questions, the model and the checking stay the same. Only the prompting strategy changes. "
            "In total we compared 11 strategies on three datasets, which is 244 questions. "
            "We used Qwen3 models that run on our own laptop, so no data left our machine. "
            "Because everything else is fixed, any difference in the results is caused by the strategy."),
        "Experimental setup": (
            "Here are the details of the setup. "
            "We used 100 FinQA questions, 100 TAT-QA questions, all 44 Indian questions, and 88 FinQA questions where we changed the numbers. "
            "An answer counts as correct if it is within half a percent of the true answer. "
            "Because we only have about 100 questions per dataset, we also show uncertainty ranges. "
            "And when we say one strategy is better than another, we check it with a statistical test called McNemar's test. "
            "That way we do not claim a difference that could just be luck."
            + (" The table below shows which experiments are complete." if has8 else "")),
        "Experiment status": status_text(),
        "Accuracy by strategy — Qwen3-1.7B": main(S),
        "Accuracy by strategy — Qwen3-8B": main(L) if has8 else "",
        "1.7B vs 8B": ("This chart compares the small and the big model. For each strategy, blue is the small 1.7 billion model and orange is the bigger 8 billion model. "
                       + " ".join(f"With {SL(s)}, FinQA accuracy goes from {pc(acc('finqa', S, s))} to {pc(acc('finqa', L, s))}." for s in ["direct", "cot_fs", "pot_fs"]
                                  if acc('finqa', L, s) is not None)
                       + (" So a bigger model helps, but a good prompt on the small model already gets a long way."
                          if has8 and sum(acc(d, L, st) - acc(d, S, st) for d in data.DATASETS for st in data.MAIN_ORDER
                                          if acc(d, L, st) is not None and acc(d, S, st) is not None) > 0
                          else " So the bigger model does not clearly beat the small one with a good prompt.") if has8 else ""),
        "Indian annual reports": (
            "Now the Indian annual reports. These are new questions that we wrote ourselves, so no model could have seen them before. "
            "They are in rupees crore and lakh, they use brackets for negative numbers, and the tables are long. "
            f"Look at the table. Asking directly gets only {pc(acc('indian', S, 'direct'))}. "
            f"Step-by-step reasoning with examples gets {pc(acc('indian', S, 'cot_fs'))}. "
            f"And Program-of-Thought, where the model writes code, gets {pc(acc('indian', S, 'pot_fs'))}. "
            + (f"That is even higher than on FinQA, where it got {pc(acc('finqa', S, 'pot_fs'))}. So our methods work on Indian reports too."
               if (acc('indian', S, 'pot_fs') or 0) >= (acc('finqa', S, 'pot_fs') or 1)
               else f"That is lower than on FinQA, where it got {pc(acc('finqa', S, 'pot_fs'))}, so Indian reports are harder for the model.")),
        "Accuracy vs. cost": (
            "Now let's look at cost. A token is a small piece of text — the model reads and writes tokens, and more tokens means more time and more money. "
            "On this chart, left means cheaper and up means more accurate. So the best strategies are at the top left. "
            f"Going from cheapest to most accurate, the best-value strategies on FinQA are {fr['finqa']}. On TAT-QA they are {fr['tatqa']}. "
            "Every other strategy costs more without being more accurate. "
            "Now look at the right side of the chart. These are the strategies that ask the model five times. "
            + (f"They use {mult[0]:.1f} to {mult[1]:.1f} times more tokens than asking once, " if mult else "They use about five times more tokens, ")
            + ("but they are not significantly more accurate. So for a small model, asking five times is not worth the cost."
               if not R.any_significant(S, ["sc_cot", "pot_sc", "vpsc"]) else "and some of them are significantly more accurate, so here the extra cost can pay off.")),
        "Why answers are wrong": (
            "Next, we looked at why answers are wrong. For every wrong answer, our program decides the type of mistake using fixed rules. "
            f"The blue part is the biggest. About {100 * vc.get('evidence_error', 0):.0f} percent of mistakes are evidence errors. "
            "That means the model used a wrong number, or forgot a number it needed. "
            f"About {100 * vc.get('reasoning_error', 0):.0f} percent are reasoning errors: the numbers were right but the formula was wrong. "
            f"About {100 * vc.get('scale_error', 0):.0f} percent are unit errors, like mixing up millions and thousands, and {100 * vc.get('sign_error', 0):.0f} percent "
            "are sign errors, like plus instead of minus. "
            "The grey part at the top is the Direct strategy, which usually shows no working at all. "
            "So the main problem is not the maths. It is picking the right numbers."),
        "VPSC result": vpsc_text(dg),
        "DSPy and TextGrad": opt_txt,
        "Memorization check": (
            "Many of these test questions are public, so a model might have memorized the answers. We tested this. "
            "We took 88 FinQA questions and changed every number in them by 10 to 30 percent. Then we calculated the new correct answers. "
            "If the model just remembers old answers, it will fail on the new numbers. "
            + ("Look at the table. " + "; ".join(f"{SL(r.strategy)} went from {pc(r.original_accuracy)} to {pc(r.perturbed_accuracy)}" for r in pm.itertuples()) + ". "
               + ("These are small drops, and our statistical test says none of them is significant. So the model is really calculating, not remembering."
                  if all(r.p_value >= 0.05 for r in pm.itertuples()) else "Some drops are significant, so the model partly remembers answers.")
               if not pm.empty else "This test is still running.")),
        "What else changes accuracy": ablation_text(th, r0),
        "Key findings": findings_text(lo, hi, vc, dg, pm, th, r0),
        "Live demo": (
            "Now our web app. Here we asked a question about Titan's revenue growth, using our VPSC method. "
            "On the left you can see the answer, 16.40 percent, and a green chip showing it matches the correct answer. "
            "The bar below it shows that all five programs agreed, and the green box confirms that every number they used is in the report. "
            "On the right, the Evidence tab highlights the exact rows the model used from the table. "
            "Other tabs show the Python code the model wrote, each vote with its grounding check, and the exact prompt we sent. "
            "So a user does not have to trust the answer blindly. They can check every step."),
        "Demo plan": (
            "Now I will show it live. Here is what you will see. "
            "First, the Overview page: our main findings, computed straight from the results, and a checklist of everything we promised in our reviews. "
            "Second, on the Ask page, I will choose a Marico question about the growth rate over nine years, run VPSC, and then paste a new table that the system has never seen. "
            "Third, the Data page shows that same Marico question next to the real page of the annual report. "
            "Fourth, on the Compare page, I will run four strategies on the same question, side by side, so you can see which ones get it right and how many tokens each uses. "
            "Fifth, the Results and Optimization pages show all our charts, including the automatic prompt tools, "
            "and the Errors page lets us open any wrong answer and see exactly what went wrong."),
        "Conclusion": (
            "To conclude. First, good prompting makes a small model on a laptop useful: asking for reasoning turns a model that is almost always wrong into one that is "
            "right most of the time. Second, letting the model write Python code is the best way to get the calculation right. "
            "Third, the main remaining problem is picking the right numbers from the report. "
            "And fourth, our grounding check can warn the user when an answer should not be trusted. "
            + ("Our main limitations are the small number of questions, one model family, and that our check does not yet confirm the exact cell. "
               "Next we would use full test sets, bigger models and a cell-level check." if has8 else "")),
        "Limitations": (
            "Every project has limits, and here are ours, with what we would do next. "
            "One: we tested about 100 questions per dataset, so our results have an uncertainty of about plus or minus 10 points. Next time we would use the full test sets. "
            "Two: we used one family of models. We would add bigger models and online models. "
            "Three: our check confirms that a number exists in the report, but not that it is the right cell — for example, it would accept last year's value by mistake. "
            "We would check the exact row and column, and let the system say 'I am not sure'. "
            "Four: our mistake types are decided by rules. We would add checking by people."),
        "Thank you & Q&A": (
            "Thank you for your attention. To sum up in one line: asking for reasoning matters most, letting the computer do the maths works best, "
            "and our check tells you when not to trust an answer. We are happy to answer your questions."),
    }
    return {k: v for k, v in sc.items() if v}


# ============================================================================================
# Document
# ============================================================================================
def spoken_form(text):
    """Turn symbols into words so the script can be said aloud."""
    text = re.sub(r"(\d)\s*–\s*(\d)", r"\1 to \2", text)
    text = re.sub(r"(\d(?:\.\d+)?)×", r"\1 times", text)
    text = text.replace("≤", "at most ").replace("→", "to").replace("CoT", "Chain-of-Thought")
    text = re.sub(r"(\d)%", r"\1 percent", text)
    return text


def find_script(scripts, title):
    for key in sorted(scripts, key=len, reverse=True):
        if title.startswith(key):
            v = scripts[key]
            return v() if callable(v) else v
    raise KeyError(f"no script for slide '{title}'")


def script_doc(review, deck, scripts, title):
    asg = deck.assignments()
    blocks, cur, spoken = [], None, {}
    for i, (n, t, who) in enumerate(asg):
        text = find_script(scripts, t)
        if who != cur:
            blocks.append(f'<h2>{who or "Last slides — not assigned (shown by the last presenter)"}</h2>')
            if cur is not None and who is not None and t != "Thank you & Q&A":
                text = f"Thank you, {FIRST[cur]}. " + text
            cur = who
        if i + 1 < len(asg) and asg[i + 1][2] != who and asg[i + 1][2] is not None:
            nt = asg[i + 1][1]
            text += f" I now hand over to {FIRST[asg[i + 1][2]]}" + (f", who will present the next part, starting with “{nt}”." if nt != "Thank you & Q&A" else ".")
        text = spoken_form(text)
        spoken[who] = spoken.get(who, 0) + len(text.split())
        secs = max(20, round(len(text.split()) / 2.3 / 5) * 5)
        blocks.append(f'<h4>Slide {n} · {t} <span style="color:#8a94a6;font-weight:400">(~{secs} s)</span></h4><p>{text}</p>')
    totals = [[name, f"{spoken.get(name, 0) / 140:.1f} min"] for name, _ in TEAM]
    if spoken.get(None):
        totals.append(["Not assigned (last slides)", f"{spoken[None] / 140:.1f} min"])
    body = (notes_head(f"Review {review}", f"Speaker script — {title}", "speaker script") +
            '<div class="oneline">Say this in your own words — do not read it out. About one minute per slide; stress the slide\'s “Key point”.</div>' +
            table(["Presenter", "Speaking time (approx.)"], totals, widths=[60, 40]) + "".join(blocks))
    return page(f"Review {review} speaker script", NOTES_CSS, body, running=f"FinReason · Review {review} · speaker script")


def r1_script():
    return script_doc(1, C.r1_deck(), R1, "Idea &amp; literature survey")


def r2_script():
    return script_doc(2, C.r2_deck(), R2, "High-level design &amp; data collection")


def r3_script():
    return script_doc(3, C.r3_deck(), r3_scripts(), "Final results &amp; demo")
