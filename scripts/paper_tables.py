"""Every number, table and figure of the TRACE paper, computed from results/runs/*.jsonl.

    python scripts/paper_tables.py      # -> paper/generated/*.tex, *.csv, figures, numbers.json
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from finreason.answers import score  # noqa: E402
from finreason.config import RUNS_DIR  # noqa: E402
from finreason.metrics import bootstrap_ci, holm, mcnemar  # noqa: E402
from finreason.strategies import _same_answer  # noqa: E402
from trace_replay import VARIANTS, decide, oracle, risk_coverage  # noqa: E402

OUT = ROOT / "paper" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
NAMES = {"cot_fs": "CoT (few-shot)", "pot_fs": "PoT", "sc_cot": "CoT-SC (5)", "pot_sc": "PoT-SC (5)",
         "vpsc": "VPSC [prior]", "vpsc2": "VPSC-v2", "trace": "TRACE (full)",
         "trace_adaptive": "TRACE (adaptive)", "trace_pg": "TRACE-PG", "trace_pg_esc": "TRACE-PG (escalated)"}
ORDER = list(NAMES)
NUMBERS = {}


def run_path(prefix, model, strategy):
    m = model.replace(":", "-")
    p = RUNS_DIR / f"{prefix}__ollama-{m}__{strategy}__markdown__full.jsonl"
    return p if p.exists() else None


def load(path):
    return {json.loads(line)["uid"]: json.loads(line) for line in open(path)}


def ok(r, a):
    return a is not None and bool(score(a, r["gold"], r["question"], r["scale"])[0])


def expected_n(prefix):
    from finreason.data import load_dataset
    from finreason.perturb import perturb_dataset
    ds, split, n = prefix.split("_")[0], prefix.split("_")[1], int(prefix.split("_n")[-1])
    examples = load_dataset(ds.replace("-perturbed", ""), split, n=n)
    return len(perturb_dataset(examples, seed=42)) if "perturbed" in ds else len(examples)


def settings():
    """(label, prefix, model) for every setting that has a complete TRACE run."""
    out = []
    for p in sorted(RUNS_DIR.glob("*__trace__markdown__full.jsonl")):
        prefix, model = p.name.split("__")[:2]
        if "_dev_" in prefix or sum(1 for _ in open(p)) < expected_n(prefix):
            continue   # development split, or a run that has not finished
        out.append((prefix, model.replace("ollama-", "").replace("-", ":", 1)))
    return out


def label(prefix, model):
    ds, split, n = prefix.split("_")[0], prefix.split("_")[1], prefix.split("_n")[-1]
    name = {"finqa": "FinQA", "tatqa": "TAT-QA", "indian": "IndAR", "finqa-perturbed": "FinQA-pert"}[ds]
    tag = {"heldout": "held-out", "test": "dev-test" if ds in ("finqa", "tatqa") else "test"}.get(split, split)
    mod = model.replace("qwen3:", "Qwen3-").replace("llama3.2:latest", "Llama-3.2-3B").replace("b", "B")
    return f"{name} {tag} (n={n}), {mod}"


def per_question(prefix, model):
    """{strategy: {uid: (correct, tokens, calls, record)}} with TRACE adaptive replayed."""
    trace = load(run_path(prefix, model, "trace"))
    uids = list(trace)
    table = {}
    pq_path = OUT / "trace_pg_per_question.csv"
    pq = pd.read_csv(pq_path) if pq_path.exists() else pd.DataFrame(columns=["prefix", "strategy"])
    for s in ORDER:
        if s == "trace_adaptive":
            rows = {}
            for u, r in trace.items():
                a, conf, cost, early = decide(r, VARIANTS["TRACE adaptive"])
                rows[u] = (ok(r, a), cost["prompt_tokens"] + cost["completion_tokens"], cost["calls"], r)
            table[s] = rows
            continue
        if s.startswith("trace_pg"):
            d = pq[(pq.prefix == prefix) & (pq.strategy == s)].set_index("uid") if model == "qwen3:1.7b" else pq.iloc[:0]
            if len(d) and all(u in d.index for u in uids):
                table[s] = {u: (bool(d.loc[u, "correct"]), float(d.loc[u, "tokens"]), float(d.loc[u, "calls"]),
                                {**trace[u], "extra": {**trace[u]["extra"], "confidence": float(d.loc[u, "confidence"])}})
                            for u in uids}
            continue
        p = run_path(prefix, model, s)
        if p is None:
            continue
        recs = load(p)
        if not all(u in recs for u in uids):
            continue
        table[s] = {u: (recs[u]["correct"], recs[u]["prompt_tokens"] + recs[u]["completion_tokens"],
                        recs[u]["n_calls"], recs[u]) for u in uids}
    return uids, table


def main_table():
    rows = []
    for prefix, model in settings():
        uids, table = per_question(prefix, model)
        ref_name = "trace_pg_esc" if "trace_pg_esc" in table else "trace"
        ref = np.array([table[ref_name][u][0] for u in uids])
        tests = []
        for s, d in table.items():
            flags = np.array([d[u][0] for u in uids])
            lo, hi = bootstrap_ci(flags)
            b, c, p = mcnemar(ref, flags) if s != ref_name else (0, 0, np.nan)
            rows.append({"setting": label(prefix, model), "prefix": prefix, "model": model, "strategy": s,
                         "method": NAMES[s], "n": len(uids), "accuracy": flags.mean(), "ci_low": lo,
                         "ci_high": hi, "tokens": np.mean([d[u][1] for u in uids]),
                         "calls": np.mean([d[u][2] for u in uids]), "trace_wins": b, "trace_losses": c,
                         "p": p})
            if s != ref_name:
                tests.append(len(rows) - 1)
        adj = holm([rows[i]["p"] for i in tests]) if tests else []
        for i, a in zip(tests, adj):
            rows[i]["p_holm"] = a
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "main_results.csv", index=False)
    return df


def ceiling_table():
    """Oracle coverage (is the gold among the candidates?) and answer agreement per candidate set."""
    rows = []
    for prefix, model in settings():
        uids, table = per_question(prefix, model)
        sets = {}
        if "pot_sc" in table:
            sets["PoT-SC: 5 programs, one prompt"] = {u: table["pot_sc"][u][3]["extra"]["votes"] for u in uids}
        if "sc_cot" in table:
            sets["CoT-SC: 5 CoT paths, one prompt"] = {u: table["sc_cot"][u][3]["extra"]["votes"] for u in uids}
        if "vpsc2" in table:
            sets["VPSC-v2: 5 calls, 3 views"] = {u: table["vpsc2"][u][3]["extra"]["votes"] for u in uids}
        sets["TRACE: 6 views + repairs"] = {u: [c["answer"] for c in table["trace"][u][3]["extra"]["candidates"]]
                                            for u in uids}
        for name, votes in sets.items():
            recs = {u: table["trace"][u][3] for u in uids}
            cover = np.mean([any(ok(recs[u], a) for a in votes[u]) for u in uids])
            distinct = np.mean([len(_distinct([a for a in votes[u] if a is not None])) for u in uids])
            unanimous_wrong = np.mean([
                len(set(map(str, votes[u]))) == 1 and not ok(recs[u], votes[u][0]) for u in uids])
            rows.append({"setting": label(prefix, model), "candidate set": name, "oracle coverage": cover,
                         "distinct answers / q": distinct, "unanimous and wrong": unanimous_wrong})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "ceiling.csv", index=False)
    return df


def _distinct(answers):
    out = []
    for a in answers:
        if not any(_same_answer(a, b) for b in out):
            out.append(a)
    return out


def ablation_table():
    rows = []
    for prefix, model in settings():
        trace = list(load(run_path(prefix, model, "trace")).values())
        for variant, cfg in VARIANTS.items():
            res = [decide(r, cfg) for r in trace]
            acc = np.mean([ok(r, a) for r, (a, *_) in zip(trace, res)])
            tok = np.mean([c["prompt_tokens"] + c["completion_tokens"] for _, _, c, _ in res])
            calls = np.mean([c["calls"] for _, _, c, _ in res])
            rows.append({"setting": label(prefix, model), "variant": variant, "accuracy": acc,
                         "tokens": tok, "calls": calls,
                         "early_exit": np.mean([e for *_, e in res])})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "ablations.csv", index=False)
    return df


def audit_repair_stats():
    """Audit precision at candidate level and what repair did."""
    rows = []
    for prefix, model in settings():
        trace = list(load(run_path(prefix, model, "trace")).values())
        flagged = flagged_wrong = clean = clean_wrong = 0
        kinds = {}
        repairs = fixed = broke = changed = 0
        for r in trace:
            cands = r["extra"]["candidates"]
            by_view = {c["view"]: c for c in cands}
            for c in cands:
                if not c["is_program"] or c["answer"] is None or c.get("parent"):
                    continue
                hard = [p for p in c["problems"] if p[1] >= 1.0]
                if hard:
                    flagged += 1
                    flagged_wrong += not ok(r, c["answer"])
                    for p in hard:
                        kinds[p[0]] = kinds.get(p[0], 0) + 1
                else:
                    clean += 1
                    clean_wrong += not ok(r, c["answer"])
            for c in cands:
                if not c.get("parent"):
                    continue
                parent = by_view[c["parent"]]
                repairs += 1
                before, after = ok(r, parent["answer"]), ok(r, c["answer"])
                fixed += (not before) and after
                broke += before and not after
                changed += parent["answer"] is None or c["answer"] is None or \
                    not _same_answer(parent["answer"], c["answer"])
        rows.append({"setting": label(prefix, model), "flagged programs": flagged,
                     "flagged wrong": flagged_wrong / max(1, flagged),
                     "unflagged wrong": clean_wrong / max(1, clean), "repairs": repairs,
                     "repairs changed answer": changed, "wrong->right": fixed, "right->wrong": broke,
                     **{f"kind:{k}": v for k, v in sorted(kinds.items())}})
    df = pd.DataFrame(rows).fillna(0)
    df.to_csv(OUT / "audit_repair.csv", index=False)
    return df


def selective_table():
    """Risk-coverage: TRACE confidence vs the vote agreement of the sampling baselines."""
    rows, curves = [], {}
    for prefix, model in settings():
        uids, table = per_question(prefix, model)
        lab = label(prefix, model)
        curves[lab] = {}
        for s in ("sc_cot", "pot_sc", "vpsc2", "trace"):
            if s not in table:
                continue
            flags = [table[s][u][0] for u in uids]
            if s == "trace":
                conf = [table[s][u][3]["extra"]["confidence"] for u in uids]
            else:
                conf = [table[s][u][3]["extra"].get("agreement", 0.0) for u in uids]
            cov, acc, aurc, a50, a80 = risk_coverage(flags, conf)
            curves[lab][NAMES[s]] = (cov, acc)
            rows.append({"setting": lab, "method": NAMES[s], "accuracy": np.mean(flags), "AURC": aurc,
                         "acc@50%": a50, "acc@80%": a80})
        # accept-path precision: TRACE early exit (audited program agrees with CoT)
        early = [u for u in uids if table["trace"][u][3]["extra"]["early_exit"]]
        if early:
            rows.append({"setting": lab, "method": "TRACE accept-path", "accuracy":
                         np.mean([table["trace"][u][0] for u in early]), "AURC": np.nan,
                         "acc@50%": np.nan, "acc@80%": np.nan, "coverage": len(early) / len(uids)})
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "selective.csv", index=False)
    return df, curves


# ---------------------------------------------------------------------------------- figures
def fig_risk_coverage(curves):
    keys = [k for k in curves if "held-out" in k] or list(curves)[:2]
    fig, axes = plt.subplots(1, len(keys), figsize=(3.5 * len(keys), 2.6), squeeze=False)
    colors = {"CoT-SC (5)": "#9aa5b1", "PoT-SC (5)": "#c58b3f", "VPSC-v2": "#5b8db8", "TRACE (full)": "#1a7f5a"}
    for ax, k in zip(axes[0], keys):
        for name, (cov, acc) in curves[k].items():
            ax.plot(cov * 100, acc * 100, label=name, color=colors.get(name), lw=1.6)
        ax.set_title(k.split(",")[0], fontsize=9)
        ax.set_xlabel("coverage (%)", fontsize=8)
        ax.set_ylabel("selective accuracy (%)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3)
    axes[0][0].legend(fontsize=6.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(OUT / "risk_coverage.pdf")
    fig.savefig(OUT / "risk_coverage.png", dpi=200)


def fig_pareto(main):
    keys = [s for s in main["setting"].unique() if "held-out" in s] or list(main["setting"].unique())[:2]
    fig, axes = plt.subplots(1, len(keys), figsize=(3.5 * len(keys), 2.6), squeeze=False)
    for ax, k in zip(axes[0], keys):
        d = main[main["setting"] == k]
        for k_, (_, r) in enumerate(d.sort_values("tokens").iterrows()):
            ours = r["strategy"].startswith("trace")
            ax.errorbar(r["tokens"] / 1000, r["accuracy"] * 100,
                        yerr=[[100 * (r["accuracy"] - r["ci_low"])], [100 * (r["ci_high"] - r["accuracy"])]],
                        fmt="o", ms=4, color="#1a7f5a" if ours else "#5b6b7b", elinewidth=0.6, capsize=1.5)
            ax.annotate(r["method"].replace(" [prior]", ""), (r["tokens"] / 1000, r["accuracy"] * 100),
                        fontsize=5.5, xytext=(3, 6 if k_ % 2 else -9), textcoords="offset points")
        ax.set_title(k.split(",")[0], fontsize=9)
        ax.set_xlabel("tokens per question (thousands)", fontsize=8)
        ax.set_ylabel("accuracy (%)", fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "pareto.pdf")
    fig.savefig(OUT / "pareto.png", dpi=200)


def main():
    main_df = main_table()
    ceil = ceiling_table()
    abl = ablation_table()
    audit = audit_repair_stats()
    sel, curves = selective_table()
    fig_risk_coverage(curves)
    fig_pareto(main_df)
    for name, df in [("main", main_df), ("ceiling", ceil), ("ablations", abl), ("audit", audit),
                     ("selective", sel)]:
        print(f"\n## {name}\n")
        print(df.to_markdown(index=False, floatfmt=".3f"))
    write_tex()




# ---------------------------------------------------------------------------------- LaTeX tables
def _cols(main, models=("qwen3:1.7b",)):
    order = ["finqa_heldout_n200", "tatqa_heldout_n200", "indian_test_n44", "finqa-perturbed_test_n100",
             "finqa_test_n100", "tatqa_test_n100"]
    have = set(zip(main["prefix"], main["model"]))
    return [(p, m) for p in order for m in models if (p, m) in have]


SHORT = {"finqa_heldout_n200": "FinQA\\textsuperscript{H}", "tatqa_heldout_n200": "TAT-QA\\textsuperscript{H}",
         "indian_test_n44": "IndAR", "finqa-perturbed_test_n100": "FinQA-pert",
         "finqa_test_n100": "FinQA\\textsuperscript{D}", "tatqa_test_n100": "TAT-QA\\textsuperscript{D}",
         "finqa_heldout_n100": "FinQA\\textsuperscript{H}", "tatqa_heldout_n100": "TAT-QA\\textsuperscript{H}"}


def _cell(r, best):
    acc = 100 * r["accuracy"]
    s = f"{acc:.1f}"
    if abs(r["accuracy"] - best) < 1e-9:
        s = f"\\textbf{{{s}}}"
    if r["strategy"] != "trace_pg_esc" and r.get("p_holm", 1) < 0.05:
        s += "$^{\\ast}$"
    return s + f" {{\\scriptsize[{100 * r['ci_low']:.0f},{100 * r['ci_high']:.0f}]}}"


def main_tex(main, models=("qwen3:1.7b",), name="main_table.tex", tokens_prefix=None):
    cols = _cols(main, models)
    if not cols:
        return
    tokens_prefix = tokens_prefix or cols[0]
    lines = ["\\begin{tabular}{l" + "c" * len(cols) + "rr}", "\\toprule",
             "Method & " + " & ".join(f"{SHORT[p]} ({int(main[(main.prefix == p) & (main.model == m)].n.iloc[0])})"
                                      for p, m in cols) + " & Tok/q & Calls \\\\", "\\midrule"]
    for s in ORDER:
        cells = []
        for p, m in cols:
            d = main[(main.prefix == p) & (main.model == m)]
            row = d[d.strategy == s]
            cells.append(_cell(row.iloc[0], d.accuracy.max()) if len(row) else "--")
        t = main[(main.prefix == tokens_prefix[0]) & (main.model == tokens_prefix[1]) & (main.strategy == s)]
        tok = f"{t.tokens.iloc[0] / 1000:.1f}k" if len(t) else "--"
        calls = f"{t.calls.iloc[0]:.1f}" if len(t) else "--"
        if s in ("trace", "trace_pg"):
            lines.append("\\midrule")
        lines.append(f"{NAMES[s]} & " + " & ".join(cells) + f" & {tok} & {calls} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / name).write_text("\n".join(lines) + "\n")


def cross_model_tex(main):
    rows = [(p, m) for p, m in sorted(set(zip(main["prefix"], main["model"]))) if m != "qwen3:1.7b"]
    if not rows:
        return
    strategies = [s for s in ORDER if s in set(main.strategy)]
    lines = ["\\begin{tabular}{l" + "c" * len(rows) + "}", "\\toprule",
             "Method & " + " & ".join(f"{SHORT.get(p, p)} {m.replace('qwen3:', 'Qwen3-').replace('llama3.2:latest', 'Llama-3B').replace('b', 'B')}"
                                      for p, m in rows) + " \\\\", "\\midrule"]
    for s in strategies:
        cells = []
        for p, m in rows:
            d = main[(main.prefix == p) & (main.model == m)]
            r = d[d.strategy == s]
            cells.append(_cell(r.iloc[0], d.accuracy.max()).split(" {")[0] if len(r) else "--")
        if all(c == "--" for c in cells):
            continue
        lines.append(f"{NAMES[s]} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "cross_model_table.tex").write_text("\n".join(lines) + "\n")


def ceiling_tex(ceil):
    keep = [s for s in ceil.setting.unique() if "Qwen3-1.7B" in s and ("held-out" in s)] or \
        [s for s in ceil.setting.unique() if "Qwen3-1.7B" in s][:2]
    lines = ["\\begin{tabular}{lccc}", "\\toprule", "Candidate set & Coverage & Distinct/q & Unan.\\ wrong \\\\"]
    for s in keep:
        lines += ["\\midrule", f"\\multicolumn{{4}}{{l}}{{\\emph{{{s.split(',')[0]}}}}} \\\\"]
        for _, r in ceil[ceil.setting == s].iterrows():
            lines.append(f"{r['candidate set']} & {100 * r['oracle coverage']:.1f} & {r['distinct answers / q']:.2f} & "
                         f"{100 * r['unanimous and wrong']:.1f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "ceiling_table.tex").write_text("\n".join(lines) + "\n")


def ablation_tex(abl):
    keep = [s for s in abl.setting.unique() if "Qwen3-1.7B" in s and "held-out" in s] or \
        [s for s in abl.setting.unique() if "Qwen3-1.7B" in s][:2]
    lines = ["\\begin{tabular}{l" + "cc" * len(keep) + "}", "\\toprule",
             "Variant & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{s.split(' (')[0]}}}" for s in keep) + " \\\\",
             " & " + " & ".join("Acc & Tok/q" for _ in keep) + " \\\\", "\\midrule"]
    for v in VARIANTS:
        cells = []
        for s in keep:
            r = abl[(abl.setting == s) & (abl.variant == v)].iloc[0]
            cells.append(f"{100 * r.accuracy:.1f} & {r.tokens / 1000:.1f}k")
        lines.append(f"{v.replace('- ', '$-$ ')} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "ablation_table.tex").write_text("\n".join(lines) + "\n")


def audit_tex(audit, sel):
    keep = [s for s in audit.setting.unique() if "Qwen3-1.7B" in s]
    lines = ["\\begin{tabular}{lccccc}", "\\toprule",
             "Setting & Flagged & P(wrong$\\mid$flag) & P(wrong$\\mid$clean) & Repairs (fix/break) & Accept-path acc (cov.) \\\\",
             "\\midrule"]
    for s in keep:
        r = audit[audit.setting == s].iloc[0]
        a = sel[(sel.setting == s) & (sel.method == "TRACE accept-path")]
        acc = f"{100 * a.accuracy.iloc[0]:.1f} ({100 * a.coverage.iloc[0]:.0f}\\%)" if len(a) else "--"
        lines.append(f"{s.split(',')[0]} & {int(r['flagged programs'])} & {100 * r['flagged wrong']:.1f} & "
                     f"{100 * r['unflagged wrong']:.1f} & {int(r['repairs'])} ({int(r['wrong->right'])}/{int(r['right->wrong'])}) & {acc} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "audit_table.tex").write_text("\n".join(lines) + "\n")


def selective_tex(sel):
    keep = [s for s in sel.setting.unique() if "Qwen3-1.7B" in s and ("held-out" in s or "IndAR" in s)] or \
        [s for s in sel.setting.unique() if "Qwen3-1.7B" in s]
    methods = ["CoT-SC (5)", "PoT-SC (5)", "VPSC-v2", "TRACE (full)"]
    lines = ["\\begin{tabular}{l" + "cc" * len(keep) + "}", "\\toprule",
             "Method & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{s.split(' (')[0]}}}" for s in keep) + " \\\\",
             " & " + " & ".join("AURC$\\downarrow$ & Acc@50\\%" for _ in keep) + " \\\\", "\\midrule"]
    for m in methods:
        cells = []
        for s in keep:
            r = sel[(sel.setting == s) & (sel.method == m)]
            cells.append(f"{r.AURC.iloc[0]:.3f} & {100 * r['acc@50%'].iloc[0]:.1f}" if len(r) else "-- & --")
        lines.append(f"{m} & " + " & ".join(cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (OUT / "selective_table.tex").write_text("\n".join(lines) + "\n")


def write_tex():
    main = pd.read_csv(OUT / "main_results.csv")
    main_tex(main)
    cross_model_tex(main)
    ceiling_tex(pd.read_csv(OUT / "ceiling.csv"))
    ablation_tex(pd.read_csv(OUT / "ablations.csv"))
    audit_tex(pd.read_csv(OUT / "audit_repair.csv"), pd.read_csv(OUT / "selective.csv"))
    selective_tex(pd.read_csv(OUT / "selective.csv"))


if __name__ == "__main__" and "--tex" in sys.argv:
    write_tex()


if __name__ == "__main__" and "--tex" not in sys.argv:
    main()
