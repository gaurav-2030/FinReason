"""Build the review documents.
    .venv/bin/python reviews/src/build.py              # concise versions (default): slides + study notes, IEEE paper
    .venv/bin/python reviews/src/build.py --detailed   # the long versions, written to reviews/detailed/
Concise PDFs go to reviews/ReviewN/ plus one combined reviews/FinReason_All_Reviews.pdf."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pypdf import PdfWriter  # noqa: E402

import figs  # noqa: E402
from common import REVIEWS, render_pdf  # noqa: E402


def concise_parts():
    import concise as C
    import review3
    import speaker as SP
    return {0: [("Work_Division", C.work_division)],
            1: [("Slides", C.r1_slides), ("Speaker_Script", SP.r1_script), ("Notes", C.r1_notes)],
            2: [("Slides", C.r2_slides), ("Speaker_Script", SP.r2_script), ("Notes", C.r2_notes)],
            3: [("Slides", C.r3_slides), ("Speaker_Script", SP.r3_script), ("Notes", C.r3_notes), ("IEEE_Paper", review3.paper)]}


def detailed_parts():
    import review1, review2, review3
    return {1: [("Slides", review1.slides), ("Report", review1.report)],
            2: [("Slides", review2.slides), ("Report", review2.report)],
            3: [("Slides", review3.slides), ("Report", review3.report), ("IEEE_Paper", review3.paper), ("Demo_and_Viva_Guide", review3.demo_guide)]}


NAMES = {0: "FinReason", 1: "Review1_Idea_and_Literature_Survey", 2: "Review2_HLD_and_Data_Collection", 3: "Review3_Final_Demo"}


def combine(paths, out):
    w = PdfWriter()
    for p in paths:
        w.append(str(p), outline_item=p.stem.replace("_", " "))
    w.write(str(out))
    print("wrote", out.relative_to(REVIEWS.parent))


if __name__ == "__main__":
    detailed = "--detailed" in sys.argv
    which = [int(a) for a in sys.argv[1:] if a.isdigit()] or ([1, 2, 3] if detailed else [0, 1, 2, 3])
    figs.all_figures()
    parts = detailed_parts() if detailed else concise_parts()
    root = REVIEWS / "detailed" if detailed else REVIEWS
    made = []
    for n in which:
        for part, fn in parts[n]:
            pdf = (root / f"Review{n}" if n else root) / f"{NAMES[n]}_{part}.pdf"
            render_pdf(fn(), pdf, f"{'d' if detailed else 'c'}{n}_{part.lower()}")
            made.append(pdf)
            print("wrote", pdf.relative_to(REVIEWS.parent))
    if which in ([1, 2, 3], [0, 1, 2, 3]):
        combine(made, root / ("FinReason_All_Reviews_Detailed.pdf" if detailed else "FinReason_All_Reviews.pdf"))
