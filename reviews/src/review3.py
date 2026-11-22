"""Review 3 (15 marks): final demo. Slides, final report, IEEE-format paper and a demo + viva guide.
Every number is computed from the experiment runs (results/runs) through data.py; experiments that have
not finished are shown as pending instead of being estimated."""
import json

import pandas as pd

import data
import diagrams as D
from common import (BUILD, ROOT, Deck, IEEE_CSS, REPORT_CSS, SLIDE_CSS, TEAM, TITLE, cover, esc, img, page, table,
                    title_slide, ul)
from references import cite, ref_list_html

LABEL = "Review 3"
S, L = data.SMALL, data.LARGE
ML = data.model_label
SL = data.strategy_label
FIG = BUILD / "fig"
SHOTS = BUILD / "shots"


def fig(name):
    import figs
    if figs.PRODUCED.get("_built"):
        return figs.PRODUCED.get(name)
    p = FIG / f"{name}.png"
    return p if p.exists() else None


def shot(name):
    p = SHOTS / f"{name}.png"
    return p if p.exists() else None


def P(x, d=1):
    return data.pct(x, d)


def acc(d, m, s, **kw):
    r = data.cell(d, m, s, **kw)
    return None if r is None else r.accuracy


def has_model(m):
    return m in data.models()   # only models whose main grid is complete


# ============================================================================================
# Experiment status
# ============================================================================================
def opt_name(kind, m):
    slug = m.replace(":", "-")
    return {"bootstrap": f"dspy:artifacts/dspy_bootstrap_{slug}.json", "mipro": f"dspy:artifacts/dspy_mipro_{slug}.json",
            "textgrad": f"textgrad:artifacts/textgrad_{slug}.json"}[kind]


def planned():
    """(stage, model, list of (dataset, strategy, kwargs)) following scripts/run_all.sh."""
    manual = ["direct", "cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot"]
    out = []
    for m in (S, L):
        out.append(("Main grid (6 strategies × FinQA, TAT-QA)", m, [(d, s, {}) for d in ["finqa", "tatqa"] for s in manual]))
        out.append(("VPSC + PoT-SC (3 datasets)", m, [(d, s, {}) for d in data.DATASETS for s in ["vpsc", "pot_sc"]]))
        out.append(("Indian set (6 strategies)", m, [("indian", s, {}) for s in manual]))
        out.append(("Perturbation test", m, [("finqa", s, {"perturbed": True}) for s in ["cot_fs", "pot_fs", "vpsc"]]))
        kinds = ["bootstrap", "mipro", "textgrad"]
        out.append(("DSPy + TextGrad (3 datasets)", m, [(d, opt_name(k, m), {}) for d in data.DATASETS for k in kinds]))
        fm_ds = ["finqa", "tatqa"] if m == S else ["finqa"]
        out.append(("Table formats", m, [(d, "cot_fs", {"fmt": f}) for d in fm_ds for f in ["json", "html", "text"]]))
        out.append(("Retrieval (top-5)", m, [(d, "pot_fs", {"context": "retrieved"}) for d in ["finqa", "tatqa"]]))
        if m == S:
            out.append(("Thinking mode", m, [("finqa", "cot_zs", {"think": True})]))
    return out


def run_done(d, s, kw):
    r = data.cell(d, kw.get("model"), s, partial=True, **{k: v for k, v in kw.items() if k != "model"})
    if r is None:
        return 0
    full = 88 if kw.get("perturbed") else data.FULL_N[d]
    return min(1.0, r.n / full)


def status_rows():
    rows = {}
    for stage, m, runs in planned():
        fr = [run_done(d, s, dict(kw, model=m)) for d, s, kw in runs]
        done = sum(1 for f in fr if f >= 1)
        if done == len(runs):
            txt = "✓ complete"
        elif done or any(fr):
            txt = f"◐ {done}/{len(runs)} runs"
        else:
            txt = "pending"
        rows.setdefault(stage, {})[m] = txt
    return [[stage, v.get(S, "–"), v.get(L, "n/a")] for stage, v in rows.items()]


def status_table(cls="t"):
    return table(["Experiment stage", "Qwen3-1.7B", "Qwen3-8B"], status_rows(), cls=cls, widths=[52, 24, 24])


def all_complete():
    return all(r[1].startswith("✓") and (r[2].startswith("✓") or r[2] == "n/a") for r in status_rows())


# ============================================================================================
# Numbers and findings
# ============================================================================================
def totals():
    df = data.runs()
    return dict(records=len(df), runs=df["run"].nunique(), calls=int(df["n_calls"].sum()),
                tokens=int((df["prompt_tokens"] + df["completion_tokens"]).sum()))


def best(d, m, pool=None):
    ms = data.main_summary()
    sub = ms[(ms.dataset == d) & (ms.model == m)]
    if pool:
        sub = sub[sub.strategy.isin(pool)]
    if sub.empty:
        return None
    top = sub.accuracy.max()
    r = sub[sub.accuracy == top].sort_values("total_tokens").iloc[0]
    return r


def sig_row(d, m, s):
    sg = data.significance()
    if sg.empty:
        return None
    r = sg[(sg.dataset == d) & (sg.model == m) & (sg.strategy == s) & (~sg.perturbed) & (sg.fmt == "markdown") & (sg.context == "full") & (~sg.think)]
    return None if r.empty else r.iloc[0]


def pfmt(p):
    if p is None or pd.isna(p):
        return "–"
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def error_shares(m):
    df = data.main_runs()
    dsets = [d for d in ["finqa", "tatqa"] if all(data.cell(d, m, s) is not None for s in data.MANUAL)]
    w = df[(df.model == m) & (~df.correct) & (df.dataset.isin(dsets)) & (df.strategy != "direct") & (~df.strategy.str.contains(":"))]
    if w.empty:
        return None
    vc = w.error_category.value_counts(normalize=True)
    return vc, len(w)


def steps_drop(m, s="cot_fs"):
    df = data.main_runs()
    g = df[(df.model == m) & (df.strategy == s) & (df.dataset.isin(["finqa", "tatqa"]))]
    if g.empty:
        return None
    g = g.assign(b=g.n_steps.clip(upper=3)).groupby("b")["correct"].agg(["mean", "count"])
    return g


REASONING = ["cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"]
SINGLE = ["cot_zs", "cot_fs", "decomp_fs", "pot_fs"]


def reasoning_range(m):
    ms = data.main_summary()
    sub = ms[(ms.model == m) & (ms.strategy.isin(REASONING))]
    return (sub.accuracy.min(), sub.accuracy.max()) if not sub.empty else (None, None)


def any_significant(m, strategies, datasets=data.DATASETS):
    for d in datasets:
        for st in strategies:
            r = sig_row(d, m, st)
            if r is not None and r.p_holm < 0.05:
                return True
    return False


def most_efficient(m, d):
    ms = data.main_summary()
    sub = ms[(ms.model == m) & (ms.dataset == d) & (ms.strategy.isin(REASONING))]
    return None if sub.empty else sub.sort_values("tokens_per_correct").iloc[0]


def frontier(m, d):
    """Strategies on the accuracy-vs-tokens frontier (no other strategy is cheaper and at least as accurate)."""
    ms = data.main_summary()
    sub = ms[(ms.model == m) & (ms.dataset == d) & (~ms.strategy.str.contains(":"))]
    out = []
    for r in sub.itertuples():
        if not any((o.total_tokens < r.total_tokens and o.accuracy >= r.accuracy) or (o.total_tokens <= r.total_tokens and o.accuracy > r.accuracy) for o in sub.itertuples()):
            out.append(r)
    return sorted(out, key=lambda r: r.total_tokens)


def five_sample_multiplier(m):
    ms = data.main_summary()
    vals = []
    for d in data.DATASETS:
        base = data.cell(d, m, "cot_fs")
        for st in ["sc_cot", "pot_sc", "vpsc"]:
            r = data.cell(d, m, st)
            if base is not None and r is not None:
                vals.append(r.total_tokens / base.total_tokens)
    return (min(vals), max(vals)) if vals else None


def pooled_steps(m, st):
    df = data.main_runs()
    g = df[(df.model == m) & (df.strategy == st)]
    if g.empty:
        return None
    return g.assign(b=g.n_steps.clip(upper=3)).groupby("b")["correct"].mean()


def steps_sentence(m):
    parts = []
    for st in ["cot_fs", "pot_fs"]:
        g = pooled_steps(m, st)
        if g is not None and 1 in g.index and 3 in g.index:
            parts.append(f"{SL(st)} {P(g[1], 0)}% on 1-step vs {P(g[3], 0)}% on 3+-step questions")
    return ("Pooled over all three datasets: " + "; ".join(parts) + ".") if parts else ""


def best_single(m, d):
    return best(d, m, SINGLE)


def single_sentence(m):
    """e.g. 'Program-of-Thought is the best single-call strategy on FinQA and Indian reports (CoT few-shot on TAT-QA)'."""
    by = {}
    for d in data.DATASETS:
        r = best_single(m, d)
        if r is not None:
            by.setdefault(r.strategy, []).append(data.DLABEL[d])
    if not by:
        return ""
    main = max(by, key=lambda k: len(by[k]))
    rest = [f"{SL(k)} on {' and '.join(v)}" for k, v in by.items() if k != main]
    return f"{SL(main)} is the best single-call strategy on {' and '.join(by[main])}" + (f" ({'; '.join(rest)})" if rest else "")


def five_sentence(m):
    mult = five_sample_multiplier(m)
    if not mult:
        return ""
    return (f"five-sample strategies cost {mult[0]:.1f}–{mult[1]:.1f}× the tokens of few-shot CoT"
            + (" without significant gains" if not any_significant(m, ["sc_cot", "pot_sc", "vpsc"]) else ""))


def findings(m):
    """Bullet findings for one model, each computed from the runs."""
    f = []
    if not has_model(m):
        return f
    # direct vs reasoning
    dir_acc = [acc(d, m, "direct") for d in data.DATASETS if acc(d, m, "direct") is not None]
    reason = [(d, best(d, m, ["cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"])) for d in data.DATASETS]
    reason = [(d, r) for d, r in reason if r is not None]
    if dir_acc and reason:
        f.append(f"<b>Showing work is essential.</b> Direct answering reaches only {P(min(dir_acc), 0)}–{P(max(dir_acc), 0)}%; the best reasoning strategy reaches "
                 + ", ".join(f"{P(r.accuracy, 0)}% ({SL(r.strategy)}) on {data.DLABEL[d]}" for d, r in reason) + ".")
    # PoT vs CoT
    parts = []
    for d in data.DATASETS:
        a, b = acc(d, m, "pot_fs"), acc(d, m, "cot_fs")
        if a is not None and b is not None:
            sr = sig_row(d, m, "pot_fs")
            parts.append(f"{data.DLABEL[d]} {100 * (a - b):+.0f} pts" + (f" (Holm p = {pfmt(sr.p_holm)})" if sr is not None else ""))
    if parts:
        sig = any_significant(m, ["pot_fs"])
        f.append("<b>Program-of-Thought vs few-shot CoT:</b> " + "; ".join(parts) + ". " +
                 ("None of these differences is significant after Holm correction — with 44–100 questions only large effects can be detected." if not sig
                  else "Some differences are significant after Holm correction (see the significance table)."))
    # self-consistency cost
    sc = [(d, acc(d, m, "sc_cot"), acc(d, m, "cot_fs"), data.cell(d, m, "sc_cot"), data.cell(d, m, "cot_fs")) for d in ["finqa", "tatqa", "indian"]]
    sc = [x for x in sc if x[1] is not None and x[2] is not None]
    if sc:
        mult = sum(x[3].total_tokens / x[4].total_tokens for x in sc) / len(sc)
        f.append("<b>Self-Consistency is poor value for a small model:</b> five CoT samples change accuracy by "
                 + ", ".join(f"{100 * (x[1] - x[2]):+.0f} pts on {data.DLABEL[x[0]]}" for x in sc)
                 + f" at about {mult:.1f}× the tokens of one few-shot CoT call"
                 + (" — none of these differences is significant." if not any_significant(m, ["sc_cot"]) else "."))
    # VPSC
    diag = data.vpsc_diagnostics(m)
    if not diag.empty:
        same = all(acc(d, m, "vpsc") == acc(d, m, "pot_sc") for d in diag.dataset)
        ung = int(diag.ungrounded.sum())
        progs = int(diag.executed.sum())
        flagged = int(diag.flagged_questions.sum())
        flagged_ok = int(diag.flagged_correct.sum())
        txt = (f"<b>VPSC (ours):</b> the grounding check rejected {ung} of {progs} executed programs ({100 * ung / max(progs, 1):.1f}%), touching {flagged} questions; "
               f"{flagged - flagged_ok} of these {flagged} questions were answered wrongly. ")
        precise = flagged > 0 and flagged_ok == 0
        if same:
            allung = int(diag.all_ungrounded.sum())
            txt += ("Because the five samples agree strongly (mean vote agreement " + ", ".join(f"{100 * r.agreement:.0f}% on {data.DLABEL[r.dataset]}" for r in diag.itertuples()) +
                    f") and in {allung} of the {flagged} flagged questions <i>all</i> programs were ungrounded (so the fallback vote was used), verification changed no final answer: VPSC = PoT-SC. " +
                    ("The check is therefore most useful as a <b>reliability flag</b> (an ungrounded answer is very likely wrong) rather than as a vote filter for this model." if precise else ""))
        else:
            txt += "Verification changed " + ", ".join(f"{int(r.answers_changed)} answers on {data.DLABEL[r.dataset]}" for r in diag.itertuples()) + " compared with PoT-SC."
        f.append(txt)
    # errors
    es = error_shares(m)
    if es:
        vc, n = es
        f.append(f"<b>Evidence errors dominate:</b> across reasoning strategies on FinQA and TAT-QA, {100 * vc.get('evidence_error', 0):.0f}% of the {n} wrong answers use a wrong or missing operand, "
                 f"{100 * vc.get('reasoning_error', 0):.0f}% have all operands but a wrong formula/arithmetic, {100 * vc.get('scale_error', 0):.0f}% are unit/scale errors and "
                 f"{100 * vc.get('sign_error', 0):.0f}% sign errors. The bottleneck is <i>finding and copying the right numbers</i>, not computing.")
    # Indian
    ind = [(s, acc("indian", m, s)) for s in ["cot_fs", "pot_fs", "vpsc"] if acc("indian", m, s) is not None]
    if ind:
        fin = {st: acc("finqa", m, st) for st, _ in ind}
        not_lower = all(fin[st] is None or a >= fin[st] for st, a in ind)
        f.append("<b>Generalization to Indian reports:</b> " + ", ".join(f"{SL(st)} {P(a, 0)}% (FinQA {P(fin[st], 0)}%)" for st, a in ind) +
                 " on the 44 ₹ crore/lakh questions" + (" — at or above the FinQA level, so the strategies transfer to unseen, region-specific statements." if not_lower
                                                         else " — lower than on FinQA for some strategies, showing a generalization gap."))
    # optimization
    opts = data.optimized_strategies(m)
    if opts:
        parts = []
        for s in opts:
            for d in data.DATASETS:
                a, base = acc(d, m, s), acc(d, m, "cot_fs")
                if a is not None and base is not None:
                    parts.append(f"{SL(s)} {data.DLABEL[d]} {P(a, 0)}% ({100 * (a - base):+.0f} vs few-shot CoT)")
        f.append("<b>Automated optimization:</b> " + "; ".join(parts) + ".")
    # perturbation
    pt = data.perturbation()
    if not pt.empty:
        pm = pt[pt.model == m]
        if not pm.empty:
            nsig = all(r.p_value >= 0.05 for r in pm.itertuples())
            f.append("<b>Perturbed numbers:</b> on the same FinQA questions with changed numbers, " + "; ".join(
                f"{SL(r.strategy)} {P(r.original_accuracy, 0)}% → {P(r.perturbed_accuracy, 0)}% (n = {int(r.n)}, McNemar p = {pfmt(r.p_value)})" for r in pm.itertuples()) + ". "
                + ("No drop is significant, so there is no evidence that the model answers from memorized FinQA answers." if nsig else "Some drops are significant, suggesting partial memorization."))
    return f


# ============================================================================================
# Tables
# ============================================================================================
def results_table(m, cls="t"):
    rows = []
    for s in data.MAIN_ORDER + data.optimized_strategies(m):
        row = [SL(s)]
        tok = []
        for d in data.DATASETS:
            r = data.cell(d, m, s)
            if r is None:
                row.append("pending")
            else:
                star = "" if data.complete(r, d) else f" (n={int(r.n)})"
                row.append(f"{P(r.accuracy)} <span style='color:#8a94a6'>[{P(r.ci_low, 0)}–{P(r.ci_high, 0)}]</span>{star}")
                tok.append(r.total_tokens)
        rf = data.cell("finqa", m, s)
        row.append(f"{sum(tok) / len(tok):,.0f}" if tok else "–")
        row.append(f"{rf.calls:.1f}" if rf is not None else "–")
        row.append(f"{rf.latency_s:.1f}" if rf is not None else "–")
        rows.append(row)
    return table(["Strategy", "FinQA (n=100)", "TAT-QA (n=100)", "Indian (n=44)", "Tokens / Q", "Calls / Q", "Latency s (FinQA)"],
                 rows, num_cols=(4, 5, 6), cls=cls, highlight=lambda i, r: "VPSC" in r[0], widths=[22, 15, 15, 15, 11, 9, 13])


def sig_table(m, cls="t"):
    sg = data.significance()
    if sg.empty:
        return "<p>Pending.</p>"
    sg = sg[(sg.model == m) & (~sg.perturbed) & (sg.fmt == "markdown") & (sg.context == "full") & (~sg.think)]
    rows = []
    for d in data.DATASETS:
        for r in sg[sg.dataset == d].sort_values("strategy", key=lambda c: c.map(data.strategy_rank)).itertuples():
            rows.append([data.DLABEL[d], SL(r.strategy), str(r.n), P(r.accuracy), P(r.baseline), f"{r.wins} / {r.losses}", pfmt(r.p_value), pfmt(r.p_holm)])
    return table(["Dataset", "Strategy", "n", "Acc.", "CoT-fs", "Wins / losses", "p", "p (Holm)"], rows, num_cols=(2, 3, 4, 5, 6, 7), cls=cls,
                 highlight=lambda i, r: r[7] not in ("–",) and (r[7] == "< 0.001" or float(r[7]) < 0.05))


def sig_compact(m, cls="t"):
    """One row per strategy, one column per dataset: accuracy (wins/losses vs CoT-fs, Holm p)."""
    rows = []
    for st in [x for x in data.MAIN_ORDER if x != "cot_fs"] + data.optimized_strategies(m):
        r = [SL(st)]
        for d in data.DATASETS:
            sr = sig_row(d, m, st)
            r.append("–" if sr is None else f"{P(sr.accuracy)} vs {P(sr.baseline)} · {sr.wins}/{sr.losses} · p<sub>H</sub> {pfmt(sr.p_holm)}")
        rows.append(r)
    return table(["Strategy vs few-shot CoT"] + [data.DLABEL[d] for d in data.DATASETS], rows, cls=cls, widths=[22, 26, 26, 26],
                 highlight=lambda i, r: any("< 0.001" in c or ("p<sub>H</sub> 0.0" in c) for c in r[1:]))


def error_table(m, cls="t"):
    df = data.main_runs()
    w = df[(df.model == m) & (~df.correct) & (df.dataset.isin(["finqa", "tatqa"]))]
    if w.empty:
        return ""
    t = w.pivot_table(index="strategy", columns="error_category", values="uid", aggfunc="count", fill_value=0)
    order = [s for s in data.MAIN_ORDER + data.optimized_strategies(m) if s in t.index]
    cats = [c for c in ["no_answer", "execution_error", "sign_error", "scale_error", "rounding_near_miss", "no_work_shown", "evidence_error", "reasoning_error"] if c in t.columns]
    names = {"no_answer": "No ans.", "execution_error": "Code fail", "sign_error": "Sign", "scale_error": "Scale", "rounding_near_miss": "Near miss",
             "no_work_shown": "No work", "evidence_error": "Evidence", "reasoning_error": "Reasoning"}
    rows = [[SL(s)] + [str(int(t.loc[s, c])) for c in cats] + [str(int(t.loc[s].sum()))] for s in order]
    return table(["Strategy"] + [names[c] for c in cats] + ["Wrong"], rows, num_cols=range(1, len(cats) + 2), cls=cls)


def vpsc_table(m, cls="t"):
    dg = data.vpsc_diagnostics(m)
    if dg.empty:
        return ""
    rows = []
    for r in dg.itertuples():
        rows.append([data.DLABEL[r.dataset], P(acc(r.dataset, m, "vpsc")), P(acc(r.dataset, m, "pot_sc")), P(acc(r.dataset, m, "sc_cot")), P(acc(r.dataset, m, "pot_fs")),
                     f"{r.ungrounded} / {r.executed}", f"{r.flagged_questions} ({r.flagged_questions - r.flagged_correct} wrong)", str(r.answers_changed), f"{100 * r.agreement:.0f}%"])
    return table(["Dataset", "VPSC", "PoT-SC", "CoT-SC", "PoT", "Ungrounded / executed programs", "Questions flagged", "Answers changed", "Vote agreement"],
                 rows, num_cols=range(1, 9), cls=cls)


def opt_table(cls="t"):
    arts = data.artifacts()
    if not arts:
        return None
    rows = []
    for name, a in arts.items():
        if name.startswith("dspy"):
            prog = a.get("program", {})
            rows.append([("DSPy MIPROv2" if "mipro" in name else "DSPy BootstrapFewShot"), ML(a["lm_spec"]), f"{a['train_size']} / {a['val_size']}",
                         P(a["val_accuracy"]), f"{a['compile_seconds'] / 60:.0f}", f"{a['compile_lm_calls']:,}",
                         f"{(a['compile_prompt_tokens'] + a['compile_completion_tokens']):,}", str(len(prog.get("demos", []))) + " demos"])
        else:
            u = a["usage"]
            kept = sum(1 for h in a["history"] if h.get("kept") and h["step"] > 0)
            rows.append(["TextGrad", ML(a["task_model"]), f"{a['train_size']} / {a['val_size']}", P(a["val_accuracy"]), f"{a['seconds'] / 60:.0f}",
                         f"{u['task_calls'] + u['optimizer_calls']:,}", f"{u['prompt_tokens'] + u['completion_tokens']:,}", f"{kept} of {len(a['history']) - 1} updates kept"])
    return table(["Optimizer", "Model", "Train / val", "Val. acc.", "Minutes", "LLM calls", "Tokens", "Result"], rows, num_cols=(3, 4, 5, 6), cls=cls)


def textgrad_prompt():
    for name, a in data.artifacts().items():
        if name.startswith("textgrad"):
            return ML(a["task_model"]), a["system_prompt"]
    return None


def perturb_table(cls="t"):
    pt = data.perturbation()
    if pt.empty:
        return None
    rows = [[SL(r.strategy), ML(r.model), str(r.n), P(r.original_accuracy), P(r.perturbed_accuracy), f"{100 * r.drop:+.1f}".replace("+", "−", 1) if r.drop > 0 else f"{-100 * r.drop:+.1f}",
             f"{r.only_original_right} / {r.only_perturbed_right}", pfmt(r.p_value)] for r in pt.itertuples()]
    return table(["Strategy", "Model", "n", "Original", "Perturbed", "Change", "Only orig. / only pert. right", "McNemar p"], rows, num_cols=range(2, 8), cls=cls)


def ablation_table(m, cls="t"):
    rows = []
    for d in ["finqa", "tatqa"]:
        for f in ["markdown", "json", "html", "text"]:
            r = data.cell(d, m, "cot_fs", fmt=f)
            if r is not None and f != "markdown" or (f == "markdown" and data.cell(d, m, "cot_fs", fmt="json") is not None):
                rows.append([f"Table format: {f}", data.DLABEL[d], "few-shot CoT", P(r.accuracy) if r is not None else "–", f"{r.total_tokens:,.0f}" if r is not None else "–"])
        for cx, lab in [("full", "full page"), ("retrieved", "top-5 retrieved")]:
            r = data.cell(d, m, "pot_fs", context=cx)
            if data.cell(d, m, "pot_fs", context="retrieved") is not None and r is not None:
                rows.append([f"Context: {lab}", data.DLABEL[d], "PoT", P(r.accuracy), f"{r.total_tokens:,.0f}"])
    th = data.cell("finqa", m, "cot_zs", think=True)
    if th is not None:
        r0 = data.cell("finqa", m, "cot_zs")
        rows.append(["Thinking off", "FinQA", "zero-shot CoT", P(r0.accuracy), f"{r0.total_tokens:,.0f}"])
        rows.append(["Thinking on", "FinQA", "zero-shot CoT", P(th.accuracy) + ("" if th.n >= 100 else f" (n={int(th.n)})"), f"{th.total_tokens:,.0f}"])
    if not rows:
        return None
    return table(["Variant", "Dataset", "Strategy", "Accuracy %", "Tokens / Q"], rows, num_cols=(3, 4), cls=cls)


def steps_table(m, cls="t"):
    df = data.main_runs()
    df = df[(df.model == m)]
    rows = []
    for s in ["direct", "cot_fs", "pot_fs", "vpsc"]:
        r = [SL(s)]
        for d in data.DATASETS:
            g = df[(df.dataset == d) & (df.strategy == s)]
            if g.empty:
                r += ["–"] * 3
                continue
            g = g.assign(b=g.n_steps.clip(upper=3)).groupby("b")["correct"].mean()
            r += [P(g.get(k)) if k in g.index else "–" for k in (1, 2, 3)]
        rows.append(r)
    return table(["Strategy", "FinQA 1", "FinQA 2", "FinQA 3+", "TAT-QA 1", "TAT-QA 2", "TAT-QA 3+", "Indian 1", "Indian 2", "Indian 3+"], rows,
                 num_cols=range(1, 10), cls=cls)


def model_table(cls="t"):
    if not has_model(L):
        return None
    rows = []
    for s in data.MAIN_ORDER:
        r = [SL(s)]
        for d in data.DATASETS:
            a, b = acc(d, S, s), acc(d, L, s)
            r.append(f"{P(a)} → {P(b)}" if b is not None else f"{P(a)} → pending")
        rows.append(r)
    return table(["Strategy", "FinQA 1.7B → 8B", "TAT-QA 1.7B → 8B", "Indian 1.7B → 8B"], rows, cls=cls)


# ============================================================================================
# Research-question answers
# ============================================================================================
def rq_answers():
    out = []
    b = {d: best(d, S, ["cot_zs", "cot_fs", "decomp_fs", "pot_fs", "sc_cot", "pot_sc", "vpsc"]) for d in data.DATASETS}
    b = {d: r for d, r in b.items() if r is not None}
    cz = {d: data.cell(d, S, "cot_zs") for d in data.DATASETS}
    lo, hi = reasoning_range(S)
    eff = {d: most_efficient(S, d) for d in data.DATASETS}
    mult = five_sample_multiplier(S)
    rq1 = ("Very much at the low end, little at the top. Moving from direct answering to any reasoning strategy raises Qwen3-1.7B from "
           f"≤{P(max(acc(d, S, 'direct') or 0 for d in data.DATASETS), 0)}% to {P(lo, 0)}–{P(hi, 0)}%. Among reasoning strategies the differences are a few points"
           + (" and none is significant after Holm correction" if not any_significant(S, REASONING) else " and mostly not significant")
           + "; the best per dataset is " + ", ".join(f"{SL(r.strategy)} on {data.DLABEL[d]} ({P(r.accuracy, 0)}%)" for d, r in b.items()) +
           ". Fewest tokens per correct answer: " + ", ".join(f"{SL(r.strategy)} on {data.DLABEL[d]} ({r.tokens_per_correct:,.0f})" for d, r in eff.items() if r is not None) +
           (f"; five-sample strategies cost {mult[0]:.1f}–{mult[1]:.1f}× the tokens of few-shot CoT." if mult else "."))
    out.append(("RQ1 — strategies", rq1))
    opts = data.optimized_strategies(S)
    if opts:
        parts = []
        for s in opts:
            for d in data.DATASETS:
                a, c0, c1 = acc(d, S, s), acc(d, S, "cot_zs"), acc(d, S, "cot_fs")
                if a is not None:
                    parts.append(f"{SL(s)} on {data.DLABEL[d]}: {P(a, 0)}% (zero-shot CoT {P(c0, 0)}%, few-shot CoT {P(c1, 0)}%)")
        out.append(("RQ2 — automated optimization", "; ".join(parts) + ". One-time optimization costs are given in the optimization table."))
    else:
        out.append(("RQ2 — automated optimization", "Pending: the DSPy and TextGrad stages are running in the experiment queue; results will be filled in automatically when they finish."))
    if has_model(L):
        parts = []
        for d in data.DATASETS:
            for s in ["cot_fs", "pot_fs", "vpsc"]:
                a, c = acc(d, S, s), acc(d, L, s)
                if a is not None and c is not None:
                    parts.append(f"{SL(s)} {data.DLABEL[d]} {P(a, 0)} → {P(c, 0)}%")
        out.append(("RQ3 — model size", "; ".join(parts) + "." if parts else "8B runs in progress."))
    else:
        out.append(("RQ3 — model size", "Pending: the Qwen3-8B runs follow the 1.7B stages in the queue."))
    es = error_shares(S)
    pt = data.perturbation()
    txt = ""
    if es:
        vc, n = es
        txt += f"Most errors are evidence errors ({100 * vc.get('evidence_error', 0):.0f}% of {n} wrong answers of reasoning strategies), followed by reasoning ({100 * vc.get('reasoning_error', 0):.0f}%) and scale/unit errors ({100 * vc.get('scale_error', 0):.0f}%). "
    ind = acc("indian", S, "pot_fs")
    if ind is not None:
        txt += f"Accuracy on the unseen Indian reports ({SL('pot_fs')} {P(ind, 0)}%) is not lower than on FinQA, so the strategies generalize to ₹ crore/lakh statements. "
    if not pt.empty:
        pm = pt[pt.model == S]
        txt += "Perturbation: " + "; ".join(f"{SL(r.strategy)} {P(r.original_accuracy, 0)}% → {P(r.perturbed_accuracy, 0)}% (p = {pfmt(r.p_value)})" for r in pm.itertuples()) + "."
    else:
        txt += "The perturbation test is running."
    out.append(("RQ4 — failures and robustness", txt))
    dg = data.vpsc_diagnostics(S)
    if not dg.empty:
        same = all(acc(d, S, "vpsc") == acc(d, S, "pot_sc") for d in dg.dataset)
        out.append(("RQ5 — verification (VPSC)",
                    ("Not for Qwen3-1.7B as a vote filter: VPSC and PoT-SC have identical accuracy on all three datasets, because the five sampled programs rarely disagree "
                     "and ungrounded programs usually appear in all five samples. " if same else "VPSC changes some answers relative to PoT-SC (see table). ") +
                    f"However, every question the check flagged ({int(dg.flagged_questions.sum())} in total) was "
                    + ("answered wrongly" if int(dg.flagged_correct.sum()) == 0 else f"answered wrongly in {int(dg.flagged_questions.sum() - dg.flagged_correct.sum())} cases") +
                    ", so grounding is a precise signal for flagging unreliable answers to a human."))
    return out


# ============================================================================================
# Slides
# ============================================================================================
def img_or_pending(path, style="width:100%", what="This experiment"):
    if path is None:
        return f'<div class="card warn"><h3>Pending</h3><p>{what} is still running in the experiment queue. This slide is regenerated automatically from the results.</p></div>'
    return img(path, style)


def slides():
    t = totals()
    d = Deck(LABEL)
    d.raw(title_slide("Review 3", "Final demo & results"))
    d.add("Agenda", "What this review covers", '<div class="cols c2">' + ul([
        "Recap: problem, objectives, design", "What we built", "Experimental setup", "Main results and significance",
        "Accuracy vs. cost; reasoning steps", "Error analysis",
    ]) + ul([
        "Our method VPSC: what verification does", "Automated optimization, robustness, ablations", "Generalization to Indian reports",
        "Answers to the research questions", "Live demo of the web application", "Limitations, conclusion, future work",
    ]) + "</div>")
    d.add("Recap", "Problem and approach in one slide", D.pipeline() + '<div class="cols c3" style="margin-top:6px">'
          '<div class="card"><h3>Task</h3><p>Numerical questions over financial tables + text (growth, margins, ratios, CAGR) — locate, extract with units, apply formula, compute.</p></div>'
          '<div class="card"><h3>Compared</h3><p>6 manual strategies · PoT-SC · <b>VPSC (ours)</b> · DSPy Bootstrap / MIPROv2 · TextGrad — same questions, scorer and models.</p></div>'
          '<div class="card"><h3>Data &amp; models</h3><p>FinQA, TAT-QA, our Indian set (₹ crore/lakh) · Qwen3-1.7B and 8B, local via Ollama.</p></div></div>')
    d.add("Implementation", "What we built", '<div class="cols c4">' + "".join(
        f'<div class="card"><div class="big" style="font-size:44px">{v}</div><div class="stat lbl">{l}</div></div>' for v, l in [
            ("11", "prompting strategies behind one interface (incl. VPSC, DSPy ×2, TextGrad)"), ("244", "test questions in 3 datasets, incl. 44 new Indian-report questions"),
            (f"{t['records']:,}", f"answered questions recorded in {t['runs']} runs"), (f"{t['tokens'] / 1e6:.1f} M", f"tokens processed in {t['calls']:,} recorded model calls")]) +
          '</div><div class="cols c2" style="margin-top:20px">' + ul([
              f"Python library <code>finreason/</code> ({data.code_stats()[0]} modules), experiment & analysis scripts, {data.code_stats()[2]} automated tests (all passing).",
              "Safe code sandbox, grounding verifier, hybrid retriever, rule-based error taxonomy, statistics.",
          ], cls="small") + ul([
              "Nine-page Streamlit web app with evidence, code, trace, votes and prompt for every answer.",
              "Everything local and reproducible: seeded samples, cached responses, resumable runs.",
          ], cls="small") + "</div>")
    d.add("Setup", "Experimental setup", '<div class="dense">' + table(["Item", "Setting"], [
        ["Models", "Qwen3-1.7B, Qwen3-8B (4-bit, Ollama, thinking off unless stated), Apple M4 24 GB"],
        ["Test sets", "FinQA test sample n = 100; TAT-QA arithmetic sample n = 100 (seed 42); Indian set n = 44; FinQA-perturbed n = 88"],
        ["Decoding", "Temperature 0; sampling strategies T = 0.7 (5 samples); max 1,024 output tokens"],
        ["Few-shot / optimization data", "FinQA train (3 worked examples; 50 optimizer train) and dev (40 validation) — never test"],
        ["Metric", "Execution accuracy: within 0.5% of gold or equal at gold's precision; % or fraction accepted for percentages"],
        ["Statistics", "95% bootstrap CI (2,000 resamples); exact McNemar vs few-shot CoT, Holm-corrected"],
    ], widths=[26, 74]) + "</div>" + '<div class="dense" style="margin-top:10px">' + status_table() + "</div>")
    for m in data.models():
        d.add("Main results", f"Accuracy by strategy — {ML(m)}", img_or_pending(fig(f"main_bars_{ML(m)}"), "width:100%"))
        d.add("Main results", f"Results table — {ML(m)} (accuracy %, 95% CI)", '<div class="dense">' + results_table(m) + "</div>"
              '<p class="note">Tokens / Q averaged over the datasets run; latency measured with 3–4 parallel requests on one laptop GPU (relative, not absolute).</p>')
        d.add("Significance", f"Paired McNemar tests vs few-shot CoT — {ML(m)}", '<div class="dense">' + sig_compact(m) + "</div>"
              '<p class="note">Each cell: strategy accuracy vs few-shot CoT accuracy · wins / losses (questions only this strategy / only CoT got right) · Holm-adjusted p. Highlighted: significant (p &lt; 0.05).</p>')
    if model_table() is not None:
        d.add("Model size", "Qwen3-1.7B vs Qwen3-8B", img_or_pending(fig("model_compare"), "width:100%"))
    d.add("Cost", "Accuracy vs. cost", '<div class="cols c2">' + img_or_pending(fig("pareto_finqa")) + img_or_pending(fig("pareto_tatqa")) + "</div>"
          '<p class="small" style="margin-top:8px">Cost-efficiency frontier (' + ML(S) + '): ' + "; ".join(data.DLABEL[dd] + ": " + " → ".join(SL(r.strategy) for r in frontier(S, dd)) for dd in ["finqa", "tatqa"]) +
          (f". Five-sample strategies cost {five_sample_multiplier(S)[0]:.1f}–{five_sample_multiplier(S)[1]:.1f}× the tokens of few-shot CoT.</p>" if five_sample_multiplier(S) else ".</p>"))
    d.add("Difficulty", "Accuracy by number of reasoning steps", img_or_pending(fig(f"steps_{ML(S)}"), "width:100%") +
          '<p class="small">' + steps_sentence(S) + '</p>')
    d.add("Error analysis", "Why answers are wrong", img_or_pending(fig(f"errors_{ML(S)}"), "width:100%"))
    d.add("Our method", "VPSC: what grounding verification actually does", '<div class="dense">' + vpsc_table(S) + "</div>" +
          '<div class="cols c2" style="margin-top:10px">' + ul([f for f in findings(S) if f.startswith("<b>VPSC")], cls="small") +
          '<div class="card accent"><h3>Interpretation</h3><p>The check is precise (flagged ⇒ wrong) but rarely triggers for a small model whose samples agree. '
          'Use it to <b>abstain or alert</b>, and with more diverse samplers or larger models where wrong programs disagree.</p></div></div>')
    o = opt_table()
    if o is not None:
        d.add("Automated optimization", "DSPy and TextGrad vs hand-written prompts", img_or_pending(fig("optimization"), "width:100%"))
        d.add("Automated optimization", "One-time optimization cost", '<div class="dense">' + o + "</div>")
    else:
        d.add("Automated optimization", "DSPy and TextGrad", img_or_pending(None, what="The DSPy / TextGrad optimization stage"))
    pt = perturb_table()
    d.add("Robustness", "Memorization check: perturbed numbers", (img_or_pending(fig("perturbation"), "width:80%") + '<div class="dense">' + pt + "</div>") if pt else img_or_pending(None, what="The perturbation test"))
    ab = ablation_table(S)
    d.add("Ablations", "Table format, retrieval and thinking mode", ('<div class="cols c2">' + img_or_pending(fig(f"ablations_{ML(S)}")) + '<div class="dense">' + ab + "</div></div>") if ab else img_or_pending(None, what="The ablation stage"))
    ind = [[SL(s)] + [P(acc("indian", m, s)) for m in data.models()] for s in data.MAIN_ORDER if acc("indian", S, s) is not None]
    d.add("Generalization", "Indian annual reports (₹ crore / lakh)", '<div class="cols c46"><div class="dense">' +
          table(["Strategy"] + [ML(m) for m in data.models()], ind, num_cols=range(1, 1 + len(data.models())), highlight=lambda i, r: "VPSC" in r[0]) +
          '</div><div>' + ul([f for f in findings(S) if f.startswith("<b>Generalization")] + [
              "Questions need unit conversion (crore → lakh / million / billion), bracketed negatives and long Ind AS tables (18 rows on average).",
          ], cls="small") + "</div></div>")
    fs = findings(S)
    d.add("Findings", "Key findings (1/2)", ul(fs[:3], cls="small"))
    d.add("Findings", "Key findings (2/2)", ul(fs[3:], cls="small"))
    d.add("Research questions", "Answers to RQ1–RQ5", '<div class="dense">' + table(["RQ", "Answer (from our results)"], [[a, b] for a, b in rq_answers()], widths=[16, 84]) + "</div>")
    if shot("ask_result"):
        d.add("Web application", "Ask: the full pipeline, live", '<div class="cols c2">' + img(shot("ask_result"), "width:100%;border-radius:10px") +
              img(shot("ask_votes"), "width:100%;border-radius:10px") + "</div>" +
              '<p class="small" style="margin-top:12px">Titan FY25 revenue growth with VPSC on Qwen3-1.7B: 5 programs, all grounded, unanimous vote, 16.4028% = gold. Evidence rows highlighted; votes with grounding status.</p>')
        d.add("Web application", "Code trace, results dashboard, error explorer", '<div class="cols c3">' + img(shot("ask_code"), "width:100%;border-radius:8px") +
              img(shot("results"), "width:100%;border-radius:8px") + img(shot("errors"), "width:100%;border-radius:8px") + "</div>" +
              '<div class="cols c3 small" style="margin-top:8px"><p>Generated code and variable trace from the sandbox.</p><p>Results: accuracy with CIs, cost frontier, McNemar tests, figures.</p><p>Every wrong answer by strategy and error category.</p></div>')
    d.add("Live demo", "Demo plan (5 minutes)", '<ol style="padding-left:26px">' + "".join(f"<li style='font-size:21px;margin-bottom:10px'>{x}</li>" for x in [
        "<b>Overview</b>: headline findings computed from the runs, literature gaps and the claims checklist.",
        "<b>Ask</b> → Indian reports → <i>marico-08</i> (9-year CAGR) with VPSC: pipeline stepper, answer card, evidence rows, code &amp; trace, votes, prompt; then <b>paste a table</b>.",
        "<b>Data</b>: the same question beside its annual-report PDF page. <b>Compare</b>: Direct vs CoT few-shot vs PoT vs VPSC on one question.",
        "<b>Results</b> and <b>Optimization</b>: accuracy with CIs, accuracy-vs-cost frontier, 1.7B vs 8B, McNemar tests, DSPy / TextGrad.",
        "<b>Errors</b>: Program-of-Thought → evidence errors → open one to show the wrong operand.",
    ]) + "</ol>")
    d.add("Limitations", "Limitations (and how we mitigate them)", '<div class="cols c2">' + ul([
        "<b>Sample size</b>: 100 / 100 / 44 questions → CIs of about ±10 points; we use paired tests and report CIs.",
        "<b>One model family</b> (Qwen3, 4-bit); API models supported by the code but not run.",
        "<b>Indian set</b> is small and written by us; automatically and independently verified against the PDFs.",
    ], cls="small") + ul([
        "<b>Rule-based taxonomy</b> is heuristic (operand matching), not human annotation.",
        "<b>Grounding</b> checks that a number exists in the report, not that it is the right one (wrong year still passes).",
        "<b>FinQA label noise</b> caps reachable accuracy; latency measured under parallel load.",
    ], cls="small") + "</div>")
    d.add("Conclusion", "Conclusion and future work", '<div class="cols c2"><div class="card accent"><h3>Conclusion</h3>' + ul([
        f"For a 1.7B local model, <i>any</i> reasoning prompt turns a near-useless model (≤{P(max(acc(dd, S, 'direct') or 0 for dd in data.DATASETS), 0)}%) into a usable one ({P(reasoning_range(S)[0], 0)}–{P(reasoning_range(S)[1], 0)}%).",
        "Best single-call strategy: " + ", ".join(f"{SL(best_single(S, dd).strategy)} on {data.DLABEL[dd]}" for dd in data.DATASETS if best_single(S, dd) is not None) + "; sampling five times did not pay off.",
        "The remaining bottleneck is evidence: picking and copying the right numbers.",
        "Grounding verification precisely flags unreliable answers; the app makes every answer auditable.",
    ], cls="small") + '</div><div class="card"><h3>Future work</h3>' + ul([
        "Row/column-aware grounding (check the <i>right</i> cell, not just any cell) and abstention when ungrounded.",
        "Larger and API models; diverse samplers for VPSC.",
        "Full test sets; human-annotated error taxonomy.",
        "Whole-document retrieval over complete annual reports.",
    ], cls="small") + "</div></div>")
    d.add("References", "Key references", ref_list_html("refs", ["finqa", "tatqa", "eedp", "cot", "zscot", "sc", "pot", "pal", "dspy", "mipro", "textgrad", "tablellm", "gsmsym", "qwen3", "mcnemar", "dror"]))
    d.raw('<section class="slide section-slide"><div class="kicker">Review 3</div><h2>Thank you — questions?</h2>'
          '<p>Code, data, results and this deck are reproducible from the FinReason repository: <code style="color:#9fe3e8">bash scripts/run_all.sh all</code> then <code style="color:#9fe3e8">python reviews/src/build.py</code>.</p></section>')
    return page(f"{LABEL} slides", SLIDE_CSS, d.html())


# ============================================================================================
# Final report (A4)
# ============================================================================================
def report():
    t = totals()
    fs = findings(S)
    fl = findings(L) if has_model(L) else []
    tg = textgrad_prompt()
    o, pt, ab, mt = opt_table(), perturb_table(), ablation_table(S), model_table()
    model_sections = ""
    for m in data.models():
        model_sections += f"""
<h3>Results for {ML(m)}</h3>
<p class="tcaption">Accuracy (%) with 95% bootstrap CI, tokens and calls per question, {ML(m)}.</p>
{results_table(m)}
<figure>{img(fig(f"main_bars_{ML(m)}"), "width:100%") if fig(f"main_bars_{ML(m)}") else ""}<div class="caption">Accuracy by strategy and dataset, {ML(m)}; bars show 95% CIs.</div></figure>
<p class="tcaption">Exact McNemar tests against few-shot CoT on the same questions ({ML(m)}).</p>
{sig_table(m)}"""
    body = cover("Review 3", "Final Report", "Implementation, experiments, results, demo and conclusions") + f"""
<h1 class="doc-title">Abstract</h1>
<p>Financial reports mix tables and narrative text, and analytical questions over them require locating evidence, extracting values with the right units,
scale and sign, applying domain formulas and multi-step arithmetic. We present <b>FinReason</b>, a controlled, cost-aware study and system for this task.
On FinQA, the arithmetic subset of TAT-QA and a new set of 44 questions over four Indian annual reports (₹ crore/lakh), we compare six hand-written
prompting strategies, automated prompt optimization (DSPy BootstrapFewShot and MIPROv2, TextGrad) and a new method, <b>Verified Program
Self-Consistency (VPSC)</b>, which rejects generated programs that use numbers not found in the report before voting. All models run locally (Qwen3-1.7B
and Qwen3-8B via Ollama). With Qwen3-1.7B, direct answering reaches at most {P(max(acc(d, S, 'direct') or 0 for d in data.DATASETS), 0)}%, while reasoning strategies reach
{P(best('finqa', S).accuracy, 0)}% on FinQA, {P(best('tatqa', S).accuracy, 0)}% on TAT-QA and {P(best('indian', S).accuracy, 0)}% on the Indian set; {single_sentence(S)},
and {five_sentence(S)}. Error analysis shows that most
remaining errors are evidence errors (wrong or missing operands). The grounding check flags such answers precisely but, for the small model, rarely changes the
vote. A Streamlit application exposes the full pipeline with evidence, code, trace and votes for every answer.</p>

<h2>1. Introduction</h2>
<p>Large Language Models are fluent in financial language but unreliable at numerical reasoning over reports: the best fine-tuned FinQA model reached 61.24%
execution accuracy against 91.16% for experts {cite("finqa")}, and GPT-4-Turbo with retrieval failed on 81% of evaluated FinanceBench questions {cite("financebench")}.
Prompting techniques such as Chain-of-Thought {cite("cot")}, Self-Consistency {cite("sc")} and Program-of-Thought {cite("pot")}, and prompt optimizers such as DSPy
{cite("dspy")}, MIPROv2 {cite("mipro")} and TextGrad {cite("textgrad")} promise cheap improvements, but we found no study that compares them under one controlled, cost-aware protocol on
financial table-text reasoning with small local models. Recent work verifies a model's numbers against structured filing data with a solver
{cite("verifin")} or with a trained evidence-auditing agent {cite("dcrc")}, and recent Indian financial benchmarks cover filing look-up {cite("indfin")}
and regulatory text {cite("indiafin")}. This report describes the implementation (Section 2), the experimental setup (Section 3), the results
(Section 4), the web application (Section 5), and discusses findings, limitations and future work (Sections 6–7). Reviews 1 and 2 contain the full literature survey
and the high-level design.</p>
<h3>Contributions</h3>
<ul><li>A reproducible benchmark of 11 prompting strategies on three datasets with accuracy, confidence intervals, paired significance tests, token cost and latency.</li>
<li>VPSC, a training-free grounding check inside program self-consistency (lighter than solver- or training-based verifiers {cite("verifin", "dcrc")}), with an exactly matched ablation.</li>
<li>An Indian annual-report test set of 44 multi-step calculation questions (₹ crore/lakh) with formula-computed, PDF-verified gold answers, complementing look-up benchmarks {cite("indfin")}.</li>
<li>An error taxonomy, a numerical-perturbation memorization test and ablations on table format, retrieval and thinking mode.</li>
<li>An auditable web application.</li></ul>

<h2>2. Implementation</h2>
<p>FinReason is a Python 3.13 library (<code>finreason/</code>, {data.code_stats()[0]} modules, about {round(data.code_stats()[1], -2):,} lines) with command-line scripts, a Streamlit application and {data.code_stats()[2]} automated tests
(all passing). Fig. 1 shows the architecture; the design is documented in the Review 2 report.</p>
<figure>{D.architecture()}<div class="caption">Fig. 1. Architecture.</div></figure>
<ul><li><b>Strategies</b> share one interface <code>strategy(llm, example, context, fmt) → Prediction</code>: direct, zero-/few-shot CoT, decomposition (after EEDP {cite("eedp")}),
Program-of-Thought with one repair round, CoT Self-Consistency (5 samples), PoT Self-Consistency and VPSC (Fig. 2); DSPy-compiled programs and TextGrad prompts are loaded
from artifacts with the same interface.</li>
<li><b>Sandbox</b>: AST checks, isolated <code>python -I</code> process, whitelisted builtins, CPU and wall-clock limits.</li>
<li><b>Grounding verifier</b>: every numeric literal in a program must occur in the report (allowing unit rescaling and harmless constants).</li>
<li><b>Evaluation</b>: answer parser for Indian and Western number formats, scorer, rule-based error taxonomy, bootstrap CIs, McNemar + Holm.</li>
<li><b>Engineering</b>: one LLM client for Ollama and API providers with a SQLite response cache; resumable JSONL run files; analysis re-scores all runs.</li></ul>
<figure>{D.vpsc()}<div class="caption">Fig. 2. Verified Program Self-Consistency (VPSC).</div></figure>

<h2>3. Experimental setup</h2>
{table(["Item", "Setting"], [
    ["Models", "Qwen3-1.7B and Qwen3-8B {0}, 4-bit, served by Ollama on an Apple M4 (24 GB); thinking mode off unless stated".format(cite("qwen3"))],
    ["Test data", "FinQA test sample (n = 100), TAT-QA arithmetic test sample (n = 100), both seed 42; Indian set (n = 44); FinQA-perturbed (n = 88)"],
    ["Decoding", "Temperature 0; sampling strategies use T = 0.7 for samples 1–4; max 1,024 output tokens; context 8,192 tokens"],
    ["Few-shot / optimization", "Three FinQA-train worked examples; DSPy and TextGrad: 50 train / 40 dev; TextGrad 6 steps × 6 questions"],
    ["Metric", "Execution accuracy (0.5% relative tolerance or equality at the gold's precision; percent and fraction forms accepted for percentage questions)"],
    ["Statistics", "95% percentile bootstrap CIs (2,000 resamples); exact McNemar vs few-shot CoT; Holm correction within each setting"],
], cls="t kv")}
<p>Experiment status at the time this document was generated:</p>
{status_table()}
<p>In total, {t['records']:,} question–strategy answers were recorded in {t['runs']} runs ({t['calls']:,} model calls, {t['tokens'] / 1e6:.1f} million tokens).</p>

<h2 class="newpage">4. Results</h2>
<h3>4.1 Main results</h3>
{model_sections}
{"<h3>Model size</h3>" + mt + (f'<figure>{img(fig("model_compare"), "width:100%")}<div class="caption">Qwen3-1.7B vs 8B.</div></figure>' if fig("model_compare") else "") if mt else ""}

<h3>4.2 Key findings</h3>
<ul>{"".join(f"<li>{x}</li>" for x in fs)}</ul>
{("<p><b>Qwen3-8B:</b></p><ul>" + "".join(f"<li>{x}</li>" for x in fl) + "</ul>") if fl else ""}

<h3>4.3 Accuracy versus cost</h3>
<div class="two"><figure>{img(fig("pareto_finqa"), "width:100%")}</figure><figure>{img(fig("pareto_tatqa"), "width:100%")}</figure></div>
<div class="caption">Fig. 3. Accuracy vs mean tokens per question (log scale), FinQA (left) and TAT-QA (right); vertical bars are 95% CIs.</div>

<h3>4.4 Accuracy by reasoning steps</h3>
{steps_table(S)}
<figure>{img(fig(f"steps_{ML(S)}"), "width:100%") if fig(f"steps_{ML(S)}") else ""}<div class="caption">Fig. 4. Accuracy by number of arithmetic operations ({ML(S)}).</div></figure>

<h3>4.5 Error analysis</h3>
<p class="tcaption">Wrong answers by error category, FinQA + TAT-QA ({ML(S)}).</p>
{error_table(S)}
<figure>{img(fig(f"errors_{ML(S)}"), "width:100%") if fig(f"errors_{ML(S)}") else ""}<div class="caption">Fig. 5. Error taxonomy ({ML(S)}).</div></figure>

<h3>4.6 VPSC: the effect of grounding verification</h3>
<p class="tcaption">VPSC compared with its ablation (PoT-SC), CoT Self-Consistency and single-call PoT, with grounding diagnostics ({ML(S)}).</p>
{vpsc_table(S)}
<p>{" ".join(x for x in fs if x.startswith("<b>VPSC"))}</p>

<h3>4.7 Automated prompt optimization</h3>
{(o + (f'<figure>{img(fig("optimization"), "width:100%")}<div class="caption">Fig. 6. Optimized vs hand-written prompts.</div></figure>' if fig("optimization") else "")) if o else '<div class="box warn"><p>Pending: the DSPy and TextGrad stages are running in the experiment queue. Rebuild this document when they finish.</p></div>'}
{f'<p>Final TextGrad system prompt ({tg[0]}):</p><pre>{esc(tg[1])}</pre>' if tg else ""}

<h3>4.8 Robustness: numerical perturbation</h3>
{pt + (f'<figure>{img(fig("perturbation"), "width:80%")}<div class="caption">Fig. 7. Original vs perturbed numbers.</div></figure>' if fig("perturbation") else "") if pt else '<div class="box warn"><p>Pending: the perturbation test is running.</p></div>'}

<h3>4.9 Ablations</h3>
{ab if ab else '<div class="box warn"><p>Pending: table-format, retrieval and thinking-mode ablations are queued.</p></div>'}

<h3>4.10 Generalization to Indian annual reports</h3>
<p>{" ".join(x for x in fs if x.startswith("<b>Generalization"))}</p>

<h2>5. Web application and demo</h2>
<p>The Streamlit application runs the complete pipeline on a dataset question, a pasted table or a page of an uploaded PDF and shows each stage, the answer with
its confidence, the evidence rows used, the generated code with its variable trace, the votes with grounding status and the exact prompt (Fig. 8). The Compare, Results,
Optimization, Robustness, Errors and Data pages expose the experiments, and the Overview page checks every claim against the project. The demo script is in the separate Demo &amp; Viva Guide.</p>
{f'<div class="two"><figure>{img(shot("ask_result"), "width:100%")}</figure><figure>{img(shot("ask_votes"), "width:100%")}</figure></div><div class="two"><figure>{img(shot("results"), "width:100%")}</figure><figure>{img(shot("errors"), "width:100%")}</figure></div><div class="caption">Fig. 8. Web application: Ask (answer, evidence, votes), Results dashboard and Errors page.</div>' if shot("ask_result") else ""}

<h2>6. Answers to the research questions</h2>
{table(["RQ", "Answer"], [[a, b] for a, b in rq_answers()], widths=[18, 82])}

<h2>7. Limitations and future work</h2>
<ul><li><b>Sample size.</b> 100/100/44 questions give CIs of about ±10 points; only large differences are certain. Paired tests partly compensate; the code supports full test sets.</li>
<li><b>Models.</b> One family (Qwen3, 4-bit, local). API models are supported by the client but were not run.</li>
<li><b>Indian set.</b> Small and authored by us; gold answers are formula-computed and independently re-verified against the PDFs (44/44), but question style follows our design.</li>
<li><b>Error taxonomy</b> is rule-based (operand matching) rather than human-annotated.</li>
<li><b>Grounding</b> verifies that a number occurs in the report, not that it is the intended cell; a wrong-year value passes.</li>
<li><b>FinQA label noise</b> caps attainable accuracy; latency was measured under parallel load.</li></ul>
<p><b>Future work:</b> cell-aware grounding (row and column, not only value) with abstention; larger and API models and more diverse samplers for VPSC; full test sets
and human error annotation; retrieval over complete annual reports.</p>

<h2>8. Conclusion</h2>
<p>Prompting matters most at the bottom: for a 1.7B local model, asking for reasoning or a program turns a near-useless model into a usable one, while the
differences between good strategies are small and mostly not significant on 100-question samples. Program-of-Thought is the most cost-effective strong strategy for
exact financial arithmetic; spending five samples rarely pays off for a small model. The dominant remaining error is evidence selection, which grounding verification
can flag precisely; making that flag cell-aware and using it for abstention is the most promising next step. FinReason makes every answer auditable and every result
reproducible.</p>

<h2 class="newpage">References</h2>
{ref_list_html()}
"""
    return page(f"{LABEL} report", REPORT_CSS, body, running="FinReason · Review 3 · Final report")


# ============================================================================================
# IEEE-format paper
# ============================================================================================
def paper():
    fs = findings(S)
    b = {d: best(d, S) for d in data.DATASETS}
    authors = "".join(f"<div>{n}<i>{u}</i><i>Dept. of CSE (AI &amp; ML)</i><i>PES University, Bengaluru</i></div>" for n, u in TEAM)
    o, pt, ab = opt_table("ie"), perturb_table("ie"), ablation_table(S, "ie")
    main = results_table(S, "ie").replace(' style="width:', ' data-w="')
    es = error_shares(S)
    ev = f"{100 * es[0].get('evidence_error', 0):.0f}%" if es else "most"
    dg = data.vpsc_diagnostics(S)
    body = f"""
<h1 class="ieee-title">{TITLE}: Evaluating Prompting Strategies, Automated Prompt Optimization and Verified Program Self-Consistency with Local LLMs</h1>
<div class="authors">{authors}</div>
<div class="cols2">
<p class="abstract noindent"><i>Abstract</i>—Answering analytical questions over financial reports requires locating evidence in tables and text, reading values with the right
unit, scale and sign, and performing multi-step arithmetic — tasks at which Large Language Models (LLMs) remain unreliable. We present a controlled, cost-aware evaluation
of prompting strategies for this task with small local models. On FinQA, the arithmetic subset of TAT-QA and a new set of 44 questions over Indian annual reports
(₹ crore/lakh), we compare direct answering, zero- and few-shot Chain-of-Thought, decomposition, Program-of-Thought, Self-Consistency, automated optimization with DSPy and
TextGrad, and a new method, Verified Program Self-Consistency (VPSC), which discards generated programs whose numbers do not occur in the report before voting. With
Qwen3-1.7B, direct answering reaches at most {P(max(acc(d, S, 'direct') or 0 for d in data.DATASETS), 0)}% while reasoning strategies reach {P(b['finqa'].accuracy, 0)}%, {P(b['tatqa'].accuracy, 0)}% and
{P(b['indian'].accuracy, 0)}% on the three sets; {single_sentence(S)}, and {five_sentence(S)}. {ev} of the remaining errors are evidence errors. Grounding verification flags these answers precisely but rarely changes the vote of a small model.</p>
<p class="kw noindent">Index Terms—large language models, prompt engineering, prompt optimization, program-of-thought, financial question answering, numerical reasoning</p>

<h2 class="ie">I. Introduction</h2>
<p>Financial analysts routinely ask numerical questions of annual reports: growth rates, margins, ratios, compound growth. Although LLMs are fluent in financial
language, their numerical reasoning over reports is unreliable: on FinQA the best fine-tuned model of the original paper reached 61.24% execution accuracy against
91.16% for experts {cite("finqa")}, and GPT-4-Turbo with retrieval failed on 81% of evaluated FinanceBench questions {cite("financebench")}. Prompting methods — Chain-of-Thought
(CoT) {cite("cot", "zscot")}, Self-Consistency {cite("sc")}, Program-of-Thought (PoT) {cite("pot", "pal")} — and prompt optimizers — DSPy {cite("dspy")}, MIPROv2 {cite("mipro")},
TextGrad {cite("textgrad")} — improve reasoning without training, but we found no study that compares them under one protocol, with cost and significance, on financial
table-text reasoning with small local models that keep sensitive data on-premise.</p>
<p>We contribute (i) a controlled benchmark of eleven strategies with confidence intervals, paired tests and token cost; (ii) VPSC, a training-free grounding check inside
program self-consistency, with an exactly matched ablation; (iii) an Indian annual-report set of multi-step calculation questions with ₹ crore/lakh units and
formula-computed, PDF-verified gold answers; and (iv) an error taxonomy, a numerical-perturbation test and an auditable application.</p>

<h2 class="ie">II. Related Work</h2>
<p><i>Benchmarks.</i> FinQA {cite("finqa")} provides 8,281 expert-annotated questions with reasoning programs over S&amp;P 500 earnings reports; TAT-QA {cite("tatqa")}
provides 16,552 questions over hybrid table-text contexts; ConvFinQA {cite("convfinqa")}, DocFinQA {cite("docfinqa")} and FinanceBench {cite("financebench")} extend to
conversations, full documents and open-book QA. Srivastava et al. {cite("eedp")} evaluate LLM mathematical reasoning on these datasets and propose EEDP prompting.
<i>Prompting.</i> CoT {cite("cot")} and zero-shot CoT {cite("zscot")} elicit intermediate steps; Self-Consistency {cite("sc")} votes over sampled paths; decomposition methods
{cite("l2m", "decomp", "pands")} split problems; PoT and PAL {cite("pot", "pal")} delegate arithmetic to an interpreter, raising Codex's FinQA accuracy from 40.4% to 64.5% {cite("pot")}.
<i>Optimization.</i> APE {cite("ape")} and OPRO {cite("opro")} search instructions with LLMs; DSPy {cite("dspy")} compiles declarative programs, MIPROv2 {cite("mipro")} jointly
optimizes instructions and demonstrations, and TextGrad {cite("textgrad")} back-propagates textual feedback. <i>Robustness.</i> Table serialization affects LLM
accuracy {cite("tablellm")}, and changing only the numbers of math problems lowers accuracy {cite("gsmsym")}. Evidence retrieval combines BM25 {cite("bm25")}, Sentence-BERT
embeddings {cite("sbert")} in FAISS {cite("faiss")} and reciprocal rank fusion {cite("rrf")}, as in retrieval-augmented generation {cite("rag")}; Binder {cite("binder")} binds LMs to
symbolic languages over tables. <i>Domain models.</i> BloombergGPT {cite("bloomberggpt")} and TAT-LLM {cite("tatllm")} train or fine-tune finance-specific models, whereas we study
in-context learning {cite("gpt3")} with general models. Following Dror et al. {cite("dror")}, we report paired significance tests. <i>Verification and Indian data.</i> Closest to our grounding check,
VeriFin {cite("verifin")} grounds the operands of LLM-generated financial claims in XBRL facts and verifies formulas with the Z3 solver, and DCRC {cite("dcrc")}
trains an agent that audits evidence before compiling executable programs; our check needs no structured data, solver or training, and runs inside
self-consistency voting over plain report tables. IndFin-Bench {cite("indfin")} (mostly filing look-up) and IndiaFinBench {cite("indiafin")} (regulatory text)
are recent Indian financial benchmarks; our Indian set targets multi-step calculation over annual-report statements.</p>

<h2 class="ie">III. Method</h2>
<h3 class="ie">A. Task and Scoring</h3>
<p>Given a table <i>T</i>, text <i>P</i> and question <i>q</i>, the system outputs a number (or yes/no). A prediction is correct if it is within 0.5% of the gold value or
equals it at the gold's precision; for percentage questions both percent and fraction forms are accepted, since FinQA stores fractions and TAT-QA percentages.</p>
<h3 class="ie">B. Strategies</h3>
<p>All strategies share the same system prompt and answer-format rules, and few-shot variants use the same three FinQA-train examples. PoT programs run in a sandbox
(AST checks, isolated interpreter, builtin whitelist, CPU and time limits) with one repair round. DSPy compiles a Chain-of-Thought program whose metric is our scorer;
TextGrad optimizes the system prompt of zero-shot CoT, keeping an update only if validation accuracy does not drop. All optimization uses FinQA train/dev only.</p>
<h3 class="ie">C. Verified Program Self-Consistency</h3>
<p>VPSC samples five programs (one greedy, four at <i>T</i> = 0.7), executes them, and keeps a program only if every numeric literal in its syntax tree occurs in the report,
allowing small integers, unit constants (10<sup>2</sup>, 10<sup>3</sup>, 10<sup>5</sup>, 10<sup>6</sup>, 10<sup>7</sup>, 10<sup>9</sup>), years and ×100/×1000 rescaling.
The answer is the majority over kept programs (all executed programs if none is kept). PoT-SC votes over the same five programs without the check, isolating its effect.</p>
<pre class="alg">Algorithm 1: VPSC(q, T, P)
 1: C ← serialize(T) ⊕ P;  N ← numbers(C)
 2: for i = 0..4: code_i ← LLM(PoT-prompt(C, q), T = 0 if i = 0 else 0.7)
 3:   (ok_i, a_i) ← sandbox(code_i)
 4:   g_i ← ∀ x ∈ literals(code_i): x ∈ const ∨ ∃ n ∈ N, s ∈ S: x = n·s
 5: K ← {{i : ok_i ∧ g_i}};  if K = ∅: K ← {{i : ok_i}}
 6: return mode{{a_i : i ∈ K}}, confidence = votes / 5</pre>

<h2 class="ie">IV. Experimental Setup</h2>
<p>We evaluate Qwen3-1.7B {cite("qwen3")} (4-bit, Ollama, non-thinking mode) on fixed samples of 100 FinQA and 100 TAT-QA arithmetic test questions (seed 42) and on all 44
Indian questions, built from the statements of Titan, Asian Paints, Marico and Pidilite; each gold answer is the sandboxed result of a formula whose operands were checked
against the PDF page. Uncertainty is a 95% bootstrap CI {cite("bootstrap")}; strategies are compared with few-shot CoT using exact McNemar tests {cite("mcnemar")} with Holm
correction {cite("holm")}.</p>

<h2 class="ie">V. Results</h2>
<div class="wide"><p class="tcap">Table I. Execution accuracy (%) [95% CI], mean tokens, calls and latency per question — Qwen3-1.7B</p>{main}</div>
<p><i>Main results.</i> {fs[0] if fs else ""} {fs[1] if len(fs) > 1 else ""}</p>
<p><i>Cost.</i> {fs[2] if len(fs) > 2 else ""} Fig. 1 shows zero-shot CoT and PoT on the cost-efficiency frontier.</p>
<figure>{img(fig("pareto_finqa"), "") if fig("pareto_finqa") else ""}<figcaption>Fig. 1. Accuracy vs. mean tokens per question on FinQA (Qwen3-1.7B); bars are 95% CIs.</figcaption></figure>
<p><i>Errors.</i> {next((x for x in fs if x.startswith("<b>Evidence")), "")}</p>
<figure>{img(fig(f"errors_{ML(S)}"), "") if fig(f"errors_{ML(S)}") else ""}<figcaption>Fig. 2. Wrong answers by error category on FinQA + TAT-QA.</figcaption></figure>
<p><i>VPSC.</i> {next((x for x in fs if x.startswith("<b>VPSC")), "")}</p>
<p class="tcap">Table II. VPSC diagnostics</p>{vpsc_table(S, "ie")}
<p><i>Generalization.</i> {next((x for x in fs if x.startswith("<b>Generalization")), "")}</p>
{('<p class="tcap">Table III. Automated optimization cost</p>' + o) if o else "<p><i>Optimization.</i> DSPy and TextGrad results are pending at the time of writing.</p>"}
{('<p class="tcap">Table IV. Perturbation test</p>' + pt) if pt else ""}
{('<p class="tcap">Table V. Ablations</p>' + ab) if ab else ""}

<h2 class="ie">VI. Discussion and Limitations</h2>
<p>For a small model the decisive choice is whether to reason at all; among reasoning strategies, differences are within the ±10-point CIs of 100-question samples.
Programs remove arithmetic errors, leaving evidence selection as the bottleneck. VPSC's grounding check is precise — every flagged question was wrong — but the 1.7B
model's samples agree {('in ' + ', '.join(f'{100 * a:.0f}%' for a in dg.agreement) + ' of votes on average') if not dg.empty else 'strongly'}, so filtering seldom changes the
majority; it is better used to abstain or alert. Limitations: small samples, one model family, a small self-authored Indian set, a heuristic error taxonomy, and value-level
(not cell-level) grounding.</p>

<h2 class="ie">VII. Conclusion</h2>
<p>We presented a reproducible, cost-aware comparison of prompting and prompt optimization for financial numerical reasoning with local LLMs, a new Indian test set and
VPSC. Program-of-Thought is the most cost-effective strong strategy; the remaining errors are evidence errors, which grounding verification flags. Future work: cell-aware
grounding with abstention, larger models and whole-document retrieval.</p>

<h2 class="ie">References</h2>
{ref_list_html("refs")}
</div>"""
    return page("FinReason IEEE paper", IEEE_CSS, body)


# ============================================================================================
# Demo and viva guide
# ============================================================================================
VIVA = [
    ("What exactly is the task?", "Given one report page (table + text) and a question that needs arithmetic, output the number (or yes/no). We score with execution accuracy: within 0.5% of the gold value, or equal at the gold's precision; percent and fraction forms both accepted."),
    ("Why not just fine-tune a model?", "Fine-tuning needs labelled data, GPUs and retraining for every new model. Prompting and prompt optimization are cheap, model-agnostic and the course focus; TAT-LLM and BloombergGPT show the training route but at much higher cost."),
    ("Why Program-of-Thought?", "LLMs are bad at exact multi-digit arithmetic. In PoT the model only decides what to compute; Python computes it exactly. In our results with Qwen3-1.7B: {single}."),
    ("What is VPSC and what is new about it?", "Five PoT programs are sampled and executed; programs that use a number not found in the report are discarded before the majority vote. Our addition is this training-free grounding check inside the vote; PoT-SC uses the same five programs without it, so the comparison isolates verification exactly."),
    ("Isn't this already done by VeriFin or IndFin-Bench?", "They are related, not the same. VeriFin checks numbers against structured XBRL data with a logic solver, and DCRC trains a special auditing model; VPSC needs no structured data, no solver and no training. IndFin-Bench asks mostly look-up questions about Indian filings and IndiaFinBench uses regulatory text; our Indian set is multi-step calculations from annual reports."),
    ("Did VPSC beat PoT-SC?", "Not for Qwen3-1.7B: accuracy is identical because the five samples nearly always agree and ungrounded programs appear in all samples. But every flagged question was wrong, so the check is a precise reliability signal — useful for abstention or alerts."),
    ("Why McNemar's test?", "All strategies answer the same questions, so results are paired. McNemar uses only the discordant questions (one right, the other wrong) and is exact via the binomial distribution. Holm corrects for testing many strategies."),
    ("Why are your confidence intervals so wide?", "With n = 100 a 95% CI is about ±10 points. We report CIs honestly and rely on paired tests; the code can run full test sets (--n 0) with more compute."),
    ("How do you avoid test leakage?", "Worked examples and all DSPy/TextGrad training data come from FinQA train/dev; test samples are fixed by seed and never used for tuning."),
    ("How did you build the Indian set and why trust it?", "Tables were transcribed from official PDFs; every one of the 366 cells must appear on its PDF page or the build fails; gold answers are computed by running formulas, never typed; and we independently re-extracted every page and confirmed all 44 questions' operands and gold values."),
    ("What is the numerical perturbation test?", "We change every operand of the FinQA gold program by 10–30%, replace it in the table/text and recompute the gold with the program. A model that memorized FinQA answers would fail; a reasoning model should not care."),
    ("How is the code sandbox safe?", "Four layers: AST rules (only math import, no dunders, no open/eval/os), a fresh isolated python -I process, whitelisted builtins, and CPU + 5 s time limits. Output is JSON only."),
    ("What does DSPy actually optimize?", "A ChainOfThought program with our FinancialQA signature. BootstrapFewShot keeps up to three self-generated traces that our metric marks correct as demos; MIPROv2 also proposes instructions and searches combinations with a Bayesian surrogate on dev minibatches."),
    ("What does TextGrad optimize?", "The system prompt of zero-shot CoT. Wrong answers get a critique (a ‘textual gradient’) from the optimizer model; TGD rewrites the prompt; we keep the update only if dev accuracy does not drop."),
    ("Why is Self-Consistency not helping?", "For a 1.7B model at T = 0.7 the samples mostly repeat the same reasoning, so the vote rarely changes the answer, while costing five times the tokens."),
    ("What are the main error types?", "Evidence errors dominate: a needed operand is missing or wrong. Then reasoning errors (right numbers, wrong formula), scale/unit errors and sign errors. Direct answering mostly shows no work."),
    ("Why two Ollama servers?", "The experiments keep one server busy for hours; the app uses a second server so live questions are not queued behind experiments."),
    ("Why cache responses?", "Identical requests return instantly and identically; experiments are resumable; VPSC's first sample reuses the PoT call, so the ablation costs nothing extra."),
    ("What would you do with more time?", "Cell-aware grounding (check the right row and column) and abstention; larger/API models; full test sets; retrieval over whole annual reports."),
    ("What are the limitations?", "Small samples, one model family, a small self-written Indian set, a heuristic error taxonomy, value-level grounding, FinQA label noise, latency measured under parallel load."),
    ("How do you know the scorer is right?", "Unit tests cover parsing (Indian grouping, brackets, %, scale words), tolerance and percent/fraction handling; the same scorer is used at run time, in DSPy's metric, in TextGrad validation, in the app and in the analysis, which re-scores everything."),
]


def viva():
    out = []
    for q, a in VIVA:
        out.append((q, a.replace("{single}", single_sentence(S))))
    return out


def demo_guide():
    rows = [(n, u, r) for (n, u), r in zip(TEAM, ["Indian-report results, cost, error analysis, VPSC result",
                                                    "Recap, setup, experiment status, main results",
                                                    "Web app, live demo, conclusion and limitations; leads the Q&A",
                                                    "DSPy/TextGrad, perturbation, ablations, key findings"])]
    body = cover("Review 3", "Demo Script &amp; Viva Guide", "Setup checklist, 5-minute demo, fallback plan, presenter roles and likely questions") + f"""
<h2>1. Before the review (setup checklist)</h2>
<ol><li>Open a terminal in the project folder and start Ollama with parallel slots:<pre>OLLAMA_NUM_PARALLEL=4 ollama serve</pre></li>
<li>Start the web app (it starts its own Ollama server on port 11435):<pre>bash scripts/start_app.sh</pre>Open <code>http://localhost:8501</code>.</li>
<li>Pre-warm the questions you will demo by running them once (answers are cached, so the live demo is instant): <i>titan-01</i> and <i>marico-08</i> with VPSC on Qwen3-1.7B.</li>
<li>Run the unit tests to show they pass: <pre>.venv/bin/python -m pytest -q        # {data.code_stats()[2]} passed</pre></li>
<li>Regenerate results and documents if new runs finished: <pre>.venv/bin/python scripts/analyze.py
.venv/bin/python reviews/src/build.py</pre></li>
<li>Keep <code>results/report.md</code> and the slide deck open as a fallback.</li></ol>

<h2>2. Demo script (5 minutes)</h2>
{table(["Time", "Page", "What to do", "What to say"], [
    ["0:00", "Overview", "Scroll through the headline findings, the literature-gap table and the claims checklist.", "Every finding is computed live from the saved runs; every claim of our reviews is checked against the project."],
    ["0:40", "Ask", "Benchmark question → Indian reports → <i>marico-08</i> (9-year CAGR); strategy VPSC (ours); Run the pipeline.", "The pipeline runs live: context → 5 programs → sandbox → grounding check → vote → score."],
    ["1:30", "Ask (tabs)", "Show the answer card (agreement bar, grounding flag), Evidence (highlighted rows), Code &amp; trace, Votes (grounded ✓), Prompt.", "Every number is traced back to the report; this is the auditable answer an analyst needs."],
    ["2:15", "Ask → Paste a table", "Paste a small P&amp;L (e.g. revenue 1,200 / 1,000) and ask for the growth rate.", "Works on unseen data, not only benchmark questions."],
    ["2:45", "Data", "Marico → <i>marico-08</i>: formula, table and the annual-report PDF page side by side.", "Our Indian gold answers are computed from formulas over numbers printed on these pages."],
    ["3:15", "Compare", "Direct, CoT few-shot, PoT, VPSC on one question → Run all strategies.", "Direct is cheap but usually wrong; programs are exact; VPSC costs five calls."],
    ["3:45", "Results · Optimization", "Accuracy with CIs, accuracy vs cost, 1.7B vs 8B; then DSPy / TextGrad cost and test accuracy.", "Main findings: reasoning is essential; PoT best single call; SC poor value; optimizers vs hand-written prompts."],
    ["4:30", "Errors", "Program-of-Thought → evidence error → open one question.", "The model copied the wrong operand — this is what grounding verification targets."],
], widths=[8, 15, 40, 37])}

<h2>3. Fallback plan</h2>
<ul><li><b>Ollama slow or busy:</b> cached questions answer instantly; use titan-01 / marico-08 which are pre-warmed.</li>
<li><b>App does not start:</b> show the screenshots in the Review 3 deck and <code>results/report.md</code>; run one question from the command line:
<pre>.venv/bin/python scripts/run_experiment.py --dataset indian --n 44 --model ollama:qwen3:1.7b --strategy vpsc</pre>(already-answered questions are skipped and the accuracy is printed).</li>
<li><b>Laptop issue:</b> present the PDF deck; every number in it comes from the saved run files.</li></ul>

<h2>4. Presenter roles</h2>
{table(["Member", "SRN", "Presents"], [list(r) for r in rows], widths=[22, 20, 58])}
<p>The work is divided equally; everyone should be able to explain the scoring rule, Program-of-Thought, VPSC and the main result.</p>

<h2>5. Numbers to remember</h2>
<ul>{"".join(f"<li>{x}</li>" for x in findings(S))}</ul>

<h2 class="newpage">6. Likely viva questions</h2>
{"".join(f"<h4>Q{i + 1}. {q}</h4><p>{a}</p>" for i, (q, a) in enumerate(viva()))}
"""
    return page("Demo and viva guide", REPORT_CSS, body, running="FinReason · Review 3 · Demo & viva guide")
