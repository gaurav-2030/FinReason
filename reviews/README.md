# FinReason review documents

Short versions to learn and present (default):

| Review | Files |
|---|---|
| Review 1: idea + literature survey | `Review1/…_Slides.pdf`, `…_Speaker_Script.pdf`, `…_Notes.pdf` |
| Review 2: high-level design + data collection | `Review2/…_Slides.pdf`, `…_Speaker_Script.pdf`, `…_Notes.pdf` |
| Review 3: final demo | `Review3/…_Slides.pdf`, `…_Speaker_Script.pdf`, `…_Notes.pdf`, `…_IEEE_Paper.pdf` |
| Work division | `FinReason_Work_Division.pdf` — equal split: 3 slides each in Reviews 1–2, 4 each in Review 3 |
| Everything | `FinReason_All_Reviews.pdf` |

The speaker scripts give, for every slide, what its presenter says (about one minute, in simple words) and the hand-over line to the next presenter.

Each slide has one "Key point" line. The notes say what to say, list the numbers to remember, and answer likely questions.
The long versions (full reports, 137 pages) are in `detailed/`; rebuild them with `build.py --detailed`.

Every result number, table and chart is computed from `results/runs/*.jsonl` by the project's own
analysis code (`scripts/analyze.py`). Experiments that had not finished when the PDFs were built are marked
**pending** and are never estimated.

## Rebuild after more experiments finish

```bash
.venv/bin/python scripts/analyze.py          # refresh results/*.csv and figures
.venv/bin/python reviews/src/screenshots.py  # optional: new app screenshots (app must be running)
.venv/bin/python reviews/src/build.py        # rebuild all PDFs (or: build.py 3 for Review 3 only)
```

To print a project guide's name on the title pages, set `GUIDE` in `reviews/src/common.py`.

## Data checks done for these documents

* `results/indian_verification.csv`: all 44 Indian-set questions were re-checked against the cited PDF pages. Every operand
  was found on the page in the intended row and year column, and every gold answer recomputes exactly from its formula. The team should still
  complete the human sign-off in `data/indian/verification_checklist.csv`.
* All literature numbers were checked against the papers: FinQA 61.24 vs 91.16; TAT-QA 50.1/58.0 vs 84.1/90.8;
  PoT FinQA 40.4→64.5 and 44.4→68.1; FinanceBench 81%; MIPROv2 up to 13%; TextGrad GPQA 51→55%.
