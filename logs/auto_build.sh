# Rebuilds the review PDFs once every experiment (main queue + small-model optimization) has finished.
cd ~/Desktop/FinReason
until grep -q '=== AFTER-QUEUE DONE' logs/optimize_rerun.log; do sleep 120; done
.venv/bin/python scripts/analyze.py > /dev/null 2>&1
.venv/bin/python reviews/src/screenshots.py || echo "screenshots skipped (app not running)"
.venv/bin/python reviews/src/build.py && echo "=== REVIEWS REBUILT $(date)" || echo "!!! BUILD FAILED $(date)"
