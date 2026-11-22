"""Load FinQA, TAT-QA and the Indian annual-report set into one common Example format."""
import json
import random
import re
from dataclasses import dataclass, field

from .config import DATA_INDIAN, DATA_RAW


@dataclass
class Example:
    uid: str
    dataset: str
    question: str
    table: list                # list of rows; each row is a list of cell strings; row 0 is the header
    texts: list                # sentences / paragraphs around the table, in document order
    gold: object               # float, or the string "yes" / "no"
    gold_program: str = ""     # FinQA program, TAT-QA derivation or Indian-set formula
    n_steps: int = 1           # number of arithmetic operations needed
    evidence: str = "table"    # where the evidence is: "table", "text" or "table-text"
    scale: str = ""            # unit of the gold answer ("percent", "million", ...) when known
    gold_facts: list = field(default_factory=list)   # gold evidence ids such as "table_3" or "text_5"
    meta: dict = field(default_factory=dict)


def _evidence_type(fact_ids):
    has_table = any(f.startswith("table") for f in fact_ids)
    has_text = any(f.startswith("text") for f in fact_ids)
    if has_table and has_text:
        return "table-text"
    return "text" if has_text else "table"


def count_operations(expression):
    """Count + - * / ** operators in a derivation such as '(1,568.6-1,571.7)/1,571.7 * 100'."""
    expr = expression.replace(",", "").replace("**", "^")   # a power counts as one operation
    expr = re.sub(r"(?<![\d)\s])\s*-(?=\s*\d)", "", expr)   # drop unary minus signs
    return max(1, len(re.findall(r"[-+*/^]", expr)))


def load_finqa(split):
    raw = json.load(open(DATA_RAW / "finqa" / f"{split}.json"))
    examples = []
    for doc in raw:
        qa = doc["qa"]
        facts = list(qa.get("gold_inds", {}).keys())
        gold = qa["exe_ans"]
        gold = gold.strip().lower() if isinstance(gold, str) else float(gold)
        examples.append(Example(
            uid=doc["id"], dataset="finqa", question=qa["question"],
            table=doc["table"], texts=doc["pre_text"] + doc["post_text"],
            gold=gold, gold_program=qa["program"], n_steps=len(qa["steps"]),
            evidence=_evidence_type(facts), gold_facts=facts,
            meta={"filename": doc["filename"]},
        ))
    return examples


TATQA_FILES = {
    "train": "tatqa_dataset_train.json",
    "dev": "tatqa_dataset_dev.json",
    "test": "tatqa_dataset_test_gold.json",
}


def load_tatqa(split):
    """Load only the arithmetic questions of TAT-QA (the numerical-reasoning subset)."""
    raw = json.load(open(DATA_RAW / "tatqa" / TATQA_FILES[split]))
    examples = []
    for doc in raw:
        paragraphs = sorted(doc["paragraphs"], key=lambda p: p["order"])
        texts = [p["text"] for p in paragraphs]
        order_to_index = {str(p["order"]): i for i, p in enumerate(paragraphs)}
        for q in doc["questions"]:
            if q["answer_type"] != "arithmetic":
                continue
            try:
                gold = float(q["answer"])
            except (TypeError, ValueError):   # a few train answers are dates, not numbers
                continue
            facts = set()
            mappings = q.get("mappings") or []
            if isinstance(mappings, dict):
                mappings = [mappings]
            for mapping in mappings:
                for key, value in mapping.items():
                    if key == "table":
                        facts.add(f"table_{value[0]}")
            for order in q.get("rel_paragraphs", []):
                if str(order) in order_to_index:
                    facts.add(f"text_{order_to_index[str(order)]}")
            examples.append(Example(
                uid=q["uid"], dataset="tatqa", question=q["question"],
                table=doc["table"]["table"], texts=texts, gold=gold,
                gold_program=q["derivation"], n_steps=count_operations(q["derivation"]),
                evidence={"table": "table", "text": "text"}.get(q["answer_from"], "table-text"),
                scale=q["scale"], gold_facts=sorted(facts),
            ))
    return examples


def load_indian(split="test"):
    """Load the curated Indian annual-report questions (data/indian/indian_set.jsonl)."""
    examples = []
    for line in open(DATA_INDIAN / "indian_set.jsonl", encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        gold = r["gold"]
        gold = gold.strip().lower() if isinstance(gold, str) else float(gold)
        examples.append(Example(
            uid=r["uid"], dataset="indian", question=r["question"], table=r["table"],
            texts=r.get("texts", []), gold=gold, gold_program=r["formula"],
            n_steps=count_operations(r["formula"]), evidence=r.get("evidence", "table"),
            scale=r.get("scale", ""), gold_facts=r.get("gold_facts", []),
            meta={"company": r["company"], "source": r["source"], "page": r.get("page"),
                  "verified": r.get("verified", False)},
        ))
    return examples


LOADERS = {"finqa": load_finqa, "tatqa": load_tatqa, "indian": load_indian}


def load_dataset(name, split="test", n=None, seed=42):
    """Load a dataset split; if n is given, return a fixed random sample of n examples.
    split="heldout" is the test split minus the fixed n=100 sample used during development, so a
    held-out sample never shares a question with the development sample."""
    if split == "heldout":
        used = {e.uid for e in load_dataset(name, "test", n=100, seed=seed)}
        examples = [e for e in LOADERS[name]("test") if e.uid not in used]
    else:
        examples = LOADERS[name](split)
    if n is not None and n < len(examples):
        indices = sorted(random.Random(seed).sample(range(len(examples)), n))
        examples = [examples[i] for i in indices]
    return examples
