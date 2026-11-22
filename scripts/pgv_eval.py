"""TRACE-PG: calibrated selection over provenance graphs, conformal abstention, budgeted escalation,
the coverage law, view error correlations and cell-level attribution. No model calls: everything is
computed from the logged candidates of `trace` runs.

    python scripts/pgv_eval.py --freeze     # fit selectors + thresholds on DEVELOPMENT data only
    python scripts/pgv_eval.py              # apply the frozen artifacts to every setting -> paper/generated/

Development data = FinQA/TAT-QA dev (n=50) and the n=100 test samples. Held-out data is never used by
--freeze.
"""
import argparse
import json
import math
import sys
from functools import lru_cache
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from finreason.answers import score  # noqa: E402
from finreason.config import RUNS_DIR  # noqa: E402
from finreason.data import load_dataset  # noqa: E402
from finreason.pgv import synthesize, type_check  # noqa: E402
from finreason.strategies import _same_answer  # noqa: E402
from finreason.trace import W_FLAGGED, W_PROGRAM, W_SOFT, W_TEXT  # noqa: E402

OUT = ROOT / "paper" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
ART = ROOT / "artifacts" / "trace_pg.json"
DEV = ["finqa_dev_n50", "tatqa_dev_n50", "finqa_test_n100", "tatqa_test_n100"]
STAGES = [["pot_guided", "cot"], ["pot_guided", "cot", "pot_plain", "decomp"], None]   # None = all views
MODEL = "ollama-qwen3-1.7b"


# ------------------------------------------------------------------------------------------ data
def examples_for(prefix):
    ds, split, n = prefix.split("_")[0], prefix.split("_")[1], int(prefix.split("_n")[-1])
    exs = load_dataset(ds.replace("-perturbed", ""), split, n=n)
    if "perturbed" in ds:
        from finreason.perturb import perturb_dataset
        exs = perturb_dataset(exs, seed=42)
    return {e.uid: e for e in exs}


def trace_runs(model=MODEL):
    out = {}
    for p in sorted(RUNS_DIR.glob(f"*__{model}__trace__markdown__full.jsonl")):
        prefix = p.name.split("__")[0]
        recs = [json.loads(line) for line in open(p)]
        exs = examples_for(prefix)
        if len(recs) >= len(exs):
            out[prefix] = (recs, exs)
    return out


def correct(r, a):
    return a is not None and bool(score(a, r["gold"], r["question"], r["scale"])[0])


@lru_cache(maxsize=None)
def _typing(code, question, table_key, texts_key):
    table, texts = json.loads(table_key), json.loads(texts_key)
    return type_check(code, question, table, texts)


def typing_of(c, e):
    if not c["is_program"] or c["answer"] is None or isinstance(c["answer"], str):
        return None
    return _typing(c["code"], e.question, json.dumps(e.table), json.dumps(e.texts))


# ------------------------------------------------------------------------------------- features
FEATURES = ["share", "w", "n_prog_clean", "n_prog_flagged", "n_text", "cross_modal", "has_guided", "has_cot",
            "has_plain", "has_decomp", "n_type_ok", "all_type_bad", "period_ok", "orient_bad", "mixed_scale",
            "struct_agree", "n_sigs", "repaired_clean", "ungrounded", "yesno", "n_pools", "is_top",
            "n_leaves", "has_synth", "synth_only"]


@lru_cache(maxsize=None)
def _synth(code, question, table_key, texts_key):
    return tuple(a for a, _ in synthesize(code, question, json.loads(table_key), json.loads(texts_key)))


def synth_answers(cands, e):
    out = []
    for c in cands:
        if c["is_program"] and c["answer"] is not None and not isinstance(c["answer"], str):
            for a in _synth(c["code"], e.question, json.dumps(e.table), json.dumps(e.texts)):
                if not any(_same_answer(a, b) for b in out):
                    out.append(a)
    return out


def trace_weight(c):
    if c["answer"] is None:
        return 0.0
    sev = [p[1] for p in c.get("problems") or []]
    if not c["is_program"]:
        return 0.0 if sev else W_TEXT
    if not sev:
        return W_PROGRAM
    return W_FLAGGED if max(sev) >= 1.0 else W_SOFT


def candidates_at(record, stage_views):
    cands = record["extra"]["candidates"]
    if stage_views is None:
        return cands
    keep = [c for c in cands if c["view"] in stage_views]
    keep += [c for c in cands if c.get("parent") in stage_views]
    return keep


def pools_of(record, e, stage_views=None):
    """Answer pools (1% tolerance) with PGV features. Returns list of dicts."""
    cands = candidates_at(record, stage_views)
    weights = [trace_weight(c) for c in cands]
    repaired = {c.get("parent") for c, w in zip(cands, weights) if c.get("parent") and w > 0}
    weights = [0.0 if c["view"] in repaired else w for c, w in zip(cands, weights)]
    pools = []
    for c, w in zip(cands, weights):
        if c["answer"] is None:
            continue
        for p in pools:
            if _same_answer(c["answer"], p["answer"]):
                p["members"].append((c, w))
                break
        else:
            pools.append({"answer": c["answer"], "members": [(c, w)]})
    synth = synth_answers(cands, e)
    for p in pools:
        p["synth"] = any(_same_answer(a, p["answer"]) for a in synth)
    for a in synth:
        if not any(_same_answer(a, p["answer"]) for p in pools):
            pools.append({"answer": a, "members": [], "synth": True})
    total = sum(weights) or 1.0
    feats = []
    for p in pools:
        mem = p["members"]
        progs = [(c, w) for c, w in mem if c["is_program"]]
        typ = [(c, typing_of(c, e)) for c, _ in progs]
        typ = [(c, t) for c, t in typ if t is not None]
        sigs = [t.signature for _, t in typ if t.signature]
        w = sum(w for _, w in mem)
        f = {
            "answer": p["answer"], "w": w, "share": w / total,
            "n_prog_clean": sum(1 for c, _ in progs if not c.get("problems")),
            "n_prog_flagged": sum(1 for c, _ in progs if c.get("problems")),
            "n_text": sum(1 for c, _ in mem if not c["is_program"] and not c.get("problems")),
            "cross_modal": float(any(c["is_program"] for c, _ in mem) and any(not c["is_program"] for c, _ in mem)),
            "has_guided": float(any(c["view"] == "pot_guided" for c, _ in mem)),
            "has_cot": float(any(c["view"] == "cot" for c, _ in mem)),
            "has_plain": float(any(c["view"] == "pot_plain" for c, _ in mem)),
            "has_decomp": float(any(c["view"] == "decomp" for c, _ in mem)),
            "n_type_ok": sum(t.type_ok for _, t in typ),
            "all_type_bad": float(bool(typ) and not any(t.type_ok for _, t in typ)),
            "period_ok": float(np.mean([t.period_ok for _, t in typ])) if typ else 1.0,
            "orient_bad": float(any(t.orientation_ok is False for _, t in typ)),
            "mixed_scale": float(any(t.mixed_scale for _, t in typ)),
            "struct_agree": max([sigs.count(s) for s in set(sigs)] or [0]),
            "n_sigs": len(set(sigs)),
            "repaired_clean": float(any(c.get("parent") and not c.get("problems") for c, _ in progs)),
            "ungrounded": float(any(t.n_ungrounded for _, t in typ)),
            "yesno": float(isinstance(p["answer"], str)),
            "n_leaves": float(np.mean([t.n_leaves for _, t in typ])) if typ else 0.0,
            "has_synth": float(p["synth"]), "synth_only": float(p["synth"] and not mem),
            "members": mem, "typings": typ,
        }
        feats.append(f)
    order = sorted(range(len(feats)), key=lambda i: -feats[i]["w"])
    for rank, i in enumerate(order):
        feats[i]["is_top"] = float(rank == 0)
        feats[i]["n_pools"] = len(feats)
    return feats


def stage_cost(record, stage_views):
    cs = candidates_at(record, stage_views)
    return (sum(c["cost"]["prompt_tokens"] + c["cost"]["completion_tokens"] for c in cs),
            sum(c["cost"]["calls"] for c in cs))


# ------------------------------------------------------------------------------------- selector
def matrix(pools):
    return np.array([[float(p[k]) for k in FEATURES] for p in pools])


class Selector:
    """Logistic model P(pool is correct | provenance-graph features), standardized inputs."""

    def __init__(self, coef=None, intercept=0.0, mean=None, std=None):
        self.coef, self.intercept, self.mean, self.std = coef, intercept, mean, std

    def fit(self, X, y, C):
        from sklearn.linear_model import LogisticRegression
        self.mean, self.std = X.mean(0), X.std(0) + 1e-9
        m = LogisticRegression(C=C, max_iter=5000).fit((X - self.mean) / self.std, y)
        self.coef, self.intercept = m.coef_[0], float(m.intercept_[0])
        return self

    def prob(self, X):
        z = ((X - self.mean) / self.std) @ self.coef + self.intercept
        return 1 / (1 + np.exp(-z))

    def to_json(self):
        return {"coef": list(map(float, self.coef)), "intercept": self.intercept,
                "mean": list(map(float, self.mean)), "std": list(map(float, self.std)), "features": FEATURES}

    @classmethod
    def from_json(cls, d):
        return cls(np.array(d["coef"]), d["intercept"], np.array(d["mean"]), np.array(d["std"]))


def select(pools, sel):
    """Returns (answer, confidence)."""
    if not pools:
        return None, 0.0
    p = sel.prob(matrix(pools))
    i = int(np.argmax(p))
    return pools[i]["answer"], float(p[i])


def heuristic(pools):
    if not pools:
        return None, 0.0
    best = max(pools, key=lambda p: p["w"])
    return best["answer"], best["share"]


def pgv_rules(pools):
    """Deterministic PGV (no learning): programs with a typed violation lose their vote."""
    if not pools:
        return None, 0.0
    def w(p):
        bad = p["orient_bad"] or p["mixed_scale"] or p["period_ok"] < 1 or p["all_type_bad"]
        return p["w"] * (0.25 if bad and p["n_prog_clean"] else 1.0)
    best = max(pools, key=w)
    tot = sum(w(p) for p in pools) or 1.0
    return best["answer"], w(best) / tot


# --------------------------------------------------------------------------- conformal risk control
def crc_threshold(conf, wrong, alpha):
    """Conformal risk control (loss = answered and wrong, monotone in the threshold): the smallest
    threshold whose adjusted empirical risk is <= alpha. Guarantees E[loss] <= alpha on exchangeable data."""
    conf, wrong = np.asarray(conf), np.asarray(wrong, dtype=float)
    n = len(conf)
    for lam in np.unique(np.concatenate([[0.0], conf, [1.01]])):
        risk = np.mean((conf >= lam) * wrong)
        if (n * risk + 1) / (n + 1) <= alpha:
            return float(lam)
    return 1.01


# ------------------------------------------------------------------------------------- freeze
def build(runs, prefixes, stage=None):
    rows = []
    for prefix in prefixes:
        recs, exs = runs[prefix]
        for r in recs:
            e = exs[r["uid"]]
            for p in pools_of(r, e, STAGES[stage] if stage is not None else None):
                rows.append((prefix, r["uid"], p, correct(r, p["answer"])))
    return rows


def freeze():
    runs = trace_runs()
    missing = [p for p in DEV if p not in runs]
    assert not missing, f"development runs missing: {missing}"
    art = {"development": DEV, "stages": {}}
    for k in range(3):
        rows = build(runs, DEV, k)
        X = matrix([p for _, _, p, _ in rows])
        y = np.array([c for *_, c in rows], dtype=int)
        qid = np.array([f"{a}|{b}" for a, b, _, _ in rows])
        # choose C by 5-fold grouped cross-validation on question accuracy
        uq = np.unique(qid)
        rng = np.random.default_rng(0)
        folds = {q: i % 5 for i, q in enumerate(rng.permutation(uq))}
        fold = np.array([folds[q] for q in qid])
        best = None
        for C in [0.01, 0.03, 0.1, 0.3, 1.0, 3.0]:
            oof = np.zeros(len(y))
            for f in range(5):
                tr = fold != f
                oof[~tr] = Selector().fit(X[tr], y[tr], C).prob(X[~tr])
            acc, confs, wrongs = [], [], []
            for q in uq:
                idx = np.where(qid == q)[0]
                i = idx[np.argmax(oof[idx])]
                acc.append(y[i])
                confs.append(oof[i])
                wrongs.append(1 - y[i])
            score_ = np.mean(acc)
            if best is None or score_ > best[0] + 1e-9:
                best = (score_, C, confs, wrongs)
        sel = Selector().fit(X, y, best[1])
        entry = {"C": best[1], "cv_accuracy": best[0], "selector": sel.to_json()}
        if k == 2:   # conformal thresholds from out-of-fold confidences of the full selector
            entry["crc"] = {str(a): crc_threshold(best[2], best[3], a) for a in (0.05, 0.10, 0.15, 0.20, 0.25)}
            heur = []
            for prefix in DEV:
                recs, exs = runs[prefix]
                heur += [correct(r, heuristic(pools_of(r, exs[r["uid"]]))[0]) for r in recs]
            entry["cv_heuristic_accuracy"] = float(np.mean(heur))
        art["stages"][str(k)] = entry
        print(f"stage {k}: C={best[1]} grouped-CV accuracy {best[0]:.3f}")
    # escalation thresholds: pick (tau1, tau2) on development data maximizing accuracy - lambda*calls
    sels = [Selector.from_json(art["stages"][str(k)]["selector"]) for k in range(3)]
    grid = [0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.01]
    res = []
    for t1 in grid:
        for t2 in grid:
            accs, calls = [], []
            for prefix in DEV:
                recs, exs = runs[prefix]
                for r in recs:
                    a, cst = escalate(r, exs[r["uid"]], sels, (t1, t2))
                    accs.append(correct(r, a))
                    calls.append(cst[1])
            res.append((np.mean(accs), np.mean(calls), t1, t2))
    full_acc = max(a for a, *_ in res)
    # cheapest policy within one point of the best development accuracy
    ok = [x for x in res if x[0] >= full_acc - 0.01]
    acc, calls, t1, t2 = min(ok, key=lambda x: x[1])
    art["escalation"] = {"tau": [t1, t2], "dev_accuracy": acc, "dev_calls": calls,
                         "grid": [list(map(float, x)) for x in res]}
    print(f"escalation tau=({t1},{t2}) dev acc {acc:.3f} calls {calls:.2f}")
    art["frozen_at"] = __import__("datetime").datetime.now().isoformat(timespec="seconds")
    ART.write_text(json.dumps(art, indent=1))
    print("frozen ->", ART)


def escalate(record, e, sels, taus):
    for k in range(3):
        pools = pools_of(record, e, STAGES[k])
        a, conf = select(pools, sels[k])
        if k < 2 and conf >= taus[k]:
            return a, stage_cost(record, STAGES[k])
    return a, stage_cost(record, None)


# ------------------------------------------------------------------------------------- analyses
def coverage_law(votes_by_q, golds):
    """Beta-binomial fit of per-question success probability from K exchangeable samples."""
    from scipy.optimize import minimize
    from scipy.special import betaln, gammaln
    s = np.array([sum(v) for v in votes_by_q])
    K = len(votes_by_q[0])

    def nll(x):
        a, b = np.exp(x)
        return -np.sum(gammaln(K + 1) - gammaln(s + 1) - gammaln(K - s + 1) + betaln(s + a, K - s + b) - betaln(a, b))
    r = minimize(nll, [0.0, 0.0], method="Nelder-Mead")
    a, b = np.exp(r.x)
    rho = 1 / (a + b + 1)
    pred = lambda k: 1 - math.exp(betaln(a, b + k) - betaln(a, b))
    emp = {}
    for k in range(1, K + 1):
        emp[k] = np.mean([np.mean([any(v[i] for i in sub) for sub in combinations(range(K), k)]) for v in votes_by_q])
    return {"alpha": a, "beta": b, "rho": rho, "pred": {k: pred(k) for k in (1, 2, 3, 4, 5, 10, 20, 50)},
            "emp": emp}


def k_needed(fit, target):
    for k in range(1, 100000):
        if 1 - math.exp(__import__("scipy.special", fromlist=["betaln"]).betaln(fit["alpha"], fit["beta"] + k)
                        - __import__("scipy.special", fromlist=["betaln"]).betaln(fit["alpha"], fit["beta"])) >= target:
            return k
    return None


def gold_rows(e):
    return {int(f.split("_")[1]) for f in e.gold_facts if f.startswith("table_")}


def attribution(prog_typing, e):
    rows = {int(r.split("[")[1].split(",")[0]) for r in prog_typing.refs if r.startswith("T[")}
    g = gold_rows(e)
    if not g or not rows:
        return None
    hit = rows & g
    return len(hit) / len(rows), len(hit) / len(g)


def chosen_program(pools, answer):
    for p in pools:
        if p["answer"] is answer or (answer is not None and _same_answer(p["answer"], answer)):
            progs = sorted(p["typings"], key=lambda ct: (bool(ct[0].get("problems")), -ct[1].n_table))
            return progs[0][1] if progs else None
    return None


def label(prefix):
    ds, split, n = prefix.split("_")[0], prefix.split("_")[1], prefix.split("_n")[-1]
    name = {"finqa": "FinQA", "tatqa": "TAT-QA", "indian": "IndAR", "finqa-perturbed": "FinQA-pert"}[ds]
    tag = {"heldout": "H", "test": "D" if ds in ("finqa", "tatqa") else "", "dev": "dev"}[split]
    return f"{name}{('$^{' + tag + '}$') if tag else ''} ({n})"


def evaluate():
    art = json.loads(ART.read_text())
    sels = [Selector.from_json(art["stages"][str(k)]["selector"]) for k in range(3)]
    taus = art["escalation"]["tau"]
    runs = trace_runs()
    rows, attr_rows, crc_rows, frontier, perq = [], [], [], [], []
    for prefix, (recs, exs) in runs.items():
        part = "development" if prefix in DEV else "evaluation"
        res = {"TRACE": [], "TRACE-PG (rules)": [], "TRACE-PG": [], "TRACE-PG (escalated)": []}
        confs, wrongs, calls_full, calls_esc, toks_full, toks_esc = [], [], [], [], [], []
        attr = {"PoT (plain)": [], "TRACE": [], "TRACE-PG": []}
        for r in recs:
            e = exs[r["uid"]]
            pools = pools_of(r, e)
            a_h, _ = heuristic(pools)
            a_r, _ = pgv_rules(pools)
            a_s, conf = select(pools, sels[2])
            a_e, cst = escalate(r, e, sels, taus)
            for k, a in zip(res, (a_h, a_r, a_s, a_e)):
                res[k].append(correct(r, a))
            confs.append(conf)
            wrongs.append(not correct(r, a_s))
            t_full, c_full = stage_cost(r, None)
            perq.append({"prefix": prefix, "uid": r["uid"], "strategy": "trace_pg", "correct": correct(r, a_s),
                         "tokens": t_full, "calls": c_full, "confidence": conf})
            perq.append({"prefix": prefix, "uid": r["uid"], "strategy": "trace_pg_esc", "correct": correct(r, a_e),
                         "tokens": cst[0], "calls": cst[1], "confidence": conf})
            toks_full.append(t_full); calls_full.append(c_full); toks_esc.append(cst[0]); calls_esc.append(cst[1])
            plain = next((c for c in r["extra"]["candidates"] if c["view"] == "pot_plain"), None)
            for name, ty in [("PoT (plain)", typing_of(plain, e) if plain else None),
                             ("TRACE", chosen_program(pools, a_h)), ("TRACE-PG", chosen_program(pools, a_s))]:
                if ty is not None and (at := attribution(ty, e)):
                    attr[name].append(at)
        row = {"setting": label(prefix), "prefix": prefix, "part": part, "n": len(recs)}
        for k, v in res.items():
            row[k] = float(np.mean(v))
        row.update(tokens_full=np.mean(toks_full), calls_full=np.mean(calls_full), tokens_escalated=np.mean(toks_esc),
                   calls_escalated=np.mean(calls_esc))
        rows.append(row)
        for name, v in attr.items():
            if v:
                attr_rows.append({"setting": label(prefix), "part": part, "method": name, "questions": len(v),
                                  "precision": np.mean([p for p, _ in v]), "recall": np.mean([q for _, q in v]),
                                  "exact": np.mean([p == 1 and q == 1 for p, q in v])})
        confs, wrongs = np.array(confs), np.array(wrongs, dtype=float)
        for a, lam in art["stages"]["2"]["crc"].items():
            ans = confs >= lam
            crc_rows.append({"setting": label(prefix), "part": part, "alpha": float(a), "threshold": lam,
                             "coverage": ans.mean(), "risk (answered & wrong)": float(np.mean(ans * wrongs)),
                             "selective accuracy": float(1 - wrongs[ans].mean()) if ans.any() else float("nan")})
        for t1, t2 in [(x, y) for x in (0.5, 0.7, 0.8, 0.9, 0.95, 1.01) for y in (0.5, 0.8, 0.9, 1.01)]:
            acc, cl = [], []
            for r in recs:
                a, cst = escalate(r, exs[r["uid"]], sels, (t1, t2))
                acc.append(correct(r, a)); cl.append(cst[1])
            frontier.append({"setting": label(prefix), "prefix": prefix, "tau1": t1, "tau2": t2,
                             "accuracy": np.mean(acc), "calls": np.mean(cl)})
    pd.DataFrame(rows).to_csv(OUT / "pgv_results.csv", index=False)
    pd.DataFrame(perq).to_csv(OUT / "trace_pg_per_question.csv", index=False)
    pd.DataFrame(attr_rows).to_csv(OUT / "attribution.csv", index=False)
    pd.DataFrame(crc_rows).to_csv(OUT / "conformal.csv", index=False)
    pd.DataFrame(frontier).to_csv(OUT / "escalation_frontier.csv", index=False)
    analyses(runs)
    fig_coverage_law(runs)
    tex(pd.DataFrame(rows), pd.DataFrame(attr_rows), pd.DataFrame(crc_rows), art)
    print(pd.DataFrame(rows).to_markdown(index=False, floatfmt=".3f"))
    print(pd.DataFrame(crc_rows).to_markdown(index=False, floatfmt=".3f"))
    print(pd.DataFrame(attr_rows).to_markdown(index=False, floatfmt=".3f"))


def analyses(runs):
    """Coverage law (same-prompt samples) and the error-correlation matrix of TRACE's views."""
    law_rows = []
    for p in sorted(RUNS_DIR.glob(f"*__{MODEL}__pot_sc__markdown__full.jsonl")) + \
            sorted(RUNS_DIR.glob(f"*__{MODEL}__sc_cot__markdown__full.jsonl")):
        prefix, strategy = p.name.split("__")[0], p.name.split("__")[2]
        if "perturbed" in prefix or prefix.startswith("indian"):
            continue
        recs = [json.loads(line) for line in open(p)]
        # samples 1..4 are i.i.d. at T=0.7 (sample 0 is greedy), so they are exchangeable
        votes = [[correct(r, a) for a in r["extra"]["votes"][1:5]] for r in recs if len(r["extra"]["votes"]) >= 5]
        if len(votes) < 40:
            continue
        fit = coverage_law(votes, None)
        law_rows.append({"setting": label(prefix), "samples": "PoT" if strategy == "pot_sc" else "CoT",
                         "rho": fit["rho"], "alpha": fit["alpha"], "beta": fit["beta"],
                         **{f"emp_K{k}": v for k, v in fit["emp"].items()},
                         **{f"pred_K{k}": v for k, v in fit["pred"].items()},
                         "K_for_75": k_needed(fit, 0.75), "K_for_90": k_needed(fit, 0.90)})
    pd.DataFrame(law_rows).to_csv(OUT / "coverage_law.csv", index=False)
    sig_rows = []
    for prefix, (recs, exs) in runs.items():
        cnt = {k: [0, 0] for k in ("type", "period", "orientation", "units", "any")}
        progs = wrong = lifted = synth_q = synth_ok = 0
        for r in recs:
            e = exs[r["uid"]]
            ok_ = lambda a: correct(r, a)
            for c in r["extra"]["candidates"]:
                t = typing_of(c, e)
                if t is None or c.get("parent"):
                    continue
                progs += 1
                lifted += t.liftable
                w = not ok_(c["answer"])
                wrong += w
                flags = {"type": not t.type_ok, "period": t.period_ok < 1, "orientation": t.orientation_ok is False,
                         "units": t.mixed_scale}
                flags["any"] = any(flags.values())
                for k, f in flags.items():
                    if f:
                        cnt[k][0] += 1
                        cnt[k][1] += w
            syn = synth_answers(r["extra"]["candidates"], e)
            if syn:
                synth_q += 1
                synth_ok += any(ok_(a) for a in syn)
        sig_rows.append({"setting": label(prefix), "part": "development" if prefix in DEV else "evaluation",
                         "programs": progs, "lifted": lifted / max(1, progs), "base_wrong": wrong / max(1, progs),
                         **{f"{k}_flags": v[0] for k, v in cnt.items()},
                         **{f"{k}_precision": (v[1] / v[0] if v[0] else float("nan")) for k, v in cnt.items()},
                         "synth_fires": synth_q / len(recs), "synth_correct": synth_ok / max(1, synth_q)})
    pd.DataFrame(sig_rows).to_csv(OUT / "pgv_signals.csv", index=False)
    views = ["pot_guided", "pot_guided_t", "pot_plain", "cot", "cot_t", "decomp"]
    corr_rows = []
    for prefix, (recs, exs) in runs.items():
        M = []
        for r in recs:
            byv = {c["view"]: c for c in r["extra"]["candidates"]}
            M.append([float(correct(r, byv[v]["answer"])) if v in byv else np.nan for v in views])
        M = np.array(M)
        C = pd.DataFrame(1 - M, columns=views).corr()   # correlation of error indicators
        for i, a in enumerate(views):
            for b in views[i + 1:]:
                corr_rows.append({"setting": label(prefix), "a": a, "b": b, "error_corr": C.loc[a, b],
                                  "acc_a": np.nanmean(M[:, i]), "acc_b": np.nanmean(M[:, views.index(b)])})
    pd.DataFrame(corr_rows).to_csv(OUT / "view_correlation.csv", index=False)


def kfmt(k):
    return "$>10^5$" if k != k or k is None else (f"{int(k):,}" if k < 1e5 else "$>10^4$")


def fig_coverage_law(runs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from scipy.special import betaln
    law = pd.read_csv(OUT / "coverage_law.csv")
    keep = [s for s in law.setting.unique()]
    if not keep:
        return
    fig, axes = plt.subplots(1, len(keep[:2]), figsize=(3.5 * len(keep[:2]), 2.5), squeeze=False)
    for ax, setting in zip(axes[0], keep[:2]):
        for _, r in law[law.setting == setting].iterrows():
            ks = np.arange(1, 51)
            pred = [1 - math.exp(betaln(r.alpha, r.beta + k) - betaln(r.alpha, r.beta)) for k in ks]
            col = "#c58b3f" if r.samples == "PoT" else "#5b8db8"
            ax.plot(ks, np.array(pred) * 100, color=col, lw=1.4, label=f"{r.samples} samples (fit, $\\rho$={r.rho:.2f})")
            ax.scatter([1, 2, 3, 4], [100 * r[f"emp_K{k}"] for k in (1, 2, 3, 4)], color=col, s=12, zorder=3)
        prefix = next((p for p in runs if label(p) == setting), None)
        if prefix:
            recs, _ = runs[prefix]
            cov = np.mean([any(correct(r, c["answer"]) for c in r["extra"]["candidates"]) for r in recs])
            ax.axhline(cov * 100, color="#1a7f5a", ls="--", lw=1.2, label="TRACE views (6 calls)")
        ax.set_xscale("log")
        ax.set_xlabel("same-prompt samples K", fontsize=8)
        ax.set_ylabel("coverage (%)", fontsize=8)
        ax.set_title(setting.replace("$^{D}$", " (dev)"), fontsize=9)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=6, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT / "coverage_law.pdf")
    fig.savefig(OUT / "coverage_law.png", dpi=200)


def tex(res, attr, crc, art):
    ev = res[res.part == "evaluation"]
    dv = res[res.part == "development"]
    lines = ["\\begin{tabular}{lcccc|cc}", "\\toprule",
             "Setting & \\textsc{Trace} & PG-rules & \\textsc{Trace}-PG & PG-esc. & Calls (full) & Calls (esc.) \\\\", "\\midrule"]
    for part, d in (("Evaluation", ev), ("Development (5-fold CV for the selector)", dv)):
        if len(d):
            lines.append(f"\\multicolumn{{7}}{{l}}{{\\emph{{{part}}}}} \\\\")
        for _, r in d.iterrows():
            vals = [r["TRACE"], r["TRACE-PG (rules)"], r["TRACE-PG"], r["TRACE-PG (escalated)"]]
            best = max(vals)
            cells = [(f"\\textbf{{{100 * v:.1f}}}" if abs(v - best) < 1e-9 else f"{100 * v:.1f}") for v in vals]
            lines.append(f"{r['setting']} & " + " & ".join(cells) + f" & {r.calls_full:.1f} & {r.calls_escalated:.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "pgv_table.tex").write_text("\n".join(lines) + "\n")
    # conformal
    lines = ["\\begin{tabular}{llccc}", "\\toprule", "Setting & $\\alpha$ & Coverage & Risk & Sel.\\ acc. \\\\", "\\midrule"]
    for _, r in crc[(crc.part == "evaluation") & crc.alpha.isin([0.1, 0.2])].iterrows():
        lines.append(f"{r.setting} & {r.alpha:.2f} & {100 * r.coverage:.1f} & {100 * r['risk (answered & wrong)']:.1f} & "
                     f"{100 * r['selective accuracy']:.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "conformal_table.tex").write_text("\n".join(lines) + "\n")
    # attribution
    lines = ["\\begin{tabular}{llccc}", "\\toprule", "Setting & Method & Precision & Recall & Exact \\\\", "\\midrule"]
    for _, r in attr[attr.part == "evaluation"].iterrows():
        lines.append(f"{r.setting} & {r.method} & {100 * r.precision:.1f} & {100 * r.recall:.1f} & {100 * r.exact:.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "attribution_table.tex").write_text("\n".join(lines) + "\n")
    # coverage law
    law = pd.read_csv(OUT / "coverage_law.csv")
    if len(law):
        lines = ["\\begin{tabular}{llcccccc}", "\\toprule",
                 "Setting & Samples & $\\hat\\rho$ & Cov@1 & Cov@4 (emp./pred.) & Cov@20 & $K_{75\\%}$ & $K_{90\\%}$ \\\\", "\\midrule"]
        for _, r in law.iterrows():
            lines.append(f"{r.setting} & {r.samples} & {r.rho:.2f} & {100 * r.emp_K1:.1f} & {100 * r.emp_K4:.1f} / {100 * r.pred_K4:.1f} & "
                         f"{100 * r.pred_K20:.1f} & {kfmt(r.K_for_75)} & {kfmt(r.K_for_90)} \\\\")
        lines += ["\\bottomrule", "\\end{tabular}"]
        (OUT / "coverage_law_table.tex").write_text("\n".join(lines) + "\n")
    sig = pd.read_csv(OUT / "pgv_signals.csv")
    lines = ["\\begin{tabular}{lccccccc}", "\\toprule",
             "Setting & Lifted & Base & Type & Period & Orient. & Units & Compl. (fires/acc.) \\\\", "\\midrule"]
    for _, r in sig.iterrows():
        cell = lambda k: (f"{100 * r[k + '_precision']:.0f} ({int(r[k + '_flags'])})" if r[k + "_flags"] else "--")
        lines.append(f"{r.setting} & {100 * r.lifted:.1f} & {100 * r.base_wrong:.0f} & {cell('type')} & {cell('period')} & "
                     f"{cell('orientation')} & {cell('units')} & {100 * r.synth_fires:.0f} / {100 * r.synth_correct:.0f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "pgv_signals_table.tex").write_text("\n".join(lines) + "\n")
    corr = pd.read_csv(OUT / "view_correlation.csv")
    if len(corr):
        within = corr[((corr.a == "pot_guided") & (corr.b == "pot_guided_t")) | ((corr.a == "cot") & (corr.b == "cot_t"))]
        cross = corr[corr.a.str.startswith("pot") & corr.b.isin(["cot", "cot_t", "decomp"])]
        summary = corr.assign(kind=np.where(corr.index.isin(within.index), "same prompt",
                                            np.where(corr.index.isin(cross.index), "program vs text", "other")))
        summary.groupby(["setting", "kind"]).error_corr.mean().unstack().to_csv(OUT / "view_correlation_summary.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", action="store_true")
    args = ap.parse_args()
    freeze() if args.freeze else evaluate()
