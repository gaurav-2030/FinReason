# What is FinReason's novelty?

## Before: VPSC (one contribution, no measurable effect)

VPSC = sample 5 Python programs from **one** prompt, drop programs whose numbers are not in the
report, majority-vote the rest. Our own results showed:

* VPSC changed **0 final answers** on all three datasets (VPSC = PoT-SC exactly: 56 / 67 / 77.3%).
* The grounding filter flagged only 6 questions out of 244.
* Reviewers would see this as "self-consistency + a string check": thin novelty, null result.

## Why VPSC could not work (new finding, now the paper's core insight)

Accuracy = **coverage** (is the right answer among the candidates?) − **selection gap**.
A filter or vote can only shrink the selection gap. For Qwen3-1.7B on FinQA, the 5 same-prompt
programs contain the right answer for 57% of questions while the vote already gets 56%: a 1-point
ceiling. On 29–31% of questions all five programs give the *same wrong* answer. And most wrong
programs pass value-level grounding because they copy a real number from the wrong row or year.

## After: TRACE (Table-grounded Repair, Audit, Consensus and Escalation)

| # | Contribution | What is new |
|---|---|---|
| 1 | Coverage/selection decomposition + measurement | Explains *why* grounding filters and voting fail for small models (correlated errors); not reported in the PoT/self-consistency literature for financial QA |
| 2 | Cell-level provenance audit | Uses the program's own variable names (`revenue_2019`) as an independent description of each operand and checks it against the exact table cell (row by words, column by year), plus question-span, answer-type, unit-aware grounding. Handles messy real tables (repeated/spanning headers). No XBRL, solver or training (cf. VeriFin, DCRC) |
| 3 | Audit-guided repair | External, cell-specific feedback ("row X, column 2008 holds 117") — unlike intrinsic self-correction, which is known to fail |
| 4 | Heterogeneous consensus | Program + CoT + decomposition views with audit weights and 1% tolerance pooling; raises coverage from 57% to 75% (FinQA) and 67% to 90% (TAT-QA) on development data |
| 5 | Escalation (adaptive compute) | Answer after 2 calls when an audited program agrees with CoT; 27–44% fewer tokens at equal accuracy (development data) |
| 6 | Selective prediction | Audit-weighted confidence halves AURC vs PoT-SC (0.20 vs 0.39 FinQA, 0.10 vs 0.26 TAT-QA, development) — the system knows when not to answer |
| 7 | Rigorous protocol | Disjoint held-out samples never inspected; exact replay of every ablation from logged calls; McNemar + Holm; second model family; larger model; perturbation; Indian reports |

Development-sample accuracy (Qwen3-1.7B): FinQA 61% (PoT 57, VPSC 56, VPSC-v2 56, CoT 52),
TAT-QA 81% (VPSC-v2 79, CoT-SC 74, PoT 67, VPSC 67). Held-out numbers: see `paper/generated/`.

"10× more novel" is not something that can be measured. Honestly: the project went from one
mechanism with a null effect to a diagnosis plus five method components, each with its own
measured effect and ablation.

## Honest caveats a reviewer will raise

* The accuracy gain comes mostly from view diversity (contribution 4). The audit's accuracy gain is
  small (0–2 points); its main value is precision (88–97% of flagged programs are wrong) and
  confidence (contribution 6). The paper says this plainly.
* Samples of 100–200 questions: CIs are ±6–10 points; not every pairwise difference is significant.
* Small models only. The self-citation `vpsc` must be anonymized for double-blind venues.
* References marked `% VERIFY` in `refs.bib` were added from memory and must be checked.
