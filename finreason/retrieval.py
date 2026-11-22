"""Hybrid evidence retrieval (BM25 + dense embeddings with FAISS) and prompt-context building."""
import re
import threading

import numpy as np

from .config import EMBED_MODEL
from .tables import row_to_text, serialize


def evidence_units(example):
    """Split a report page into retrievable units: one per table row and one per sentence.
    Unit ids follow FinQA's convention: 'table_i' (row i, header is row 0) and 'text_j'."""
    units = []
    if example.table:
        header = [str(c) for c in example.table[0]]
        for i, row in enumerate(example.table[1:], start=1):
            units.append((f"table_{i}", row_to_text(header, [str(c) for c in row])))
    for j, sentence in enumerate(example.texts):
        if sentence.strip():
            units.append((f"text_{j}", sentence))
    return units


def tokenize(text):
    return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower())


class HybridRetriever:
    """Ranks evidence units with BM25 (keyword match) and a sentence-embedding model (meaning
    match), then fuses the two rankings with Reciprocal Rank Fusion."""

    def __init__(self, model_name=EMBED_MODEL, rrf_k=60):
        self.model_name = model_name
        self.rrf_k = rrf_k
        self._encoder = None
        self._lock = threading.Lock()

    @property
    def encoder(self):
        with self._lock:   # load the embedding model only once, when first needed
            if self._encoder is None:
                from sentence_transformers import SentenceTransformer
                self._encoder = SentenceTransformer(self.model_name, device="cpu")
        return self._encoder

    def bm25_ranking(self, question, texts):
        from rank_bm25 import BM25Okapi
        bm25 = BM25Okapi([tokenize(t) or ["_"] for t in texts])
        scores = bm25.get_scores(tokenize(question))
        return list(np.argsort(-scores, kind="stable"))

    def dense_ranking(self, question, texts):
        vectors = self.encoder.encode(texts, normalize_embeddings=True).astype("float32")
        query = self.encoder.encode([question], normalize_embeddings=True).astype("float32")
        import faiss   # imported after torch has loaded (see finreason/__init__.py)
        index = faiss.IndexFlatIP(vectors.shape[1])   # inner product = cosine on unit vectors
        index.add(vectors)
        _, order = index.search(query, len(texts))
        return list(order[0])

    def retrieve(self, question, units, k=5, method="hybrid"):
        """Return the top-k units as (unit_id, text, score), best first."""
        if not units:
            return []
        texts = [text for _, text in units]
        rankings = []
        if method in ("bm25", "hybrid"):
            rankings.append(self.bm25_ranking(question, texts))
        if method in ("dense", "hybrid"):
            rankings.append(self.dense_ranking(question, texts))
        fused = np.zeros(len(units))
        for ranking in rankings:
            for rank, idx in enumerate(ranking):
                fused[idx] += 1.0 / (self.rrf_k + rank + 1)
        best = np.argsort(-fused, kind="stable")[:k]
        return [(units[i][0], units[i][1], float(fused[i])) for i in best]


def recall_at_k(retrieved_ids, gold_ids):
    """Fraction of gold evidence units that appear in the retrieved set."""
    if not gold_ids:
        return None
    return len(set(retrieved_ids) & set(gold_ids)) / len(set(gold_ids))


def build_context(example, fmt="markdown", mode="full", retriever=None, k=5):
    """Text given to the model. mode='full' uses the whole table and all text;
    mode='retrieved' keeps the header plus the top-k retrieved rows/sentences in document order."""
    if mode == "full":
        table, texts = example.table, example.texts
        retrieved = None
    else:
        retrieved = retriever.retrieve(example.question, evidence_units(example), k=k)
        ids = {uid for uid, _, _ in retrieved}
        rows = sorted(int(u.split("_")[1]) for u in ids if u.startswith("table_"))
        sents = sorted(int(u.split("_")[1]) for u in ids if u.startswith("text_"))
        table = [example.table[0]] + [example.table[i] for i in rows] if rows else []
        texts = [example.texts[j] for j in sents]
    parts = []
    if table:
        parts.append(f"Table:\n{serialize(table, fmt)}")
    if texts:
        parts.append("Text:\n" + "\n".join(t for t in texts if t.strip()))
    return "\n\n".join(parts), retrieved
