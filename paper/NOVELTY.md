# FinReason novelty: from VPSC to TRACE-PG

## Where we started
VPSC (5 same-prompt programs + value grounding + vote) changed **0 answers** (VPSC = PoT-SC).

## Core idea now
**Programs as typed provenance graphs.** Every generated program is executed symbolically into a
formula whose leaves are typed references to report evidence (cell, row label, period, unit,
percent flag). That representation lets us verify *what a program computes* against *what the
question asks*, compare programs by computation rather than printed value, complete formulas
symbolically, and attach a calibrated, conformally-guaranteed confidence and cell citations.

## Contributions (each implemented, logged and measured)
| # | Advancement | Where | Development evidence |
|---|---|---|---|
| 1 | Coverage law: beta-binomial model of sampling coverage, one parameter rho | `scripts/pgv_eval.py` | rho = 0.97/0.98 for program samples; fits measured coverage within 0.3 pt; CoT-SC needs ~53 samples to match 6 heterogeneous calls |
| 2 | Symbolic lifting to provenance graphs | `finreason/pgv.py` | 99-100% of programs lifted |
| 3 | Intent typing of formula shapes | `pgv.py` | flagged programs 67-82% wrong (base 27-51%) |
| 4 | Period + temporal-orientation checking (sign errors) | `pgv.py` | orientation flags 100% wrong |
| 5 | Dimensional/scale analysis | `pgv.py` | unit flags 100% wrong |
| 6 | Structural consensus (canonical formula signatures) | `pgv.py` | verifier feature |
| 7 | Neuro-symbolic template completion (model picks evidence, question type picks formula) | `pgv.py` | fires on 12-66% of questions, 58-88% correct |
| 8 | Heterogeneous views + audit-guided repair (TRACE) | `finreason/trace.py`, `provenance.py` | error correlation 0.91-0.97 -> 0.38-0.55; repair 7 fixes / 0 breaks |
| 9 | Calibrated verifier (grouped CV, development only) | `pgv_eval.py` | CV 71.0% vs 70.7% fixed weights (honest: small) |
| 10 | Conformal risk control abstention | `pgv_eval.py` | distribution-free bound on wrong-answer rate |
| 11 | Staged escalation with stage-wise calibration | `pgv_eval.py` | 72.3% at 3.2 calls vs 70.7% at 6.2 (development, tuned there) |
| 12 | Cell-level attribution metric | `pgv_eval.py` | exact gold-row citation 81% vs 76% for PoT (FinQA-D) |
| 13 | Strict protocol: frozen artifacts, disjoint held-out samples, exact replay | `artifacts/trace_pg.json`, `logs/run_trace.sh` | |

## Honest reading
* Accuracy gains come mostly from the candidate set (views, repair), exactly as the coverage law
  predicts; typed verification adds precision, citations, confidence and cost savings.
* No paper is guaranteed acceptance. Biggest remaining risks: small samples (CIs +-6-10 points),
  small models only, rule-based intent parser, references marked `% VERIFY` still to check.
